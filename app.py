from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
# from flask_wtf.csrf import CSRFProtect  # TODO: Install Flask-WTF and uncomment
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import requests
import sqlite3
import re
import logging
from datetime import timedelta
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pwa_helpers import cache_recipe_for_offline, save_search_for_offline



# Load environment variables
load_dotenv()


# Validate required environment variables
REQUIRED_ENV_VARS = ['SECRET_KEY', 'SPOONACULAR_API_KEY', 'MAIL_SERVER', 'MAIL_USERNAME', 'MAIL_PASSWORD']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")



# Session configuration for security
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=not app.debug,  # Use secure cookies in production
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

# Flask-Mail setup
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() == "true",
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME")
)

# Initialize extensions
mail = Mail(app)
# csrf = CSRFProtect(app)  # TODO: Install Flask-WTF and uncomment

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Logging setup
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Recipe app startup')

# Store pending registrations (in production, use Redis or database)
pending_registrations = {}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_databases():
    """Initialize all required database tables"""
    with get_db_connection() as conn:
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Favorites table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS saved_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                recipe_id INTEGER NOT NULL,
                recipe_title TEXT NOT NULL,
                recipe_image TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, recipe_id)
            )
        ''')
    
    app.logger.info("Databases initialized successfully")

# Database helper functions
def username_exists(username):
    """Check if username exists in database"""
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            return user is not None
    except Exception as e:
        app.logger.error(f"Error checking username: {e}")
        return False

def email_exists_in_db(email):
    """Check if email exists in database"""
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            return user is not None
    except Exception as e:
        app.logger.error(f"Error checking email: {e}")
        return False

def register_user(username, password, email):
    """Register a new user with hashed password"""
    try:
        with get_db_connection() as conn:
            hashed_password = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                (username, hashed_password, email)
            )
        
        app.logger.info(f"User {username} registered successfully")
        return True
    except Exception as e:
        app.logger.error(f"Registration error: {e}")
        return False

def verify_user(username, password):
    """Verify user credentials"""
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT password FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                return True
            return False
    except Exception as e:
        app.logger.error(f"Verification error: {e}")
        return False

def get_user_email(username):
    """Get user email by username"""
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT email FROM users WHERE username = ?', (username,)).fetchone()
            return user['email'] if user else None
    except Exception as e:
        app.logger.error(f"Error getting user email: {e}")
        return None

def get_user_favorites(username):
    """Get list of user's favorite recipe IDs"""
    try:
        with get_db_connection() as conn:
            favorites = conn.execute(
                'SELECT recipe_id FROM saved_recipes WHERE username = ?', (username,)
            ).fetchall()
            return [fav['recipe_id'] for fav in favorites]
    except Exception as e:
        app.logger.error(f"Error getting user favorites: {e}")
        return []

# Validation functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username (letters, numbers, underscore only)"""
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None and 3 <= len(username) <= 20

def validate_password(password):
    """Validate password strength"""
    return len(password) >= 6

# API helper functions
def fetch_recipes_by_ingredients_with_offset(ingredients_str, dietary_prefs, api_key, offset=0):
    """Fetch recipes from Spoonacular API with offset for pagination"""
    import random
    
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    
    # Simplified parameters - remove complex randomization that might cause issues
    params = {
        "ingredients": ingredients_str,
        "number": 8,
        "offset": offset,
        "apiKey": api_key,
        "addRecipeInformation": True,
        "fillIngredients": True
    }
    
    # Only add diet parameter if there are actual dietary preferences
    if dietary_prefs and len(dietary_prefs) > 0:
        # Format dietary preferences properly
        diet_string = ",".join(dietary_prefs)
        params["diet"] = diet_string
    
    print(f"🔍 API URL: {url}")
    print(f"📊 API Params: {params}")
    
    response = requests.get(url, params=params, timeout=15)  # Increased timeout
    
    print(f"📡 API Response Status: {response.status_code}")
    print(f"📄 API Response Length: {len(response.text)}")
    
    return response

# Legacy function for caching compatibility
@cache.memoize(timeout=1800)  # Cache for 30 minutes (shorter to allow variety)
def fetch_recipes_by_ingredients(ingredients_str, dietary_prefs, api_key):
    """Fetch recipes from Spoonacular API with caching"""
    return fetch_recipes_by_ingredients_with_offset(ingredients_str, dietary_prefs, api_key, 0)

@cache.memoize(timeout=3600)
def fetch_recipe_details(recipe_id, api_key):
    """Fetch detailed recipe information with caching"""
    response = requests.get(
        f"https://api.spoonacular.com/recipes/{recipe_id}/information",
        params={"apiKey": api_key, "includeNutrition": True},
        timeout=10
    )
    return response

def send_verification_email(email, confirm_link):
    """Send verification email with improved error handling"""
    try:
        msg = Message(
            subject="Confirm Your Email - SmartRecipes",
            recipients=[email],
            html=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4CAF50;">Welcome to SmartRecipes!</h2>
                    <p>Please verify your email address by clicking the button below:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{confirm_link}" 
                           style="background-color:#4CAF50;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;display:inline-block;">
                           Verify Email
                        </a>
                    </p>
                    <p>Or paste this link in your browser:</p>
                    <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 3px;">
                        {confirm_link}
                    </p>
                    <p style="color: #666; font-size: 12px;">
                        If you didn't request this, you can safely ignore this message.
                    </p>
                </div>
            '''
        )
        mail.send(msg)
        app.logger.info(f"Verification email sent to {email}")
        return True
    except Exception as e:
        app.logger.error(f"Failed to send verification email to {email}: {e}")
        return False

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('errors/429.html'), 429

