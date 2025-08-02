from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import requests
import traceback

from data import calorie_lookup
from auth import register_user, verify_user, get_user_email, username_exists, email_exists_in_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)

# Flask-Mail setup
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")) if os.getenv("MAIL_PORT") else 587,
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS") == "true",
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME")
)
mail = Mail(app)

# Store pending registrations
pending_registrations = {}

def send_verification_email(email, confirm_link):
    try:
        msg = Message(
            subject="Confirm Your Email - SmartRecipes",
            recipients=[email],
            html=f'''
                <h2>Welcome to SmartRecipes!</h2>
                <p>Please verify your email address by clicking the button below:</p>
                <p><a href="{confirm_link}" style="background-color:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Verify Email</a></p>
                <p>Or paste this link in your browser: {confirm_link}</p>
                <p>If you didn't request this, you can ignore this message.</p>
            '''
        )
        mail.send(msg)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print("Flask-Mail error:", e)
        return False

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/input")
def input_page():
    return render_template("input.html")

@app.route("/generate", methods=["POST"])
def generate():
    print("=== GENERATE ROUTE STARTED ===")
    
    raw = request.form.get("ingredients", "")
    ingredients = [i.strip() for i in raw.split(",") if i.strip()]
    
    print(f"Raw ingredients input: '{raw}'")
    print(f"Processed ingredients: {ingredients}")
    
    if not ingredients:
        print("No ingredients provided")
        flash("Please enter at least one ingredient.", "warning")
        return redirect(url_for("input_page"))

    # Check environment variables
    api_key = os.getenv("SPOONACULAR_API_KEY")
    print(f"API key exists: {api_key is not None}")
    if api_key:
        print(f"API key first 10 chars: {api_key[:10]}...")
    else:
        print("ERROR: No API key found in environment!")
        flash("Configuration error. Please contact support.", "danger")
        return redirect(url_for("input_page"))

    try:
        print("Making API request...")
        
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": ",".join(ingredients), 
            "number": 6, 
            "apiKey": api_key
        }
        
        print(f"Request URL: {url}")
        print(f"Request params: {params}")
        
        resp = requests.get(url, params=params, timeout=10)
        
        print(f"API Response Status: {resp.status_code}")
        print(f"Response headers: {dict(resp.headers)}")
        print(f"Response content (first 500 chars): {resp.text[:500]}")

        if resp.status_code == 402:
            print("API quota exceeded")
            flash("API quota exceeded. Please try again later.", "warning")
            return redirect(url_for("input_page"))
        elif resp.status_code == 401:
            print("API authentication failed")
            flash("API authentication failed.", "danger")
            return redirect(url_for("input_page"))
        elif resp.status_code != 200:
            print(f"API returned non-200 status: {resp.status_code}")
            flash(f"API error (status {resp.status_code}). Try again.", "danger")
            return redirect(url_for("input_page"))

        print("Parsing JSON response...")
        recipes_data = resp.json()
        print(f"Number of recipes returned: {len(recipes_data)}")
        
        recipes = []
        for i, r in enumerate(recipes_data):
            print(f"Processing recipe {i}: {r.get('title', 'No title')}")
            recipe = {
                "id": r["id"],
                "title": r["title"],
                "image": r["image"],
                "used": [ui.get("original", ui.get("name", "")) for ui in r.get("usedIngredients", [])],
                "missed": [mi.get("original", mi.get("name", "")) for mi in r.get("missedIngredients", [])]
            }
            recipes.append(recipe)

        print(f"Successfully processed {len(recipes)} recipes")
        print("=== GENERATE ROUTE SUCCESS ===")
        return render_template("result.html", recipes=recipes)
        
    except requests.exceptions.Timeout as e:
        print(f"Request timeout: {e}")
        flash("Request timed out. Please try again.", "danger")
        return redirect(url_for("input_page"))
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        flash("Network error. Check your connection.", "danger")
        return redirect(url_for("input_page"))
    except ValueError as e:
        print(f"JSON parsing error: {e}")
        flash("Invalid response from API. Try again.", "danger")
        return redirect(url_for("input_page"))
    except KeyError as e:
        print(f"Missing key in API response: {e}")
        flash("Unexpected API response format.", "danger")
        return redirect(url_for("input_page"))
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        flash("An unexpected error occurred. Please try again.", "danger")
        return redirect(url_for("input_page"))

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()

        if not username or not password or not email:
            flash("Please fill in all fields.", "warning")
            return render_template("register.html")

        if len(username) < 3 or len(password) < 6:
            flash("Username must be at least 3 chars, password at least 6.", "warning")
            return render_template("register.html")

        if username_exists(username) or any(d["username"] == username for d in pending_registrations.values()):
            flash("Username is taken or pending verification.", "danger")
            return render_template("register.html")

        if email_exists_in_db(email) or any(d["email"] == email for d in pending_registrations.values()):
            flash("Email already used or pending.", "danger")
            return render_template("register.html")

        token = os.urandom(16).hex()
        pending_registrations[token] = {
            "username": username,
            "password": password,
            "email": email
        }

        confirm_link = url_for("confirm_email", token=token, _external=True)
        if send_verification_email(email, confirm_link):
            flash("Check your email to verify.", "success")
            return render_template("register_pending.html", email=email)
        else:
            pending_registrations.pop(token, None)
            flash("Could not send verification email.", "danger")
            return render_template("register.html")

    return render_template("register.html")

