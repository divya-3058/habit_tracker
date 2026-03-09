from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path  = os.path.join(base_dir, '..', 'habitcarnival.db')

    app.config['SECRET_KEY']                  = os.environ.get('SECRET_KEY', 'hc-ultra-secret-xp-key-2025!')
    app.config['SQLALCHEMY_DATABASE_URI']      = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view         = 'auth.login'
    login_manager.login_message      = '🎪 Please login to enter the carnival!'
    login_manager.login_message_category = 'info'

    from app.auth    import auth_bp
    from app.habit   import habit_bp
    from app.carnival import carnival_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(habit_bp)
    app.register_blueprint(carnival_bp)

    with app.app_context():
        db.create_all()

    return app
