from tests.conftest import SEED_SUBJECTS, register_and_login


def test_profile_requires_login(client):
    assert client.get('/api/profile').status_code == 401
    assert client.put('/api/profile', json={'bio': 'x'}).status_code == 401


def test_update_profile_and_read_it_back(client):
    register_and_login(client)
    resp = client.put('/api/profile', json={
        'display_name': 'Anna K.', 'major': 'Computer Science',
        'bio': 'Likes graphs.', 'language': 'Mongolian',
    })
    assert resp.status_code == 200

    profile = client.get('/api/profile').get_json()
    assert profile['display_name'] == 'Anna K.'
    assert profile['major'] == 'Computer Science'
    assert profile['bio'] == 'Likes graphs.'
    assert profile['language'] == 'Mongolian'


def test_profile_fields_longer_than_database_allows_are_rejected(client):
    # schema.sql: display_name 100, major 100, bio 1000, language 50 characters
    register_and_login(client)
    for field, limit in [('display_name', 100), ('major', 100), ('bio', 1000), ('language', 50)]:
        resp = client.put('/api/profile', json={field: 'x' * (limit + 1)})
        assert resp.status_code == 400, field
        assert client.put('/api/profile', json={field: 'x' * limit}).status_code == 200, field


# ---------- subjects ----------

def test_list_subjects_shows_seed_subjects(client):
    names = [s['name'] for s in client.get('/api/profile/subjects').get_json()['subjects']]
    assert sorted(names) == sorted(SEED_SUBJECTS)


def test_add_existing_subject_ignores_case(client):
    register_and_login(client)
    all_subjects = client.get('/api/profile/subjects').get_json()['subjects']
    databases_id = next(s['id'] for s in all_subjects if s['name'] == 'Databases')

    resp = client.post('/api/profile/subjects',
                       json={'subject_name': 'databases', 'level': 'advanced', 'goal': 'exam'})
    assert resp.status_code == 201
    assert resp.get_json()['subject_id'] == databases_id

    mine = client.get('/api/profile').get_json()['subjects']
    assert mine == [{'id': mine[0]['id'], 'name': 'Databases', 'level': 'advanced', 'goal': 'exam'}]


def test_add_new_subject_creates_it(client):
    register_and_login(client)
    resp = client.post('/api/profile/subjects', json={'subject_name': 'Quantum Computing'})
    assert resp.status_code == 201
    names = [s['name'] for s in client.get('/api/profile/subjects').get_json()['subjects']]
    assert 'Quantum Computing' in names
    mine = client.get('/api/profile').get_json()['subjects']
    assert mine[0]['level'] == 'beginner' and mine[0]['goal'] == 'general'   # defaults


def test_add_same_subject_twice_is_rejected(client):
    register_and_login(client)
    assert client.post('/api/profile/subjects', json={'subject_name': 'Statistics'}).status_code == 201
    assert client.post('/api/profile/subjects', json={'subject_name': 'statistics'}).status_code == 409


def test_add_subject_requires_name(client):
    register_and_login(client)
    assert client.post('/api/profile/subjects', json={'subject_name': '  '}).status_code == 400


def test_subject_name_longer_than_database_allows_is_rejected(client):
    # schema.sql: subjects.name 100 characters
    register_and_login(client)
    assert client.post('/api/profile/subjects', json={'subject_name': 'x' * 101}).status_code == 400


def test_subject_level_and_goal_longer_than_database_allows_are_rejected(client):
    # schema.sql: skill_level 20, study_goal 50 characters
    register_and_login(client)
    resp = client.post('/api/profile/subjects', json={'subject_name': 'Statistics', 'level': 'x' * 21})
    assert resp.status_code == 400
    resp = client.post('/api/profile/subjects', json={'subject_name': 'Statistics', 'goal': 'x' * 51})
    assert resp.status_code == 400


def test_remove_subject(client):
    register_and_login(client)
    client.post('/api/profile/subjects', json={'subject_name': 'Algorithms'})
    us_id = client.get('/api/profile').get_json()['subjects'][0]['id']
    assert client.delete(f'/api/profile/subjects/{us_id}').status_code == 200
    assert client.get('/api/profile').get_json()['subjects'] == []


def test_cannot_remove_another_users_subject(client, make_client):
    register_and_login(client)
    client.post('/api/profile/subjects', json={'subject_name': 'Algorithms'})
    us_id = client.get('/api/profile').get_json()['subjects'][0]['id']

    other = make_client()
    register_and_login(other)
    other.delete(f'/api/profile/subjects/{us_id}')
    assert len(client.get('/api/profile').get_json()['subjects']) == 1
