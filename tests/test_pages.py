"""The HTML pages: login redirects, navigation, admin link, static files."""
import re

import pytest

from app.db import get_db
from tests.conftest import login, register, register_and_login

PAGES = {
    '/dashboard': 'Dashboard',
    '/profile': 'Profile',
    '/matches': 'Find partners',
    '/groups': 'Groups',
    '/chat': 'Messages',
}


def make_admin(app, user_id):
    with app.app_context():
        db = get_db()
        db.cursor().execute("UPDATE users SET role = 'admin' WHERE id = :1", [user_id])
        db.commit()


def test_login_page_has_no_menu(client):
    html = client.get('/').get_data(as_text=True)
    assert 'id="login-form"' in html
    assert 'site-nav' not in html


@pytest.mark.parametrize('path', [*PAGES, '/admin'])
def test_pages_redirect_when_logged_out(client, path):
    resp = client.get(path, follow_redirects=True)
    assert resp.request.path == '/'          # ends up on the login page
    assert 'id="login-form"' in resp.get_data(as_text=True)


def test_login_page_redirects_to_dashboard_when_logged_in(client):
    register_and_login(client)
    resp = client.get('/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/dashboard')


@pytest.mark.parametrize('path,label', PAGES.items())
def test_page_loads_and_highlights_its_menu_item(client, path, label):
    register_and_login(client)
    resp = client.get(path)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert re.search(rf'href="{path}"\s+aria-current="page">{label}</a>', html)
    assert html.count('aria-current="page"') == 1
    assert 'data-logout' in html


def test_student_has_no_admin_link_or_page(client):
    register_and_login(client)
    assert 'href="/admin"' not in client.get('/dashboard').get_data(as_text=True)
    resp = client.get('/admin')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/dashboard')


def test_admin_sees_admin_link_and_page(app, client):
    email, user_id = register(client)
    make_admin(app, user_id)
    login(client, email)           # role is stored in the session at login
    assert 'href="/admin"' in client.get('/dashboard').get_data(as_text=True)
    assert client.get('/admin').status_code == 200


@pytest.mark.parametrize('path', ['/', *PAGES])
def test_light_by_default_with_dark_mode_button(client, path):
    if path != '/':
        register_and_login(client)
    html = client.get(path).get_data(as_text=True)
    assert 'data-theme="dark"' not in html          # pages start light; only the button turns dark on
    assert re.search(r'<button[^>]*aria-pressed="false"[^>]*data-theme-toggle', html)
    # theme.js must load in <head> without defer, so a saved dark theme applies before drawing
    head = html.split('</head>')[0]
    assert re.search(r'<script src="[^"]*theme\.js"></script>', head)


@pytest.mark.parametrize('path', ['/', *PAGES])
def test_every_linked_static_file_exists(client, path):
    if path != '/':
        register_and_login(client)
    html = client.get(path).get_data(as_text=True)
    assets = re.findall(r'(?:href|src)="(/static/[^"]+)"', html)
    assert any(a.endswith('main.css') for a in assets)
    assert any(a.endswith('main.js') for a in assets)
    assert any(a.endswith('theme.js') for a in assets)
    for asset in assets:
        resp = client.get(asset)
        assert resp.status_code == 200, asset
        resp.close()
