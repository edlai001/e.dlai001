from flask import Blueprint, request, jsonify
from ..db import get_db
from ..auth.utils import require_login, require_admin

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/stats', methods=['GET'])
@require_login
@require_admin
def stats():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    users = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM groups')
    groups = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM match_requests WHERE status='accepted'")
    matches = cur.fetchone()[0]
    return jsonify({'total_users': users, 'total_groups': groups, 'accepted_matches': matches})

@admin_bp.route('/subjects', methods=['GET'])
@require_login
@require_admin
def list_subjects():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, name FROM subjects ORDER BY name')
    return jsonify({'subjects': [{'id': r[0], 'name': r[1]} for r in cur.fetchall()]})

@admin_bp.route('/subjects', methods=['POST'])
@require_login
@require_admin
def add_subject():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO subjects (name) VALUES (:1)', [name])
    db.commit()
    return jsonify({'message': 'Subject added'}), 201

@admin_bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
@require_login
@require_admin
def delete_subject(subject_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM subjects WHERE id=:1', [subject_id])
    db.commit()
    return jsonify({'message': 'Subject deleted'})

@admin_bp.route('/users', methods=['GET'])
@require_login
@require_admin
def list_users():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        SELECT u.id, u.email, u.role, NVL(p.display_name,'-'), u.created_at
        FROM users u LEFT JOIN profiles p ON p.user_id = u.id
        ORDER BY u.created_at DESC
    ''')
    users = [{'id': r[0], 'email': r[1], 'role': r[2], 'display_name': r[3]} for r in cur.fetchall()]
    return jsonify({'users': users})