@app.route("/confirm/<token>")
def confirm_email(token):
    if token in pending_registrations:
        data = pending_registrations.pop(token)
        if username_exists(data["username"]) or email_exists_in_db(data["email"]):
            flash("Username/email taken. Try again.", "danger")
            return redirect(url_for("register_page"))

        if register_user(data["username"], data["password"], data["email"]):
            flash("🎉 Email verified. You can now log in.", "success")
            return redirect(url_for("login_page"))
        else:
            flash("Error creating account.", "danger")
            return redirect(url_for("register_page"))
    else:
        flash("Invalid or expired link.", "danger")
        return redirect(url_for("register_page"))

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Fill all fields.", "warning")
            return render_template("login.html")

        if verify_user(username, password):
            session["user"] = username
            flash("Welcome back!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid login.", "danger")

    return render_template("login.html")

@app.route("/resend-confirmation", methods=["POST"])
def resend_confirmation():
    email = request.form.get("resend_email", "").strip()
    if not email:
        flash("Enter your email.", "warning")
        return redirect(url_for("register_page"))

    for token, data in pending_registrations.items():
        if data["email"] == email:
            confirm_link = url_for("confirm_email", token=token, _external=True)
            if send_verification_email(email, confirm_link):
                flash("Verification email resent.", "success")
                return render_template("register_pending.html", email=email)
            else:
                flash("Failed to resend email.", "danger")
                return redirect(url_for("register_page"))

    flash("No pending registration found.", "danger")
    return redirect(url_for("register_page"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("home"))

@app.route("/calories", methods=["POST"])
def calories():
    raw = request.form.get("ingredients", "")
    ingredients = [i.strip() for i in raw.split(",") if i.strip()]
    if not ingredients:
        flash("Please enter ingredients.", "warning")
        return redirect(url_for("input_page"))

    try:
        total, breakdown = calorie_lookup(ingredients)
        return render_template("calories.html", total=total, breakdown=breakdown)
    except Exception as e:
        print(f"Calorie lookup error: {e}")
        flash("Error calculating calories.", "danger")
        return redirect(url_for("input_page"))

@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    """Get detailed information about a specific recipe"""
    try:
        api_key = os.getenv("SPOONACULAR_API_KEY")
        if not api_key:
            flash("Configuration error.", "danger")
            return redirect(url_for("input_page"))
        
        # Get recipe information
        resp = requests.get(
            f"https://api.spoonacular.com/recipes/{recipe_id}/information",
            params={"apiKey": api_key},
            timeout=10
        )
        
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
        
        return render_template("recipe_detail.html", recipe=recipe, instructions=instructions)
        
    except Exception as e:
        print(f"Recipe detail error: {e}")
        flash("Error loading recipe details.", "danger")
        return redirect(url_for("input_page"))

# Debug test route
@app.route("/test-debug")
def test_debug():
    print("DEBUG TEST ROUTE WORKING!")
    api_key = os.getenv("SPOONACULAR_API_KEY")
    return f"Debug test successful - API key exists: {api_key is not None}"

if __name__ == "__main__":
    app.run(debug=True)