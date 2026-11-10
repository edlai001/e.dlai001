from flask import Blueprint, request, jsonify
from ..db import get_db
from ..auth.utils import require_login, current_user_id

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

MAX_LEN = 1000


def are_partners(cur, a, b):
    """True if a and b have an accepted match request (either direction)."""
    cur.execute('''
        SELECT 1 FROM match_requests
        WHERE status = 'accepted'
          AND ((from_user_id = :a AND to_user_id = :b)
            OR (from_user_id = :b AND to_user_id = :a))
    ''', {'a': a, 'b': b})
    return cur.fetchone() is not None


def is_member(cur, group_id, user_id):
    cur.execute('SELECT 1 FROM group_members WHERE group_id = :g AND user_id = :u',
                {'g': group_id, 'u': user_id})
    return cur.fetchone() is not None


def fmt(ts):
    return ts.strftime('%Y-%m-%d %H:%M') if ts else ''


def clean_body():
    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return None, (jsonify({'error': 'Message is empty'}), 400)
    if len(body) > MAX_LEN:
        return None, (jsonify({'error': f'Message too long (max {MAX_LEN})'}), 400)
    return body, None


# ---------- partners ----------

@chat_bp.route('/partners', methods=['GET'])
@require_login
def partners():
    cur = get_db().cursor()
    cur.execute('''
        SELECT u.id, NVL(p.display_name, u.email)
        FROM users u LEFT JOIN profiles p ON p.user_id = u.id
        WHERE u.id IN (
            SELECT to_user_id FROM match_requests WHERE from_user_id = :me AND status = 'accepted'
            UNION
            SELECT from_user_id FROM match_requests WHERE to_user_id = :me AND status = 'accepted')
        ORDER BY 2
    ''', {'me': current_user_id()})
    return jsonify({'partners': [{'user_id': r[0], 'name': r[1]} for r in cur.fetchall()]})


# ---------- direct messages ----------

@chat_bp.route('/messages/direct/<int:other_id>', methods=['GET'])
@require_login
def get_direct(other_id):
    me = current_user_id()
    cur = get_db().cursor()
    if not are_partners(cur, me, other_id):
        return jsonify({'error': 'You can only chat with accepted partners'}), 403
    cur.execute('''
        SELECT id, from_user_id, body, sent_at FROM (
            SELECT id, from_user_id, body, sent_at FROM direct_messages
            WHERE (from_user_id = :me AND to_user_id = :o) OR (from_user_id = :o AND to_user_id = :me)
            ORDER BY id DESC FETCH FIRST 200 ROWS ONLY)
        ORDER BY id
    ''', {'me': me, 'o': other_id})
    msgs = [{'id': r[0], 'mine': r[1] == me, 'body': r[2], 'sent_at': fmt(r[3])} for r in cur.fetchall()]
    return jsonify({'messages': msgs})


@chat_bp.route('/messages/direct/<int:other_id>', methods=['POST'])
@require_login
def send_direct(other_id):
    me = current_user_id()
    db = get_db()
    cur = db.cursor()
    if not are_partners(cur, me, other_id):
        return jsonify({'error': 'You can only chat with accepted partners'}), 403
    body, err = clean_body()
    if err:
        return err
    cur.execute('INSERT INTO direct_messages (from_user_id, to_user_id, body) VALUES (:1, :2, :3)',
                [me, other_id, body])
    db.commit()
    return jsonify({'message': 'Sent'}), 201


# ---------- group messages ----------

@chat_bp.route('/groups/<int:group_id>/messages', methods=['GET'])
@require_login
def get_group_messages(group_id):
    me = current_user_id()
    cur = get_db().cursor()
    if not is_member(cur, group_id, me):
        return jsonify({'error': 'Not a member of this group'}), 403
    cur.execute('''
        SELECT id, sender_id, name, body, sent_at FROM (
            SELECT m.id, m.sender_id, NVL(p.display_name, u.email) AS name, m.body, m.sent_at
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            LEFT JOIN profiles p ON p.user_id = m.sender_id
            WHERE m.group_id = :g
            ORDER BY m.id DESC FETCH FIRST 200 ROWS ONLY)
        ORDER BY id
    ''', {'g': group_id})
    msgs = [{'id': r[0], 'mine': r[1] == me, 'sender': r[2], 'body': r[3], 'sent_at': fmt(r[4])}
            for r in cur.fetchall()]
    return jsonify({'messages': msgs})


@chat_bp.route('/groups/<int:group_id>/messages', methods=['POST'])
@require_login
def send_group_message(group_id):
    me = current_user_id()
    db = get_db()
    cur = db.cursor()
    if not is_member(cur, group_id, me):
        return jsonify({'error': 'Not a member of this group'}), 403
    body, err = clean_body()
    if err:
        return err
    cur.execute('INSERT INTO messages (group_id, sender_id, body) VALUES (:1, :2, :3)',
                [group_id, me, body])
    db.commit()
    return jsonify({'message': 'Sent'}), 201


# ---------- group invites (partners not yet in the group) ----------

@chat_bp.route('/groups/<int:group_id>/invitable', methods=['GET'])
@require_login
def invitable(group_id):
    me = current_user_id()
    cur = get_db().cursor()
    if not is_member(cur, group_id, me):
        return jsonify({'error': 'Not a member of this group'}), 403
    cur.execute('''
        SELECT u.id, NVL(p.display_name, u.email)
        FROM users u LEFT JOIN profiles p ON p.user_id = u.id
        WHERE u.id IN (
            SELECT to_user_id FROM match_requests WHERE from_user_id = :me AND status = 'accepted'
            UNION
            SELECT from_user_id FROM match_requests WHERE to_user_id = :me AND status = 'accepted')
          AND u.id NOT IN (SELECT user_id FROM group_members WHERE group_id = :g)
        ORDER BY 2
    ''', {'me': me, 'g': group_id})
    return jsonify({'partners': [{'user_id': r[0], 'name': r[1]} for r in cur.fetchall()]})
