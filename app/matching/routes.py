from flask import Blueprint, request, jsonify
from ..db import get_db
from ..auth.utils import require_login, current_user_id
from .algorithm import get_matches

matching_bp = Blueprint('matching', __name__, url_prefix='/api/matches')

@matching_bp.route('', methods=['GET'])
@require_login
def matches():
    results = get_matches(current_user_id())
    return jsonify({'matches': results})

@matching_bp.route('/request', methods=['POST'])
@require_login
def send_request():
    data = request.get_json()
    to_id = data.get('to_user_id')
    if not to_id:
        return jsonify({'error': 'to_user_id required'}), 400
    db = get_db()
    cur = db.cursor()
    from_id = current_user_id()
    cur.execute('SELECT id FROM match_requests WHERE from_user_id=:1 AND to_user_id=:2', [from_id, to_id])
    if cur.fetchone():
        return jsonify({'error': 'Request already sent'}), 409
    cur.execute('INSERT INTO match_requests (from_user_id, to_user_id) VALUES (:1,:2)', [from_id, to_id])
    db.commit()
    return jsonify({'message': 'Request sent'}), 201

@matching_bp.route('/request/<int:req_id>', methods=['PUT'])
@require_login
def respond_request(req_id):
    data = request.get_json()
    status = data.get('status')
    if status not in ('accepted', 'declined'):
        return jsonify({'error': 'status must be accepted or declined'}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE match_requests SET status=:1 WHERE id=:2 AND to_user_id=:3',
                [status, req_id, current_user_id()])
    db.commit()
    return jsonify({'message': f'Request {status}'})

@matching_bp.route('/requests/incoming', methods=['GET'])
@require_login
def incoming():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        SELECT mr.id, mr.from_user_id, NVL(p.display_name, u.email), mr.status, mr.created_at
        FROM match_requests mr
        JOIN users u ON u.id = mr.from_user_id
        LEFT JOIN profiles p ON p.user_id = mr.from_user_id
        WHERE mr.to_user_id=:1 AND mr.status='pending'
    ''', [current_user_id()])
    rows = cur.fetchall()
    return jsonify({'requests': [{'id': r[0], 'from_user_id': r[1], 'from_name': r[2], 'status': r[3]} for r in rows]})
