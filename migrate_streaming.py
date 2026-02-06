"""
Database migration script for streaming functionality.
Run this script to add new streaming fields to the database.

Usage:
    python migrate_streaming.py
"""

from sqlalchemy import inspect, text
from app import create_app
from extensions import db

def migrate():
    app = create_app()
    with app.app_context():
        print("Starting database migration for streaming functionality...")
        
        # Get inspector from SQLAlchemy engine
        inspector = inspect(db.engine)
        movie_columns = [c['name'] for c in inspector.get_columns('movies')]
        
        print(f"Current movie columns: {movie_columns}")
        
        columns_to_add = {
            'video_url': 'VARCHAR(500)',
            'hls_url': 'VARCHAR(500)',
            'quality_variants': 'TEXT',
            'duration_seconds': 'INTEGER'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in movie_columns:
                try:
                    db.session.execute(
                        text(f"ALTER TABLE movies ADD COLUMN {column_name} {column_type}")
                    )
                    print(f"  Added column: {column_name}")
                except Exception as e:
                    print(f"  Error adding {column_name}: {e}")
            else:
                print(f"  Column {column_name} already exists")
        
        # Check if watch_progress table exists
        table_exists = 'watch_progress' in inspector.get_table_names()
        
        if not table_exists:
            print("Creating watch_progress table...")
            db.session.execute(text("""
                CREATE TABLE watch_progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    movie_id INTEGER NOT NULL REFERENCES movies(id),
                    current_time FLOAT DEFAULT 0.0,
                    total_duration FLOAT DEFAULT 0.0,
                    last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, movie_id)
                )
            """))
            print("  Created watch_progress table")
        else:
            print("  watch_progress table already exists")
        
        # Commit changes
        db.session.commit()
        
        print("\nMigration completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python seed_data.py' to add sample movies with streaming")
        print("2. Restart your Flask development server")
        print("3. Visit /movie/1 to see the 'Watch Now' button")

if __name__ == "__main__":
    migrate()