# Security headers
@app.after_request
def after_request(response):
    """Add security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: *; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.tailwindcss.com cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com; "
        "font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com data:; "
        "img-src 'self' data: https: http: *; "
        "connect-src 'self' *;"
    )
    return response

# Request logging
@app.before_request
def log_request_info():
    if not app.debug:
        app.logger.info(f'{request.remote_addr} - {request.method} {request.url}')

# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/input")
def input_page():
    return render_template("input.html")

@app.route("/generate", methods=["POST"])
@limiter.limit("10 per minute")
def generate():
    app.logger.info("Generate route accessed")
    
    raw = request.form.get("ingredients", "")
    ingredients = [i.strip() for i in raw.split(",") if i.strip()]
    dietary_prefs = request.form.getlist("diet")
    page = int(request.form.get("page", 1))  # Get page number, default to 1
    
    app.logger.info(f"Ingredients: {ingredients}, Dietary prefs: {dietary_prefs}, Page: {page}")
    
    if not ingredients:
        app.logger.warning("No ingredients provided")
        flash("Please enter at least one ingredient.", "warning")
        return redirect(url_for("input_page"))

    # Save search to history
    if 'search_history' not in session:
        session['search_history'] = []
    
    search_term = ",".join(ingredients)
    if search_term not in session['search_history']:
        session['search_history'].insert(0, search_term)
        session['search_history'] = session['search_history'][:5]

    api_key = os.getenv("SPOONACULAR_API_KEY")
    
    try:
        app.logger.info(f"Making API request to Spoonacular for page {page}")
        
        # Use pagination with offset calculation
        if page > 1:
            offset = (page - 1) * 6  # 6 recipes per page
            resp = fetch_recipes_by_ingredients_with_offset(",".join(ingredients), dietary_prefs, api_key, offset)
        else:
            resp = fetch_recipes_by_ingredients(",".join(ingredients), dietary_prefs, api_key)
        
        app.logger.info(f"API Response Status: {resp.status_code}")
        app.logger.info(f"API Response Content: {resp.text[:500]}...")  # Log first 500 chars
        
        if resp.status_code == 402:
            app.logger.warning("API quota exceeded")
            flash("API quota exceeded. Please try again later.", "warning")
            return redirect(url_for("input_page"))
        elif resp.status_code == 401:
            app.logger.error("API authentication failed")
            flash("API authentication failed.", "danger")
            return redirect(url_for("input_page"))
        elif resp.status_code != 200:
            app.logger.error(f"API returned status {resp.status_code}")
            app.logger.error(f"API Error Response: {resp.text}")
            flash(f"Service temporarily unavailable. Please try again.", "danger")
            return redirect(url_for("input_page"))

        recipes_data = resp.json()
        app.logger.info(f"Retrieved {len(recipes_data)} recipes from API")
        
        # Process recipes with detailed nutrition info
        recipes = []
        for i, r in enumerate(recipes_data):
            try:
                # Get cached recipe details
                detail_resp = fetch_recipe_details(r['id'], api_key)
                recipe_details = detail_resp.json() if detail_resp.status_code == 200 else {}
            except Exception as e:
                app.logger.warning(f"Failed to get details for recipe {r['id']}: {e}")
                recipe_details = {}
            
            # Extract nutritional information
            nutrition = {}
            if recipe_details.get('nutrition'):
                nutrients = recipe_details['nutrition'].get('nutrients', [])
                for nutrient in nutrients:
                    name = nutrient.get('name', '').lower()
                    if 'calorie' in name:
                        nutrition['calories'] = int(nutrient.get('amount', 0))
                    elif 'protein' in name:
                        nutrition['protein'] = round(nutrient.get('amount', 0), 1)
                    elif 'carbohydrate' in name:
                        nutrition['carbs'] = round(nutrient.get('amount', 0), 1)
            
            # Extract dietary information
            dietary_info = []
            if recipe_details.get('vegetarian'):
                dietary_info.append('Vegetarian')
            if recipe_details.get('vegan'):
                dietary_info.append('Vegan')
            if recipe_details.get('glutenFree'):
                dietary_info.append('Gluten Free')
            if recipe_details.get('dairyFree'):
                dietary_info.append('Dairy Free')
            
            recipe = {
                "id": r["id"],
                "title": r["title"],
                "image": r["image"],
                "used": [ui.get("original", ui.get("name", "")) for ui in r.get("usedIngredients", [])],
                "missed": [mi.get("original", mi.get("name", "")) for mi in r.get("missedIngredients", [])],
                "nutrition": nutrition if nutrition else None,
                "readyInMinutes": recipe_details.get('readyInMinutes'),
                "servings": recipe_details.get('servings'),
                "dietary_info": dietary_info
            }
            recipes.append(recipe)

        # Cache recipes for offline access and save search history
        username = session.get('user')
        for recipe in recipes:
            cache_recipe_for_offline(recipe)
        
        # Save search to PWA history for offline access
        save_search_for_offline(username, search_term, ingredients, recipes)
        
        # Get user favorites if logged in
        user_favorites = []
        if username:
            user_favorites = get_user_favorites(username)
        
        app.logger.info(f"Successfully processed {len(recipes)} recipes")
        return render_template("result.html", recipes=recipes, user_favorites=user_favorites)
        
    except requests.exceptions.Timeout:
        app.logger.error("API request timeout")
        flash("Request timed out. Please try again.", "danger")
        return redirect(url_for("input_page"))
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request error: {e}")
        flash("Network error. Please check your connection.", "danger")
        return redirect(url_for("input_page"))
    except Exception as e:
        app.logger.error(f"Unexpected error in generate route: {e}", exc_info=True)
        flash("An unexpected error occurred. Please try again.", "danger")
        return redirect(url_for("input_page"))

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip().lower()

        # Enhanced input validation
        if not username or not password or not email:
            flash("Please fill in all fields.", "warning")
            return render_template("register.html")

        if not validate_username(username):
            flash("Username must be 3-20 characters and contain only letters, numbers, and underscores.", "warning")
            return render_template("register.html")
            
        if not validate_password(password):
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("register.html")
        
        if not validate_email(email):
            flash("Please enter a valid email address.", "warning")
            return render_template("register.html")

        # Check for existing users
        if username_exists(username):
            flash("Username is already taken.", "danger")
            return render_template("register.html")
            
        if any(d["username"] == username for d in pending_registrations.values()):
            flash("Username is pending verification.", "warning")
            return render_template("register.html")

        if email_exists_in_db(email):
            flash("Email is already registered.", "danger")
            return render_template("register.html")
            
        if any(d["email"] == email for d in pending_registrations.values()):
            flash("Email is pending verification.", "warning")
            return render_template("register.html")

        # Generate verification token
        token = os.urandom(32).hex()
        pending_registrations[token] = {
            "username": username,
            "password": password,
            "email": email
        }
        
        app.logger.info(f"Created pending registration for {username}")

        # Send verification email
        confirm_link = url_for("confirm_email", token=token, _external=True)
        if send_verification_email(email, confirm_link):
            flash("Please check your email to verify your account.", "success")
            return render_template("register_pending.html", email=email)
        else:
            pending_registrations.pop(token, None)
            flash("Could not send verification email. Please try again.", "danger")
            return render_template("register.html")

    return render_template("register.html")

@app.route("/confirm/<token>")
def confirm_email(token):
    app.logger.info(f"Email confirmation attempt for token: {token[:10]}...")
    
    if token not in pending_registrations:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for("register_page"))
    
    data = pending_registrations[token]
    app.logger.info(f"Found pending registration for: {data['username']}")
    
    # Double-check if username/email already exists
    if username_exists(data["username"]):
        pending_registrations.pop(token, None)
        flash("Username already taken. Please register with a different username.", "danger")
        return redirect(url_for("register_page"))
    
    if email_exists_in_db(data["email"]):
        pending_registrations.pop(token, None)
        flash("Email already registered. Please use a different email.", "danger")
        return redirect(url_for("register_page"))

    # Register the user
    if register_user(data["username"], data["password"], data["email"]):
        pending_registrations.pop(token, None)
        flash("🎉 Email verified successfully! You can now log in.", "success")
        return redirect(url_for("login"))
    else:
        flash("Error creating account. Please try again.", "danger")
        return redirect(url_for("register_page"))

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        app.logger.info(f"Login attempt for username: {username}")
        
        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return render_template("login.html")
        
        if verify_user(username, password):
            session["user"] = username
            session.permanent = True
            flash("Logged in successfully!", "success")
            app.logger.info(f"User {username} logged in successfully")
            return redirect(url_for("input_page"))
        else:
            flash("Invalid username or password.", "danger")
            app.logger.warning(f"Failed login attempt for {username}")

    return render_template("login.html")

@app.route("/logout")
def logout():
    username = session.get('user', 'Unknown')
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    app.logger.info(f"User {username} logged out")
    return redirect(url_for("home"))

@app.route("/resend-confirmation", methods=["POST"])
@limiter.limit("3 per minute")
def resend_confirmation():
    email = request.form.get("resend_email", "").strip()
    if not email:
        flash("Please enter your email address.", "warning")
        return redirect(url_for("register_page"))

    for token, data in pending_registrations.items():
        if data["email"] == email:
            confirm_link = url_for("confirm_email", token=token, _external=True)
            if send_verification_email(email, confirm_link):
                flash("Verification email resent successfully.", "success")
                return render_template("register_pending.html", email=email)
            else:
                flash("Failed to resend verification email.", "danger")
                return redirect(url_for("register_page"))

    flash("No pending registration found for this email.", "warning")
    return redirect(url_for("register_page"))

@app.route("/toggle-favorite", methods=["POST"])
@limiter.limit("30 per minute")
def toggle_favorite():
    """Toggle recipe favorite status"""
    if not session.get('user'):
        return jsonify({'error': 'Must be logged in'}), 401
    
    data = request.get_json()
    username = session['user']
    recipe_id = data.get('recipe_id')
    recipe_title = data.get('recipe_title')
    recipe_image = data.get('recipe_image')
    
    try:
        with get_db_connection() as conn:
            # Check if already favorited
            existing = conn.execute(
                'SELECT id FROM saved_recipes WHERE username = ? AND recipe_id = ?',
                (username, recipe_id)
            ).fetchone()
            
            if existing:
                # Remove from favorites
                conn.execute(
                    'DELETE FROM saved_recipes WHERE username = ? AND recipe_id = ?',
                    (username, recipe_id)
                )
                favorited = False
                app.logger.info(f"User {username} removed recipe {recipe_id} from favorites")
            else:
                # Add to favorites
                conn.execute(
                    'INSERT INTO saved_recipes (username, recipe_id, recipe_title, recipe_image) VALUES (?, ?, ?, ?)',
                    (username, recipe_id, recipe_title, recipe_image)
                )
                favorited = True
                app.logger.info(f"User {username} added recipe {recipe_id} to favorites")
        
        return jsonify({'favorited': favorited})
    
    except Exception as e:
        app.logger.error(f"Error toggling favorite: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route("/favorites")
def favorites():
    """Show user's favorite recipes"""
    if not session.get('user'):
        flash("Please log in to view favorites.", "warning")
        return redirect(url_for('login'))
    
    try:
        with get_db_connection() as conn:
            favorites = conn.execute(
                'SELECT recipe_id, recipe_title, recipe_image, saved_at FROM saved_recipes WHERE username = ? ORDER BY saved_at DESC',
                (session['user'],)
            ).fetchall()
        
        return render_template("favorites.html", favorites=favorites)
    except Exception as e:
        app.logger.error(f"Error fetching favorites: {e}")
        flash("Error loading favorites.", "danger")
        return redirect(url_for("input_page"))

