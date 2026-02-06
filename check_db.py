#!/usr/bin/env python
"""Check database status."""
from app import create_app
from extensions import db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    print('Movie columns:', [c['name'] for c in inspector.get_columns('movies')])
    print('Tables:', inspector.get_table_names())
