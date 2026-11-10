from ..db import get_db

W_SUBJECT = 0.6
W_AVAIL   = 0.4

def slots_overlap(s1, e1, s2, e2):
    return s1 < e2 and s2 < e1

def get_matches(user_id, limit=20):
    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT subject_id FROM user_subjects WHERE user_id=:1', [user_id])
    my_subjects = set(r[0] for r in cur.fetchall())
    if not my_subjects:
        return []

    placeholders = ','.join([f':{i+1}' for i in range(len(my_subjects))])
    bind = list(my_subjects) + [user_id]
    cur.execute(f'''
        SELECT DISTINCT us.user_id, NVL(p.display_name, u.email) as display_name
        FROM user_subjects us
        JOIN users u ON u.id = us.user_id
        LEFT JOIN profiles p ON p.user_id = us.user_id
        WHERE us.subject_id IN ({placeholders}) AND us.user_id != :{len(bind)}
    ''', bind)
    candidates = cur.fetchall()
    if not candidates:
        return []

    cur.execute('SELECT day_of_week, start_time, end_time FROM availability_slots WHERE user_id=:1', [user_id])
    my_slots = cur.fetchall()

    scores = []
    for (cid, display_name) in candidates:
        cur.execute('SELECT subject_id FROM user_subjects WHERE user_id=:1', [cid])
        their_subjects = set(r[0] for r in cur.fetchall())
        inter = len(my_subjects & their_subjects)
        union = len(my_subjects | their_subjects)
        subject_score = inter / union if union else 0

        cur.execute('SELECT day_of_week, start_time, end_time FROM availability_slots WHERE user_id=:1', [cid])
        their_slots = cur.fetchall()
        overlap = sum(
            1 for ms in my_slots for ts in their_slots
            if ms[0] == ts[0] and slots_overlap(ms[1], ms[2], ts[1], ts[2])
        )
        avail_score = overlap / len(my_slots) if my_slots else 0

        # Shared subject names
        cur.execute(f'''
            SELECT s.name FROM subjects s
            JOIN user_subjects us ON us.subject_id = s.id
            WHERE us.user_id = :1 AND us.subject_id IN ({placeholders})
        ''', [cid] + list(my_subjects))
        shared = [r[0] for r in cur.fetchall()]

        total = W_SUBJECT * subject_score + W_AVAIL * avail_score
        scores.append({
            'user_id': cid,
            'display_name': display_name,
            'score': round(total, 3),
            'subject_score': round(subject_score, 3),
            'availability_score': round(avail_score, 3),
            'shared_subjects': shared
        })

    scores.sort(key=lambda x: x['score'], reverse=True)
    return scores[:limit]
