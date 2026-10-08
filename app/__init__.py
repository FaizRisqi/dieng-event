from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app import models  # noqa: F401

    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.events import bp as events_bp
    app.register_blueprint(events_bp)
    from app.routes.communities import bp as communities_bp
    app.register_blueprint(communities_bp)

    return app