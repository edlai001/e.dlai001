from flask import Flask
from .db import init_db, close_db
from .auth.routes import auth_bp
from .profile.routes import profile_bp
from .availability.routes import availability_bp
from .matching.routes import matching_bp
from .groups.routes import groups_bp
from .admin.routes import admin_bp
from .chat.routes import chat_bp
from .views import views_bp

def create_app(config_object='config.DevelopmentConfig'):
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    app.config.from_object(config_object)
    init_db(app)
    app.teardown_appcontext(close_db)
    for bp in [views_bp, auth_bp, profile_bp, availability_bp, matching_bp, groups_bp, admin_bp, chat_bp]:
        app.register_blueprint(bp)
    return app
