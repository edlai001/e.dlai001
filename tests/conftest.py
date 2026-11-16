"""Shared test setup.

Every test runs against the studybuddy_test database user (config.TestingConfig)
and starts with empty tables, apart from the 12 seed subjects from schema.sql.
"""
import itertools

import pytest

from app import create_app
from app.db import get_db

TEST_DB_USER = 'STUDYBUDDY_TEST'

SEED_SUBJECTS = [
    'Mathematics', 'Algorithms', 'Databases', 'Data Structures',
    'Operating Systems', 'Computer Networks', 'Python Programming',
    'Java Programming', 'Web Development', 'Machine Learning',
    'Linear Algebra', 'Statistics',
]

# Children before parents, so foreign keys never block a delete.
TABLES_TO_EMPTY = [
    'direct_messages', 'messages', 'ratings', 'study_sessions',
    'group_members', 'groups', 'match_requests', 'availability_slots',
    'user_subjects', 'profiles', 'users',
]

PASSWORD = 'secret123'
_email_counter = itertools.count(1)


@pytest.fixture(scope='session')
def app():
    app = create_app('config.TestingConfig')
    # Safety net: never empty tables unless we really are the test user.
    with app.app_context():
        cur = get_db().cursor()
        cur.execute('SELECT user FROM dual')
        actual = cur.fetchone()[0]
    if actual != TEST_DB_USER:
        pytest.exit(f'Refusing to run: connected as {actual}, expected {TEST_DB_USER}')
    return app


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        for table in TABLES_TO_EMPTY:
            cur.execute(f'DELETE FROM {table}')
        binds = ','.join(f':{i + 1}' for i in range(len(SEED_SUBJECTS)))
        cur.execute(f'DELETE FROM subjects WHERE name NOT IN ({binds})', SEED_SUBJECTS)
        db.commit()
    yield


@pytest.fixture
def client(app):
    """A browser with its own login cookie."""
    return app.test_client()


@pytest.fixture
def make_client(app):
    """Create extra browsers when a test needs several logged-in users."""
    return app.test_client


def register(client, email=None, password=PASSWORD):
    email = email or f'student{next(_email_counter)}@test.local'
    resp = client.post('/api/auth/register', json={'email': email, 'password': password})
    assert resp.status_code == 201, resp.get_json()
    return email, resp.get_json()['user_id']


def login(client, email, password=PASSWORD):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def register_and_login(client, email=None):
    """Register a new student, log them in, and return their user id."""
    email, user_id = register(client, email)
    resp = login(client, email)
    assert resp.status_code == 200, resp.get_json()
    return user_id
