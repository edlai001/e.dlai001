from tests.conftest import PASSWORD, login, register


def test_register_creates_user_and_empty_profile(client):
    resp = client.post('/api/auth/register',
                       json={'email': 'Anna@Test.local', 'password': PASSWORD})
    assert resp.status_code == 201
    assert isinstance(resp.get_json()['user_id'], int)

    # Email is stored lower-case, so logging in with lower case works.
    assert login(client, 'anna@test.local').status_code == 200
    profile = client.get('/api/profile').get_json()
    assert profile['email'] == 'anna@test.local'
    assert profile['language'] == 'English'      # schema default
    assert profile['subjects'] == []


def test_register_duplicate_email_is_rejected(client):
    register(client, 'dup@test.local')
    resp = client.post('/api/auth/register',
                       json={'email': 'DUP@test.local', 'password': 'other'})
    assert resp.status_code == 409


def test_register_requires_email_and_password(client):
    assert client.post('/api/auth/register', json={'email': 'x@test.local'}).status_code == 400
    assert client.post('/api/auth/register', json={'password': 'x'}).status_code == 400


def test_login_returns_user_id_and_student_role(client):
    email, user_id = register(client)
    resp = login(client, email)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['user_id'] == user_id
    assert body['role'] == 'student'               # schema default


def test_login_with_wrong_password_fails(client):
    email, _ = register(client)
    assert login(client, email, 'wrong-password').status_code == 401


def test_login_with_unknown_email_fails(client):
    assert login(client, 'nobody@test.local').status_code == 401


def test_logout_ends_session(client):
    email, _ = register(client)
    login(client, email)
    assert client.get('/api/profile').status_code == 200
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/profile').status_code == 401
