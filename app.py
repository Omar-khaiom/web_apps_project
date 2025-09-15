from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import load_dotenv
import os
import math
import requests
import re
import logging
from datetime import timedelta
from logging.handlers import RotatingFileHandler

# -------- constants & resilient HTTP session --------
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RECIPES_PER_PAGE = 12      # aligned pagination
REQUEST_TIMEOUT = 15        # seconds

def _build_session():
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"])
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

session_http = _build_session()
# ----------------------------------------------------

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

def normalize_ingredient_name(name):
    """Normalize ingredient name for better matching"""
    if not name:
        return ""
    
    # Convert to lowercase and remove extra spaces
    normalized = name.lower().strip()
    
    # Remove common measurement words and quantities
    measurement_words = ['cup', 'cups', 'tbsp', 'tablespoon', 'tablespoons', 'tsp', 'teaspoon', 'teaspoons', 
                        'oz', 'ounce', 'ounces', 'lb', 'pound', 'pounds', 'g', 'gram', 'grams', 'kg', 'kilogram',
                        'ml', 'milliliter', 'milliliters', 'l', 'liter', 'liters', 'pinch', 'dash', 'handful',
                        'clove', 'cloves', 'slice', 'slices', 'piece', 'pieces', 'can', 'cans', 'bunch', 'bunches']
    
    # Remove numbers and measurement words
    words = normalized.split()
    filtered_words = []
    for word in words:
        # Skip if it's just a number or measurement word
        if not (word.isdigit() or word in measurement_words):
            filtered_words.append(word)
    
    return ' '.join(filtered_words)

# ---------- Helpers for server-side diet filters ----------
def _map_dietary_prefs_to_api_params(dietary_prefs):
    """
    Map form values to Spoonacular complexSearch params.
    - diet: supports 'vegetarian', 'vegan', 'gluten free', etc.
    - intolerances: supports 'dairy', 'gluten', 'peanut', etc.
    We handle the common ones from your UI.
    """
    if not dietary_prefs:
        return None, None

    diets = []
    intolerances = []

    for pref in dietary_prefs:
        p = pref.strip().lower()
        if p == "vegetarian":
            diets.append("vegetarian")
        elif p == "vegan":
            diets.append("vegan")
        elif p == "gluten free":
            diets.append("gluten free")
        elif p == "dairy free":
            intolerances.append("dairy")
        # add more mappings if your UI has more options

    # De-duplicate
    diets = list(dict.fromkeys(diets))
    intolerances = list(dict.fromkeys(intolerances))

    diet_param = ",".join(diets) if diets else None
    intolerance_param = ",".join(intolerances) if intolerances else None
    return diet_param, intolerance_param
# ----------------------------------------------------------

# API helper functions (now using complexSearch for server-side filtering)
def fetch_recipes_by_ingredients_with_offset(ingredients_str, dietary_prefs, api_key, offset=0):
    """
    Fetch recipes with Spoonacular complexSearch (supports diet/intolerances).
    We also request addRecipeInformation & addRecipeNutrition so we can avoid
    extra detail calls for most fields, but we still keep details for robustness
    and for the recipe detail page.
    """
    url = "https://api.spoonacular.com/recipes/complexSearch"

    diet_param, intolerance_param = _map_dietary_prefs_to_api_params(dietary_prefs)

    params = {
        "includeIngredients": ingredients_str,
        "number": RECIPES_PER_PAGE,
        "offset": offset,
        "apiKey": api_key,
        "addRecipeInformation": True,
        "addRecipeNutrition": True,
        # You can also add sort=popularity|healthiness|... if desired
    }
    if diet_param:
        params["diet"] = diet_param
    if intolerance_param:
        params["intolerances"] = intolerance_param

    print(f"🔍 API URL: {url}")
    print(f"📊 API Params: {params}")

    resp = session_http.get(url, params=params, timeout=REQUEST_TIMEOUT)

    print(f"📡 API Response Status: {resp.status_code}")
    print(f"📄 API Response Length: {len(resp.text)}")

    return resp

# Legacy function for caching compatibility
@cache.memoize(timeout=1800)  # Cache for 30 minutes (shorter to allow variety)
def fetch_recipes_by_ingredients(ingredients_str, dietary_prefs, api_key):
    """Fetch recipes with caching (complexSearch, page 1)"""
    return fetch_recipes_by_ingredients_with_offset(ingredients_str, dietary_prefs, api_key, 0)

