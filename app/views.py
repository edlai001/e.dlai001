from flask import Blueprint, render_template, session, redirect, url_for

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('views.dashboard'))
    return render_template('index.html')

@views_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('views.index'))
    return render_template('dashboard.html')

@views_bp.route('/profile')
def profile():
    if not session.get('user_id'):
        return redirect(url_for('views.index'))
    return render_template('profile.html')

@views_bp.route('/matches')
def matches():
    if not session.get('user_id'):
        return redirect(url_for('views.index'))
    return render_template('matches.html')

@views_bp.route('/groups')
def groups():
    if not session.get('user_id'):
        return redirect(url_for('views.index'))
    return render_template('groups.html')

@views_bp.route('/chat')
def chat():
    if not session.get('user_id'):
        return redirect(url_for('views.index'))
    return render_template('chat.html')

@views_bp.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('views.dashboard'))
    return render_template('admin.html')
