from flask import Blueprint, request, jsonify, session
from ..db import get_db
from .utils import hash_password, check_password, login_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE email = :1', [email])
    if cursor.fetchone():
        return jsonify({'error': 'Email already registered'}), 409
    pw_hash = hash_password(password)
    cursor.execute(
        'INSERT INTO users (email, password_hash) VALUES (:1, :2)',
        [email, pw_hash]
    )
    cursor.execute('SELECT users_seq.CURRVAL FROM dual')
    user_id = cursor.fetchone()[0]
    cursor.execute('INSERT INTO profiles (user_id) VALUES (:1)', [user_id])
    db.commit()
    return jsonify({'message': 'Registered', 'user_id': user_id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, password_hash, role FROM users WHERE email = :1', [email])
    row = cursor.fetchone()
    if not row or not check_password(password, row[1]):
        return jsonify({'error': 'Invalid credentials'}), 401
    login_user(row[0], row[2])
    return jsonify({'message': 'Logged in', 'user_id': row[0], 'role': row[2]})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})
