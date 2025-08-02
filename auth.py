import json
from werkzeug.security import generate_password_hash, check_password_hash

USERS_DB = "users.db"

def load_users():
    try:
        with open(USERS_DB, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_DB, "w") as f:
        json.dump(users, f)

def register_user(username, password, email):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": generate_password_hash(password),
        "email": email
    }
    save_users(users)
    return True

def verify_user(username, password):
    users = load_users()
    user = users.get(username)
    if not user:
        return False
    return check_password_hash(user["password"], password)

def username_exists(username):
    return username in load_users()

def email_exists_in_db(email):
    users = load_users()
    return any(user["email"] == email for user in users.values())

def get_user_email(username):
    users = load_users()
    user = users.get(username)
    if user:
        return user.get("email")
    return None