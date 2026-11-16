import pytest

from tests.conftest import register_and_login


def setup_student(client, name, subjects, slots=()):
    user_id = register_and_login(client)
    client.put('/api/profile', json={'display_name': name})
    for s in subjects:
        assert client.post('/api/profile/subjects', json={'subject_name': s}).status_code == 201
    for day, start, end in slots:
        resp = client.post('/api/availability',
                           json={'day_of_week': day, 'start_time': start, 'end_time': end})
        assert resp.status_code == 201
    return user_id


@pytest.fixture
def three_students(make_client):
    """Anna and Bat share subjects and a time slot; Cara shares nothing with Anna."""
    anna, bat, cara = make_client(), make_client(), make_client()
    ids = {
        'anna': setup_student(anna, 'Anna', ['Databases', 'Algorithms'], [(0, '09:00', '11:00')]),
        'bat': setup_student(bat, 'Bat', ['Databases', 'Algorithms'], [(0, '10:00', '12:00')]),
        'cara': setup_student(cara, 'Cara', ['Statistics']),
    }
    return {'anna': anna, 'bat': bat, 'cara': cara}, ids


def test_matches_require_login(client):
    assert client.get('/api/matches').status_code == 401


def test_no_subjects_means_no_matches(client):
    register_and_login(client)
    assert client.get('/api/matches').get_json()['matches'] == []


def test_matching_scores_shared_subjects_and_overlapping_time(three_students):
    clients, ids = three_students
    matches = clients['anna'].get('/api/matches').get_json()['matches']

    assert len(matches) == 1                       # Cara shares nothing, Anna never matches herself
    m = matches[0]
    assert m['user_id'] == ids['bat']
    assert m['display_name'] == 'Bat'
    assert m['subject_score'] == 1.0               # same 2 subjects
    assert m['availability_score'] == 1.0          # Monday 09-11 overlaps 10-12
    assert m['score'] == 1.0                       # 0.6 * 1 + 0.4 * 1
    assert sorted(m['shared_subjects']) == ['Algorithms', 'Databases']


def test_partial_subject_overlap_and_no_time_overlap(make_client):
    a, b = make_client(), make_client()
    setup_student(a, 'A', ['Databases', 'Statistics'], [(1, '09:00', '10:00')])
    b_id = setup_student(b, 'B', ['Databases'], [(1, '10:00', '11:00')])   # touching, not overlapping

    m = a.get('/api/matches').get_json()['matches'][0]
    assert m['user_id'] == b_id
    assert m['subject_score'] == 0.5               # 1 shared / 2 total
    assert m['availability_score'] == 0.0
    assert m['score'] == 0.3                       # 0.6 * 0.5


def test_match_request_accept_flow(three_students):
    clients, ids = three_students
    anna, bat = clients['anna'], clients['bat']

    assert anna.post('/api/matches/request', json={'to_user_id': ids['bat']}).status_code == 201
    assert anna.post('/api/matches/request', json={'to_user_id': ids['bat']}).status_code == 409

    incoming = bat.get('/api/matches/requests/incoming').get_json()['requests']
    assert len(incoming) == 1
    assert incoming[0]['from_user_id'] == ids['anna']
    assert incoming[0]['from_name'] == 'Anna'
    assert incoming[0]['status'] == 'pending'

    req_id = incoming[0]['id']
    assert bat.put(f'/api/matches/request/{req_id}', json={'status': 'accepted'}).status_code == 200
    assert bat.get('/api/matches/requests/incoming').get_json()['requests'] == []

    # Both now see each other as partners
    assert [p['user_id'] for p in anna.get('/api/partners').get_json()['partners']] == [ids['bat']]
    assert [p['user_id'] for p in bat.get('/api/partners').get_json()['partners']] == [ids['anna']]


def test_match_request_requires_target(client):
    register_and_login(client)
    assert client.post('/api/matches/request', json={}).status_code == 400


def test_match_request_to_unknown_user_is_rejected(client):
    register_and_login(client)
    assert client.post('/api/matches/request', json={'to_user_id': 999999}).status_code == 404


def test_match_request_to_yourself_is_rejected(client):
    me = register_and_login(client)
    assert client.post('/api/matches/request', json={'to_user_id': me}).status_code == 400


def test_respond_with_invalid_status_is_rejected(three_students):
    clients, ids = three_students
    clients['anna'].post('/api/matches/request', json={'to_user_id': ids['bat']})
    req_id = clients['bat'].get('/api/matches/requests/incoming').get_json()['requests'][0]['id']
    resp = clients['bat'].put(f'/api/matches/request/{req_id}', json={'status': 'maybe'})
    assert resp.status_code == 400


def test_only_the_receiver_can_answer_a_request(three_students):
    clients, ids = three_students
    clients['anna'].post('/api/matches/request', json={'to_user_id': ids['bat']})
    req_id = clients['bat'].get('/api/matches/requests/incoming').get_json()['requests'][0]['id']

    resp = clients['cara'].put(f'/api/matches/request/{req_id}', json={'status': 'accepted'})
    assert resp.status_code == 404
    # Still pending for Bat
    assert len(clients['bat'].get('/api/matches/requests/incoming').get_json()['requests']) == 1