@app.route("/clear-favorites", methods=["POST"])
@limiter.limit("5 per minute")
def clear_favorites():
    """Clear all user favorites"""
    if not session.get('user'):
        return jsonify({'error': 'Must be logged in'}), 401
    
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM saved_recipes WHERE username = ?', (session['user'],))
        
        app.logger.info(f"User {session['user']} cleared all favorites")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error clearing favorites: {e}")
        return jsonify({'error': 'Server error'}), 500

# Calorie lookup functionality removed - not needed

@app.route("/pwa-info")
def pwa_info():
    """Information page about PWA installation"""
    return render_template("pwa_info.html")

@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    """Get detailed information about a specific recipe"""
    try:
        api_key = os.getenv("SPOONACULAR_API_KEY")
        
        # Get cached recipe information
        resp = fetch_recipe_details(recipe_id, api_key)
        
        if resp.status_code != 200:
            flash("Could not fetch recipe details.", "danger")
            return redirect(url_for("input_page"))
        
        recipe = resp.json()
        
        # Get recipe instructions
        instructions_resp = requests.get(
            f"https://api.spoonacular.com/recipes/{recipe_id}/analyzedInstructions",
            params={"apiKey": api_key},
            timeout=10
        )
        
        instructions = []
        if instructions_resp.status_code == 200:
            instructions_data = instructions_resp.json()
            if instructions_data:
                instructions = instructions_data[0].get('steps', [])
        
        # Check if user has favorited this recipe
        is_favorited = False
        if session.get('user'):
            try:
                with get_db_connection() as conn:
                    existing = conn.execute(
                        'SELECT id FROM saved_recipes WHERE username = ? AND recipe_id = ?',
                        (session['user'], recipe_id)
                    ).fetchone()
                    is_favorited = existing is not None
            except Exception as e:
                app.logger.error(f"Error checking favorite status: {e}")
        
        return render_template("recipe_detail.html", recipe=recipe, instructions=instructions, is_favorited=is_favorited)
        
    except Exception as e:
        app.logger.error(f"Recipe detail error: {e}")
        flash("Error loading recipe details.", "danger")
        return redirect(url_for("input_page"))

# Initialize databases on startup
init_databases()

if __name__ == "__main__":
    app.logger.info("Starting Flask Recipe app...")
    app.logger.info(f"Mail server configured: {os.getenv('MAIL_SERVER') is not None}")
    app.logger.info(f"API key configured: {os.getenv('SPOONACULAR_API_KEY') is not None}")
    print(f"🔑 API key configured: {os.getenv('SPOONACULAR_API_KEY') is not None}")
    
    import sys
    if '--host' in sys.argv or '--network' in sys.argv:
        print("🌐 Running with network access enabled")
        print("📱 Your APK can now connect to this server")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("💻 Running in local mode only")
        print("🌐 To enable network access for APK, run with: python app.py --network")
        app.run(debug=True)


