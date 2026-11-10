from flask import Blueprint, request, jsonify
from ..db import get_db
from ..auth.utils import require_login, current_user_id

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@profile_bp.route('', methods=['GET'])
@require_login
def get_profile():
    db = get_db()
    cur = db.cursor()
    uid = current_user_id()
    cur.execute('''
        SELECT p.display_name, p.major, p.bio, p.language, u.email
        FROM profiles p JOIN users u ON u.id = p.user_id
        WHERE p.user_id = :1
    ''', [uid])
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'Profile not found'}), 404
    cur.execute('''
        SELECT us.id, s.name, us.skill_level, us.study_goal
        FROM user_subjects us JOIN subjects s ON s.id = us.subject_id
        WHERE us.user_id = :1
    ''', [uid])
    subjects = [{'id': r[0], 'name': r[1], 'level': r[2], 'goal': r[3]} for r in cur.fetchall()]
    return jsonify({
        'user_id': uid,
        'email': row[4],
        'display_name': row[0],
        'major': row[1],
        'bio': row[2],
        'language': row[3],
        'subjects': subjects
    })

@profile_bp.route('', methods=['PUT'])
@require_login
def update_profile():
    data = request.get_json()
    db = get_db()
    cur = db.cursor()
    uid = current_user_id()
    cur.execute('''
        UPDATE profiles SET display_name=:1, major=:2, bio=:3, language=:4
        WHERE user_id=:5
    ''', [data.get('display_name'), data.get('major'), data.get('bio'), data.get('language', 'English'), uid])
    db.commit()
    return jsonify({'message': 'Profile updated'})

@profile_bp.route('/subjects', methods=['POST'])
@require_login
def add_subject():
    data = request.get_json()
    subject_name = data.get('subject_name', '').strip()
    level = data.get('level', 'beginner')
    goal = data.get('goal', 'general')
    if not subject_name:
        return jsonify({'error': 'Subject name required'}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id FROM subjects WHERE LOWER(name) = LOWER(:1)', [subject_name])
    row = cur.fetchone()
    if row:
        subject_id = row[0]
    else:
        cur.execute('INSERT INTO subjects (name) VALUES (:1)', [subject_name])
        cur.execute('SELECT subjects_seq.CURRVAL FROM dual')
        subject_id = cur.fetchone()[0]
    uid = current_user_id()
    cur.execute('SELECT id FROM user_subjects WHERE user_id=:1 AND subject_id=:2', [uid, subject_id])
    if cur.fetchone():
        return jsonify({'error': 'Subject already added'}), 409
    cur.execute('INSERT INTO user_subjects (user_id, subject_id, skill_level, study_goal) VALUES (:1,:2,:3,:4)',
                [uid, subject_id, level, goal])
    db.commit()
    return jsonify({'message': 'Subject added', 'subject_id': subject_id}), 201

@profile_bp.route('/subjects/<int:us_id>', methods=['DELETE'])
@require_login
def remove_subject(us_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM user_subjects WHERE id=:1 AND user_id=:2', [us_id, current_user_id()])
    db.commit()
    return jsonify({'message': 'Subject removed'})

@profile_bp.route('/subjects', methods=['GET'])
def list_subjects():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, name FROM subjects ORDER BY name')
    return jsonify({'subjects': [{'id': r[0], 'name': r[1]} for r in cur.fetchall()]})
