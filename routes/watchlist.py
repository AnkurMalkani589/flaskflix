from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from models import Movie, watchlist
from extensions import db

watchlist_bp = Blueprint('watchlist', __name__)

@watchlist_bp.route('/watchlist/add/<int:movie_id>')
@login_required
def add(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    current_user.add_to_watchlist(movie)
    db.session.commit()
    flash(f'"{movie.title}" added to your watchlist!', 'success')
    return redirect(url_for('movies.detail', movie_id=movie_id))

@watchlist_bp.route('/watchlist/remove/<int:movie_id>')
@login_required
def remove(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    current_user.remove_from_watchlist(movie)
    db.session.commit()
    flash(f'"{movie.title}" removed from your watchlist.', 'info')
    return redirect(url_for('movies.detail', movie_id=movie_id))

@watchlist_bp.route('/watchlist')
@login_required
def index():
    movies = current_user.watchlist_movies.order_by(watchlist.c.added_at.desc()).all()
    return render_template('watchlist/index.html', movies=movies)

