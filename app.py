from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import requests
from data import calorie_lookup
from auth import register_user, verify_user

# Load env vars
load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Flask setup
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("EMAIL_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASS"),
)
mail = Mail(app)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/input")
def input_page():
    return render_template("input.html")


@app.route("/generate", methods=["POST"])
def generate():
    raw = request.form["ingredients"]
    ingredients = [i.strip() for i in raw.split(",") if i.strip()]
    if not ingredients:
        flash("Please enter at least one ingredient.", "warning")
        return redirect(url_for("input_page"))

    resp = requests.get(
        "https://api.spoonacular.com/recipes/findByIngredients",
        params={
            "ingredients": ",".join(ingredients),
            "number": 3,
            "apiKey": SPOONACULAR_API_KEY
        }
    )
    if resp.status_code != 200:
        flash("Could not fetch recipes. Try again.", "danger")
        return redirect(url_for("input_page"))

    recipes_data = resp.json()
    recipes = []
    for r in recipes_data:
        recipes.append({
            "id": r["id"],
            "title": r["title"],
            "image": r["image"],
            # <- FIXED: use 'original' instead of non-existent 'originalString'
            "used":   [ui.get("original", ui.get("name")) for ui in r.get("usedIngredients", [])],
            "missed":[mi.get("original", mi.get("name")) for mi in r.get("missedIngredients", [])],
        })

    return render_template("result.html", recipes=recipes)


@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    resp = requests.get(
        f"https://api.spoonacular.com/recipes/{recipe_id}/information",
        params={"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    )
    if resp.status_code != 200:
        flash("Could not fetch recipe details.", "danger")
        return redirect(url_for("home"))

    data = resp.json()

    # Prepare ingredients list as the template expects (with 'text' and optional 'aisle')
    ingredients = [{
        "text": ing.get("original", ing.get("name")),
        "aisle": ing.get("aisle")
    } for ing in data.get("extendedIngredients", [])]

    # Steps from analyzedInstructions
    steps = []
    analyzed = data.get("analyzedInstructions", [])
    if analyzed and analyzed[0].get("steps"):
        steps = [step["step"] for step in analyzed[0]["steps"]]

    # Nutrition is already a list in data['nutrition']['nutrients']
    nutrition = data.get("nutrition", {}).get("nutrients", [])

    return render_template("recipe_detail.html", recipe={
        "title": data.get("title"),
        "image": data.get("image"),
        "ingredients": ingredients,           # matches template use of recipe.ingredients
        "instructions": data.get("instructions") or "",
        "steps": steps,
        "readyInMinutes": data.get("readyInMinutes"),
        "servings": data.get("servings"),
        "sourceName": data.get("sourceName"),
        "nutrition": nutrition                 # flat list, matches template's recipe.nutrition
    })

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        if verify_user(request.form["username"], request.form["password"]):
            session["user"] = request.form["username"]
            flash("Logged in!", "success")
            return redirect(url_for("home"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        user, pw, email = (request.form[k] for k in ("username", "password", "email"))
        if register_user(user, pw, email):
            token = os.urandom(16).hex()
            url = url_for("confirm_email", token=token, _external=True)
            msg = Message("Confirm Email",
                          sender=app.config["MAIL_USERNAME"],
                          recipients=[email],
                          body=f"Click to confirm: {url}")
            mail.send(msg)
            flash("Registered! Check your email.", "success")
            return redirect(url_for("login_page"))
        flash("Username taken.", "danger")
    return render_template("register.html")


@app.route("/confirm/<token>")
def confirm_email(token):
    flash("Email confirmed!", "success")
    return redirect(url_for("login_page"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("home"))


@app.route("/calories", methods=["POST"])
def calories():
    ing_list = [i.strip() for i in request.form["ingredients"].split(",")]
    total, breakdown = calorie_lookup(ing_list)
    return render_template("calories.html", total=total, breakdown=breakdown)


if __name__ == "__main__":
    app.run(debug=True)