@cache.memoize(timeout=3600)
def fetch_recipe_details(recipe_id, api_key):
    """Fetch detailed recipe information with caching"""
    response = session_http.get(
        f"https://api.spoonacular.com/recipes/{recipe_id}/information",
        params={"apiKey": api_key, "includeNutrition": True},
        timeout=REQUEST_TIMEOUT
    )
    return response

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
    # Tightened CSP (no default-src *; no unsafe-eval)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com use.fontawesome.com; "
        "font-src 'self' fonts.gstatic.com data: cdnjs.cloudflare.com use.fontawesome.com cdn.jsdelivr.net; "
        "connect-src 'self' https://api.spoonacular.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
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
    dietary_prefs = request.form.getlist("diet")  # e.g., ['Vegetarian','Vegan','Gluten Free','Dairy Free']
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
    
    # Store current search parameters for pagination (total_pages updated after API call)
    session['current_search'] = {
        'ingredients': ingredients,
        'dietary_prefs': dietary_prefs,
        'current_page': page,
        'total_pages': 1
    }

    api_key = os.getenv("SPOONACULAR_API_KEY")

    try:
        app.logger.info(f"Making API request to Spoonacular for page {page}")

        # Pagination with offset calculation (aligned with RECIPES_PER_PAGE)
        if page > 1:
            offset = (page - 1) * RECIPES_PER_PAGE
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

        # Parse complexSearch payload safely
        try:
            payload = resp.json()
        except ValueError:
            app.logger.error("Invalid JSON from API (complexSearch)")
            flash("Upstream error. Please try again.", "danger")
            return redirect(url_for("input_page"))

        results = payload.get("results", [])
        # Update total pages from API totalResults if available
        total_results = payload.get("totalResults") or 0
        total_pages = max(1, math.ceil(total_results / RECIPES_PER_PAGE)) if total_results else 1
        session['current_search']['total_pages'] = total_pages
        app.logger.info(f"Retrieved {len(results)} recipes from complexSearch")

        # Build recipe cards; still call details (cached) for consistency & robustness
        provided_names = {x.lower() for x in ingredients}
        recipes = []

        for r in results:
            rid = r.get("id")
            title = r.get("title")
            image = r.get("image")

            # Try to use info already present from addRecipeInformation
            extended = r.get("extendedIngredients") or []
            app.logger.info(f"Recipe {rid} has {len(extended)} extended ingredients from complexSearch")
            # Nutrition may be included via addRecipeNutrition
            nutrition = {}
            try:
                if "nutrition" in r and r["nutrition"].get("nutrients"):
                    for nutrient in r["nutrition"]["nutrients"]:
                        name = (nutrient.get("name") or "").lower()
                        if 'calorie' in name:
                            nutrition['calories'] = int(round(float(nutrient.get('amount', 0))))
                        elif 'protein' in name:
                            nutrition['protein'] = round(float(nutrient.get('amount', 0)), 1)
                        elif 'carbohydrate' in name:
                            nutrition['carbs'] = round(float(nutrient.get('amount', 0)), 1)
            except Exception as e:
                app.logger.warning(f"Nutrition parse (from complexSearch) failed for recipe {rid}: {e}")

            # Process ingredients after we have all the data
            used_list = []
            missed_list = []

            # Pull details (cached) to fill anything missing & ensure flags are accurate
            recipe_details = {}
            try:
                detail_resp = fetch_recipe_details(rid, api_key)
                if detail_resp.status_code == 200:
                    try:
                        recipe_details = detail_resp.json()
                        app.logger.info(f"Successfully fetched details for recipe {rid}")
                    except ValueError:
                        recipe_details = {}
                else:
                    app.logger.warning(f"Details fetch failed for recipe {rid} status {detail_resp.status_code}")
            except Exception as e:
                app.logger.warning(f"Failed to get details for recipe {rid}: {e}")

            # If we don't have extended ingredients from complexSearch, try to get them from details
            if not extended and recipe_details.get("extendedIngredients"):
                extended = recipe_details.get("extendedIngredients", [])
                app.logger.info(f"Got {len(extended)} extended ingredients from recipe details for recipe {rid}")

            # Now process ingredients with the best available data
            try:
                app.logger.info(f"Processing ingredients for recipe {rid}. Provided ingredients: {provided_names}")
                app.logger.info(f"Extended ingredients count: {len(extended)}")
                
                # Normalize provided ingredients for better matching
                normalized_provided = {normalize_ingredient_name(ing) for ing in provided_names}
                app.logger.info(f"Normalized provided ingredients: {normalized_provided}")
                
                for ing in extended:
                    nm = (ing.get("name") or "").lower()
                    original_txt = ing.get("original") or ing.get("originalName") or nm
                    normalized_ingredient = normalize_ingredient_name(original_txt)
                    
                    app.logger.info(f"Checking ingredient: '{original_txt}' (normalized: '{normalized_ingredient}')")
                    
                    # Improved matching: check if any provided ingredient matches the recipe ingredient
                    is_used = False
                    matched_provided = None
                    
                    for provided_ing in provided_names:
                        normalized_provided_ing = normalize_ingredient_name(provided_ing)
                        
                        # More flexible matching - check various combinations
                        if (normalized_provided_ing in normalized_ingredient or 
                            normalized_ingredient in normalized_provided_ing or
                            any(word in normalized_ingredient for word in normalized_provided_ing.split() if len(word) > 2) or
                            any(word in normalized_provided_ing for word in normalized_ingredient.split() if len(word) > 2) or
                            # Check if any word from provided ingredient appears in recipe ingredient
                            any(prov_word in normalized_ingredient for prov_word in normalized_provided_ing.split() if len(prov_word) > 2)):
                            is_used = True
                            matched_provided = provided_ing
                            break
                    
                    if is_used:
                        used_list.append(original_txt)
                        app.logger.info(f"✅ Matched ingredient: '{original_txt}' (matched with provided: '{matched_provided}')")
                    else:
                        missed_list.append(original_txt)
                        app.logger.info(f"❌ Missed ingredient: '{original_txt}'")
                        
            except Exception as e:
                app.logger.warning(f"Extended ingredients parse failed for recipe {rid}: {e}")
                # Fallback: if extended ingredients parsing fails, use basic ingredients
                if not used_list and not missed_list and extended:
                    for ing in extended:
                        original_txt = ing.get("original") or ing.get("originalName") or ing.get("name", "")
                        missed_list.append(original_txt)

            # Ensure we have some ingredients to display - show actual ingredients instead of fallback message
            if not used_list and not missed_list:
                app.logger.warning(f"No ingredients found for recipe {rid}, using extended ingredients as missed")
                if extended:
                    for ing in extended:
                        original_txt = ing.get("original") or ing.get("originalName") or ing.get("name", "")
                        if original_txt:
                            missed_list.append(original_txt)
                else:
                    missed_list = ["Ingredients not available"]

            # If nutrition missing, try to parse from details
            if not nutrition and recipe_details.get('nutrition'):
                try:
                    for nutrient in recipe_details['nutrition'].get('nutrients', []):
                        name = (nutrient.get('name') or "").lower()
                        if 'calorie' in name:
                            nutrition['calories'] = int(round(float(nutrient.get('amount', 0))))
                        elif 'protein' in name:
                            nutrition['protein'] = round(float(nutrient.get('amount', 0)), 1)
                        elif 'carbohydrate' in name:
                            nutrition['carbs'] = round(float(nutrient.get('amount', 0)), 1)
                except Exception as e:
                    app.logger.warning(f"Nutrition parse (from details) failed for recipe {rid}: {e}")

            # Dietary badges (from details preferred)
            dietary_info = []
            src = recipe_details or r
            if src.get('vegetarian'):
                dietary_info.append('Vegetarian')
            if src.get('vegan'):
                dietary_info.append('Vegan')
            if src.get('glutenFree'):
                dietary_info.append('Gluten Free')
            if src.get('dairyFree'):
                dietary_info.append('Dairy Free')

            recipe = {
                "id": rid,
                "title": title,
                "image": image,
                "used": used_list,
                "missed": missed_list,
                "nutrition": nutrition if nutrition else None,
                "readyInMinutes": recipe_details.get('readyInMinutes') or r.get('readyInMinutes'),
                "servings": recipe_details.get('servings') or r.get('servings'),
                "dietary_info": dietary_info
            }
            recipes.append(recipe)

        app.logger.info(f"Successfully processed {len(recipes)} recipes (server-side filtered)")
        
        # Store recipes in session for GET redirect
        session['current_recipes'] = recipes
        
        # Redirect to GET route to prevent resubmission on back navigation
        return redirect(url_for("results", page=page))

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

