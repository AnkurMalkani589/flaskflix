from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, session
from extensions import db, login_manager

# Association table for watchlist (many-to-many relationship)
watchlist = db.Table('watchlist',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    User model for authentication and user management.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist_movies = db.relationship('Movie', secondary=watchlist, 
                                        backref=db.backref('watched_by', lazy='dynamic'),
                                        lazy='dynamic')
    watch_progress = db.relationship('WatchProgress', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_token(self, expires_sec=1800):
        """Generate a password reset token"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.id, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, max_age=1800):
        """Verify a password reset token"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset-salt', max_age=max_age)
        except:
            return None
        return User.query.get(user_id)
    
    def add_to_watchlist(self, movie):
        if not self.is_in_watchlist(movie):
            self.watchlist_movies.append(movie)
    
    def remove_from_watchlist(self, movie):
        if self.is_in_watchlist(movie):
            self.watchlist_movies.remove(movie)
    
    def is_in_watchlist(self, movie):
        return self.watchlist_movies.filter(watchlist.c.movie_id == movie.id).count() > 0
    
    def get_watch_progress(self, movie_id):
        """Get user's watch progress for a specific movie"""
        return self.watch_progress.filter_by(movie_id=movie_id).first()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Movie(db.Model):
    """
    Movie model for storing movie information and streaming URLs.
    """
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    poster = db.Column(db.String(500), nullable=True)
    
    # Streaming URLs
    trailer_url = db.Column(db.String(500), nullable=True)  # YouTube trailer
    video_url = db.Column(db.String(500), nullable=True)    # Direct MP4 URL
    hls_url = db.Column(db.String(500), nullable=True)      # HLS playlist (.m3u8)
    
    # Video metadata
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    release_year = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    
    # Video quality variants (comma-separated for multiple qualities)
    # Format: "360p:url,720p:url,1080p:url"
    quality_variants = db.Column(db.Text, nullable=True)
    
    # Duration in seconds
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    watch_progress = db.relationship('WatchProgress', backref='movie', lazy='dynamic')
    
    def __repr__(self):
        return f'<Movie {self.title}>'
    
    @property
    def trailer_embed_url(self):
        """Convert YouTube URL to embed URL"""
        if not self.trailer_url:
            return None
        if "watch?v=" in self.trailer_url:
            video_id = self.trailer_url.split("watch?v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return self.trailer_url
    
    @property
    def formatted_duration(self):
        """Return formatted duration (HH:MM:SS)"""
        if not self.duration_seconds:
            return "00:00"
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    def get_quality_url(self, quality='720p'):
        """Get URL for specific quality"""
        if not self.quality_variants:
            return self.hls_url
        variants = {}
        for variant in self.quality_variants.split(','):
            if ':' in variant:
                q, url = variant.split(':', 1)
                variants[q] = url.strip()
        return variants.get(quality, self.hls_url)
    
    def get_qualities(self):
        """Return list of available qualities"""
        if not self.quality_variants:
            return []
        return [v.split(':')[0].strip() for v in self.quality_variants.split(',') if ':' in v]
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'poster': self.poster,
            'trailer_url': self.trailer_url,
            'trailer_embed_url': self.trailer_embed_url,
            'video_url': self.video_url,
            'hls_url': self.hls_url,
            'description': self.description,
            'category': self.category,
            'release_year': self.release_year,
            'rating': self.rating,
            'duration_seconds': self.duration_seconds,
            'formatted_duration': self.formatted_duration,
            'qualities': self.get_qualities()
        }


class WatchProgress(db.Model):
    """
    Track user's watch progress for each movie.
    Used for "Continue Watching" feature.
    """
    __tablename__ = 'watch_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    
    # Progress tracking
    current_time = db.Column(db.Float, default=0.0)  # Current position in seconds
    total_duration = db.Column(db.Float, default=0.0)  # Total movie duration
    
    # Percentage completed
    @property
    def percentage(self):
        if self.total_duration and self.total_duration > 0:
            return (self.current_time / self.total_duration) * 100
        return 0
    
    # Last watched timestamp
    last_watched_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='_user_movie_progress_uc'),
    )
    
    def update_progress(self, current_time, total_duration=None):
        """Update watch progress"""
        self.current_time = current_time
        if total_duration:
            self.total_duration = total_duration
        self.last_watched_at = datetime.utcnow()
    
    def is_completed(self, threshold=0.9):
        """Check if movie is considered completed (90% watched)"""
        if self.total_duration and self.total_duration > 0:
            return self.current_time >= (self.total_duration * threshold)
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'current_time': self.current_time,
            'total_duration': self.total_duration,
            'percentage': self.percentage,
            'last_watched_at': self.last_watched_at.isoformat() if self.last_watched_at else None
        }

