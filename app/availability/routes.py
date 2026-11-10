from flask import Blueprint, request, jsonify
from ..db import get_db
from ..auth.utils import require_login, current_user_id

availability_bp = Blueprint('availability', __name__, url_prefix='/api/availability')

@availability_bp.route('', methods=['GET'])
@require_login
def get_slots():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, day_of_week, start_time, end_time FROM availability_slots WHERE user_id=:1 ORDER BY day_of_week, start_time',
                [current_user_id()])
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    slots = [{'id': r[0], 'day': days[r[1]], 'day_index': r[1], 'start': r[2], 'end': r[3]} for r in cur.fetchall()]
    return jsonify({'slots': slots})

@availability_bp.route('', methods=['POST'])
@require_login
def add_slot():
    data = request.get_json()
    day = data.get('day_of_week')
    start = data.get('start_time')
    end = data.get('end_time')
    if day is None or not start or not end:
        return jsonify({'error': 'day_of_week, start_time, end_time required'}), 400
    if start >= end:
        return jsonify({'error': 'start_time must be before end_time'}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO availability_slots (user_id, day_of_week, start_time, end_time) VALUES (:1,:2,:3,:4)',
                [current_user_id(), day, start, end])
    cur.execute('SELECT availability_seq.CURRVAL FROM dual')
    slot_id = cur.fetchone()[0]
    db.commit()
    return jsonify({'message': 'Slot added', 'id': slot_id}), 201

@availability_bp.route('/<int:slot_id>', methods=['DELETE'])
@require_login
def delete_slot(slot_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM availability_slots WHERE id=:1 AND user_id=:2', [slot_id, current_user_id()])
    db.commit()
    return jsonify({'message': 'Slot removed'})