@app.route("/results")
def results():
    """GET route for results to prevent resubmission on back navigation"""
    page = int(request.args.get("page", 1))
    
    # Get recipes and search info from session
    recipes = session.get('current_recipes', [])
    current_search = session.get('current_search', {})
    
    if not recipes or not current_search:
        flash("No search results found. Please search for recipes first.", "warning")
        return redirect(url_for("input_page"))
    
    total_pages = current_search.get('total_pages', 1)
    
    return render_template("result.html", recipes=recipes, current_page=page, total_pages=total_pages)



@app.route("/load-more-recipes", methods=["POST"])
@limiter.limit("10 per minute")
def load_more_recipes():
    """Navigate recipe pages (next/prev) for the current search and return updated HTML"""
    app.logger.info("Load more recipes route accessed")
    
    # Get current search from session
    current_search = session.get('current_search')
    if not current_search:
        flash("No active search found. Please search for recipes first.", "warning")
        return redirect(url_for("input_page"))
    
    # Determine direction and target page
    direction = (request.form.get('direction') or 'next').lower()
    cur = int(current_search.get('current_page', 1) or 1)
    total_pages = int(current_search.get('total_pages', 1) or 1)
    if direction == 'prev':
        target_page = max(1, cur - 1)
    else:
        target_page = min(total_pages, cur + 1)
    session['current_search']['current_page'] = target_page
    
    # Get API key
    api_key = os.getenv("SPOONACULAR_API_KEY")
    
    try:
        app.logger.info(f"Loading page {target_page} for current search (direction={direction})")
        
        # Fetch target page of recipes
        offset = (target_page - 1) * RECIPES_PER_PAGE
        resp = fetch_recipes_by_ingredients_with_offset(
            ",".join(current_search['ingredients']), 
            current_search['dietary_prefs'], 
            api_key, 
            offset
        )
        
        app.logger.info(f"API Response Status: {resp.status_code}")
        
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
            flash(f"Service temporarily unavailable. Please try again.", "danger")
            return redirect(url_for("input_page"))
        
        # Parse response
        try:
            payload = resp.json()
        except ValueError:
            app.logger.error("Invalid JSON from API")
            flash("Upstream error. Please try again.", "danger")
            return redirect(url_for("input_page"))
        
        results = payload.get("results", [])
        # Update total pages based on API response if available
        total_results = payload.get("totalResults") or 0
        if total_results:
            session['current_search']['total_pages'] = max(1, math.ceil(total_results / RECIPES_PER_PAGE))
        app.logger.info(f"Retrieved {len(results)} recipes for page {target_page}")
        
        # Process recipes (same logic as generate route)
        provided_names = {x.lower() for x in current_search['ingredients']}
        recipes = []
        
        for r in results:
            rid = r.get("id")
            title = r.get("title")
            image = r.get("image")
            
            # Process ingredients and nutrition (same as generate route)
            extended = r.get("extendedIngredients") or []
            nutrition = {}
            
            # Get nutrition data
            try:
                if "nutrition" in r and r["nutrition"].get("nutrients"):
                    for nutrient in r["nutrition"]["nutrients"]:
                        name = (nutrient.get("name") or "").lower()
                        if 'calorie' in name:
                            nutrition['calories'] = int(round(float(nutrient.get('amount', 0))))
                        elif 'protein' in name:
                            nutrition['protein'] = round(float(nutrient.get('amount', 0)), 1)
                        elif 'carbohydrate' in name:
                            nutrition['carbs'] = round(float(nutrient.get('amount', 0)), 1)
            except Exception as e:
                app.logger.warning(f"Nutrition parse failed for recipe {rid}: {e}")
            
            # Get recipe details for additional info
            recipe_details = {}
            try:
                detail_resp = fetch_recipe_details(rid, api_key)
                if detail_resp.status_code == 200:
                    try:
                        recipe_details = detail_resp.json()
                    except ValueError:
                        recipe_details = {}
            except Exception as e:
                app.logger.warning(f"Failed to get details for recipe {rid}: {e}")
            
            # Process ingredients
            used_list = []
            missed_list = []
            
            if not extended and recipe_details.get("extendedIngredients"):
                extended = recipe_details.get("extendedIngredients", [])
            
            try:
                normalized_provided = {normalize_ingredient_name(ing) for ing in provided_names}
                
                for ing in extended:
                    nm = (ing.get("name") or "").lower()
                    original_txt = ing.get("original") or ing.get("originalName") or nm
                    normalized_ingredient = normalize_ingredient_name(original_txt)
                    
                    is_used = False
                    matched_provided = None
                    
                    for provided_ing in provided_names:
                        normalized_provided_ing = normalize_ingredient_name(provided_ing)
                        
                        if (normalized_provided_ing in normalized_ingredient or 
                            normalized_ingredient in normalized_provided_ing or
                            any(word in normalized_ingredient for word in normalized_provided_ing.split() if len(word) > 2) or
                            any(word in normalized_provided_ing for word in normalized_ingredient.split() if len(word) > 2) or
                            any(prov_word in normalized_ingredient for prov_word in normalized_provided_ing.split() if len(prov_word) > 2)):
                            is_used = True
                            matched_provided = provided_ing
                            break
                    
                    if is_used:
                        used_list.append(original_txt)
                    else:
                        missed_list.append(original_txt)
                        
            except Exception as e:
                app.logger.warning(f"Extended ingredients parse failed for recipe {rid}: {e}")
                if not used_list and not missed_list and extended:
                    for ing in extended:
                        original_txt = ing.get("original") or ing.get("originalName") or ing.get("name", "")
                        missed_list.append(original_txt)
            
            # Ensure we have some ingredients to display
            if not used_list and not missed_list:
                if extended:
                    for ing in extended:
                        original_txt = ing.get("original") or ing.get("originalName") or ing.get("name", "")
                        if original_txt:
                            missed_list.append(original_txt)
                else:
                    missed_list = ["Ingredients not available"]
            
            # Get nutrition from details if missing
            if not nutrition and recipe_details.get('nutrition'):
                try:
                    for nutrient in recipe_details['nutrition'].get('nutrients', []):
                        name = (nutrient.get('name') or "").lower()
                        if 'calorie' in name:
                            nutrition['calories'] = int(round(float(nutrient.get('amount', 0))))
                        elif 'protein' in name:
                            nutrition['protein'] = round(float(nutrient.get('amount', 0)), 1)
                        elif 'carbohydrate' in name:
                            nutrition['carbs'] = round(float(nutrient.get('amount', 0)), 1)
                except Exception as e:
                    app.logger.warning(f"Nutrition parse (from details) failed for recipe {rid}: {e}")
            
            # Dietary badges
            dietary_info = []
            src = recipe_details or r
            if src.get('vegetarian'):
                dietary_info.append('Vegetarian')
            if src.get('vegan'):
                dietary_info.append('Vegan')
            if src.get('glutenFree'):
                dietary_info.append('Gluten Free')
            if src.get('dairyFree'):
                dietary_info.append('Dairy Free')
            
            recipe = {
                "id": rid,
                "title": title,
                "image": image,
                "used": used_list,
                "missed": missed_list,
                "nutrition": nutrition if nutrition else None,
                "readyInMinutes": recipe_details.get('readyInMinutes') or r.get('readyInMinutes'),
                "servings": recipe_details.get('servings') or r.get('servings'),
                "dietary_info": dietary_info
            }
            recipes.append(recipe)
        
        app.logger.info(f"Successfully processed {len(recipes)} recipes for page {target_page}")
        
        # Store updated recipes in session
        session['current_recipes'] = recipes
        
        return render_template("result.html", recipes=recipes, current_page=target_page, total_pages=session['current_search']['total_pages'])
        
    except requests.exceptions.Timeout:
        app.logger.error("API request timeout")
        flash("Request timed out. Please try again.", "danger")
        return redirect(url_for("input_page"))
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request error: {e}")
        flash("Network error. Please check your connection.", "danger")
        return redirect(url_for("input_page"))
    except Exception as e:
        app.logger.error(f"Unexpected error in load_more_recipes route: {e}", exc_info=True)
        flash("An unexpected error occurred. Please try again.", "danger")
        return redirect(url_for("input_page"))

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

        try:
            recipe = resp.json()
        except ValueError:
            app.logger.error("Invalid JSON from API (recipe_detail)")
            flash("Upstream error. Please try again.", "danger")
            return redirect(url_for("input_page"))

        # Get recipe instructions (sometimes not included in details)
        instructions_resp = session_http.get(
            f"https://api.spoonacular.com/recipes/{recipe_id}/analyzedInstructions",
            params={"apiKey": api_key},
            timeout=REQUEST_TIMEOUT
        )

        instructions = []
        if instructions_resp.status_code == 200:
            try:
                instructions_data = instructions_resp.json()
            except ValueError:
                instructions_data = []
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
    app.run(debug=False)
