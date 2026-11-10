from flask import Blueprint, request, jsonify
from ..db import get_db
from ..auth.utils import require_login, current_user_id

groups_bp = Blueprint('groups', __name__, url_prefix='/api/groups')

@groups_bp.route('', methods=['GET'])
@require_login
def list_groups():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        SELECT g.id, g.name, g.description, g.created_at
        FROM groups g JOIN group_members gm ON gm.group_id = g.id
        WHERE gm.user_id = :1
        ORDER BY g.created_at DESC
    ''', [current_user_id()])
    groups = [{'id': r[0], 'name': r[1], 'description': r[2]} for r in cur.fetchall()]
    return jsonify({'groups': groups})

@groups_bp.route('', methods=['POST'])
@require_login
def create_group():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '')
    if not name:
        return jsonify({'error': 'Group name required'}), 400
    db = get_db()
    cur = db.cursor()
    uid = current_user_id()
    cur.execute('INSERT INTO groups (name, description, created_by) VALUES (:1,:2,:3)',
                [name, description, uid])
    cur.execute('SELECT groups_seq.CURRVAL FROM dual')
    group_id = cur.fetchone()[0]
    cur.execute("INSERT INTO group_members (group_id, user_id, member_role) VALUES (:1,:2,'owner')",
                [group_id, uid])
    db.commit()
    return jsonify({'message': 'Group created', 'group_id': group_id}), 201

@groups_bp.route('/discover', methods=['GET'])
@require_login
def discover():
    """Groups the current user has NOT joined, with a summary of each."""
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        SELECT g.id, g.name, g.description, NVL(p.display_name, u.email),
               (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id)
        FROM groups g
        JOIN users u ON u.id = g.created_by
        LEFT JOIN profiles p ON p.user_id = g.created_by
        WHERE g.id NOT IN (SELECT group_id FROM group_members WHERE user_id = :me)
        ORDER BY g.created_at DESC
    ''', {'me': current_user_id()})
    rows = cur.fetchall()

    # subjects studied by the members of each group = what kind of group it is
    cur.execute('''
        SELECT DISTINCT gm.group_id, s.name
        FROM group_members gm
        JOIN user_subjects us ON us.user_id = gm.user_id
        JOIN subjects s ON s.id = us.subject_id
        ORDER BY s.name
    ''')
    subjects = {}
    for gid, name in cur.fetchall():
        subjects.setdefault(gid, []).append(name)

    cur.execute('''
        SELECT group_id, MIN(start_datetime) FROM study_sessions
        WHERE start_datetime > LOCALTIMESTAMP GROUP BY group_id
    ''')
    next_session = {gid: ts.strftime('%Y-%m-%d %H:%M') for gid, ts in cur.fetchall()}

    groups = [{
        'id': r[0], 'name': r[1], 'description': r[2], 'creator': r[3],
        'member_count': r[4], 'subjects': subjects.get(r[0], [])[:6],
        'next_session': next_session.get(r[0])
    } for r in rows]
    return jsonify({'groups': groups})


@groups_bp.route('/<int:group_id>/join', methods=['POST'])
@require_login
def join_group(group_id):
    db = get_db()
    cur = db.cursor()
    uid = current_user_id()
    cur.execute('SELECT id FROM groups WHERE id = :1', [group_id])
    if not cur.fetchone():
        return jsonify({'error': 'Group not found'}), 404
    cur.execute('SELECT 1 FROM group_members WHERE group_id = :1 AND user_id = :2', [group_id, uid])
    if cur.fetchone():
        return jsonify({'error': 'Already a member'}), 409
    cur.execute("INSERT INTO group_members (group_id, user_id, member_role) VALUES (:1,:2,'member')",
                [group_id, uid])
    db.commit()
    return jsonify({'message': 'Joined group', 'group_id': group_id}), 201


@groups_bp.route('/<int:group_id>', methods=['GET'])
@require_login
def get_group(group_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, name, description FROM groups WHERE id=:1', [group_id])
    g = cur.fetchone()
    if not g:
        return jsonify({'error': 'Not found'}), 404
    cur.execute('''
        SELECT u.id, NVL(p.display_name, u.email), gm.member_role
        FROM group_members gm
        JOIN users u ON u.id = gm.user_id
        LEFT JOIN profiles p ON p.user_id = gm.user_id
        WHERE gm.group_id = :1
    ''', [group_id])
    members = [{'user_id': r[0], 'name': r[1], 'role': r[2]} for r in cur.fetchall()]
    cur.execute('''
        SELECT id, start_datetime, end_datetime, location_or_link
        FROM study_sessions WHERE group_id=:1 ORDER BY start_datetime
    ''', [group_id])
    sessions = [{'id': r[0], 'start': str(r[1]), 'end': str(r[2]), 'location': r[3]} for r in cur.fetchall()]
    return jsonify({'id': g[0], 'name': g[1], 'description': g[2], 'members': members, 'sessions': sessions})

@groups_bp.route('/<int:group_id>/invite', methods=['POST'])
@require_login
def invite(group_id):
    from ..chat.routes import are_partners, is_member
    data = request.get_json(silent=True) or {}
    to_id = data.get('user_id')
    if not to_id:
        return jsonify({'error': 'user_id required'}), 400
    db = get_db()
    cur = db.cursor()
    me = current_user_id()
    if not is_member(cur, group_id, me):
        return jsonify({'error': 'Only group members can invite'}), 403
    if not are_partners(cur, me, to_id):
        return jsonify({'error': 'You can only invite accepted partners'}), 403
    if is_member(cur, group_id, to_id):
        return jsonify({'error': 'Already a member'}), 409
    cur.execute("INSERT INTO group_members (group_id, user_id, member_role) VALUES (:1,:2,'member')",
                [group_id, to_id])
    db.commit()
    return jsonify({'message': 'User added to group'}), 201

@groups_bp.route('/<int:group_id>/sessions', methods=['POST'])
@require_login
def add_session(group_id):
    data = request.get_json()
    start = data.get('start_datetime')
    end = data.get('end_datetime')
    location = data.get('location_or_link', '')
    if not start or not end:
        return jsonify({'error': 'start_datetime and end_datetime required'}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        INSERT INTO study_sessions (group_id, start_datetime, end_datetime, location_or_link)
        VALUES (:1, TO_TIMESTAMP(:2,'YYYY-MM-DD HH24:MI'), TO_TIMESTAMP(:3,'YYYY-MM-DD HH24:MI'), :4)
    ''', [group_id, start, end, location])
    db.commit()
    return jsonify({'message': 'Session scheduled'}), 201

@groups_bp.route('/<int:group_id>/leave', methods=['POST'])
@require_login
def leave_group(group_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM group_members WHERE group_id=:1 AND user_id=:2',
                [group_id, current_user_id()])
    db.commit()
    return jsonify({'message': 'Left group'})
