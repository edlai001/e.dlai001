import bcrypt
from functools import wraps
from flask import session, jsonify

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def login_user(user_id: int, role: str):
    session['user_id'] = user_id
    session['role'] = role

def current_user_id():
    return session.get('user_id')

def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user_id():
            return jsonify({'error': 'Unauthorised'}), 401
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return wrapper
