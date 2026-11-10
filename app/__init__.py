from flask import Flask, render_template
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

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("413.html"), 413

    from app import models  # noqa: F401

    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.events import bp as events_bp
    app.register_blueprint(events_bp)

    from app.routes.communities import bp as communities_bp
    app.register_blueprint(communities_bp)

    from app.routes.notes import bp as notes_bp
    app.register_blueprint(notes_bp)

    from app.routes.sesi import bp as sesi_bp
    app.register_blueprint(sesi_bp)

    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    from app.routes.tugas import bp as tugas_bp
    app.register_blueprint(tugas_bp)

    from app.routes.rekap import bp as rekap_bp
    app.register_blueprint(rekap_bp)

    from app.routes.profil import bp as profil_bp
    app.register_blueprint(profil_bp)

    return app
