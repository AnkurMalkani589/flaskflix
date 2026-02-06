from flask import Flask
from config import Config
from extensions import db, migrate, login_manager
from models import User, Movie
from urllib.parse import urlparse 

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.movies import movies_bp
    from routes.watchlist import watchlist_bp
    from routes.streaming import streaming_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(streaming_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@flaskflix.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin / admin123")
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

