from routes.main import main_bp
from routes.auth import auth_bp

def init_app(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

