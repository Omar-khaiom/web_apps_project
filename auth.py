# auth.py
import json
from werkzeug.security import generate_password_hash, check_password_hash

USERS_DB = "users.db"

def load_users():
    try:
        with open(USERS_DB, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_DB, "w") as f:
        json.dump(users, f)

def register_user(username, password):
    
    users = load_users()
    if username in users:
        return False  # user exists
    users[username] = generate_password_hash(password)
    save_users(users)
    return True



def verify_user(username, password):
    users = load_users()
    if username not in users:
        return False
    return check_password_hash(users[username], password)
