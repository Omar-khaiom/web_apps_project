from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import load_dotenv
import os
import requests
import re
import logging
from datetime import timedelta
from logging.handlers import RotatingFileHandler



# Load environment variables
load_dotenv()


# Validate required environment variables (minimal set for local web app)
REQUIRED_ENV_VARS = ['SECRET_KEY', 'SPOONACULAR_API_KEY']
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

# Initialize extensions

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

# No authentication, email, or database functionality in this cleaned version

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

# Email functionality removed

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

    # Save search to in-memory session history (no persistent DB)
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

        app.logger.info(f"Successfully processed {len(recipes)} recipes")
        return render_template("result.html", recipes=recipes)
        
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

# Authentication, registration, and favorites endpoints removed

# Calorie lookup functionality removed - not needed

# Base app: remove PWA info route

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
        
        return render_template("recipe_detail.html", recipe=recipe, instructions=instructions, is_favorited=False)
        
    except Exception as e:
        app.logger.error(f"Recipe detail error: {e}")
        flash("Error loading recipe details.", "danger")
        return redirect(url_for("input_page"))

if __name__ == "__main__":
    app.logger.info("Starting Flask Recipe app...")
    app.logger.info(f"API key configured: {os.getenv('SPOONACULAR_API_KEY') is not None}")
    print(f"🔑 API key configured: {os.getenv('SPOONACULAR_API_KEY') is not None}")
    app.run(debug=True)


