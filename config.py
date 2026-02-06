import os
import urllib.parse

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'

    # Database credentials
    DB_USER = 'postgres'
    DB_PASSWORD = 'Ankur@589'
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_NAME = 'flaskflixdb'

    DB_PASSWORD_ESCAPED = urllib.parse.quote_plus(DB_PASSWORD)

    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ESCAPED}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    }

    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = 86400  # 1 day

    # Pagination
    MOVIES_PER_PAGE = 12
