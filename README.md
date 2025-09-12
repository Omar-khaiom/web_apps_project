# SmartRecipes (Web App Only)

Minimal Flask web app for searching recipes via the Spoonacular API. Auth, hosting, mobile (APK/Capacitor), and PWA features have been removed.

## What's included
- `app.py`: Flask server with routes for home, input, recipe generation, and recipe detail
- `templates/`: Jinja2 templates (`layout.html`, `home.html`, `input.html`, `result.html`, `recipe_detail.html`, `errors/`)
- `static/images/`: Background images used by templates
- `requirements.txt`: Python dependencies

## Requirements
- Python 3.10+
- Spoonacular API key

## Setup
1) Create and activate a virtual environment (recommended)
2) Install dependencies:
   - `pip install -r requirements.txt`
3) Create a `.env` file with:
   - `SECRET_KEY=your_random_secret_key`
   - `SPOONACULAR_API_KEY=your_api_key`

## Run locally
`python app.py`

App runs at `http://127.0.0.1:5000`.

## Routes
- `/` Home
- `/input` Ingredient input and options
- `/generate` POST: fetch recipes from Spoonacular
- `/recipe/<id>` Recipe details and instructions

## Project structure
```
app.py
requirements.txt
templates/
  layout.html
  home.html
  input.html
  result.html
  recipe_detail.html
  errors/
    404.html
    429.html
    500.html
static/
  images/
    land.jpg
    landing-page.jpg
```

## Notes
- Favorites, login/register, email, PWA, and APK/Android build files were removed.
- You can add your own auth/hosting (e.g., Supabase) later without changing the current flow.
