from flask import Flask, render_template, request
from openai import OpenAI
import os
from dotenv import load_dotenv
from data import calorie_lookup

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/input")
def input_page():
    return render_template("input.html")
@app.route("/register")
def register():
    return render_template("register.html")
@app.route("/generate", methods=["POST"])
def generate():
    ingredients = request.form["ingredients"]
    prompt = f"Suggest 3 simple recipes using only these ingredients: {ingredients}. Keep it short and beginner friendly."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )

    recipes = response.choices[0].message.content
    return render_template("result.html", recipes=recipes)

@app.route("/calories", methods=["POST"])
def calories():
    ingredients = request.form["ingredients"]
    ing_list = [i.strip() for i in ingredients.split(",")]
    total, breakdown = calorie_lookup(ing_list)
    return render_template("calories.html", total=total, breakdown=breakdown)

if __name__ == "__main__":
    app.run(debug=True)
