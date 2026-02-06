from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from models import Movie
from flask_login import login_required, current_user
from extensions import db

movies_bp = Blueprint('movies', __name__)

@movies_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Movie.query
    
    if search:
        query = query.filter(Movie.title.ilike(f'%{search}%'))
    
    if category:
        query = query.filter_by(category=category)
    
    movies = query.order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = db.session.query(Movie.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('movies/index.html', movies=movies, categories=categories)

@movies_bp.route('/movie/<int:movie_id>')
def detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    in_watchlist = False
    has_streaming = bool(movie.video_url or movie.hls_url)
    if current_user.is_authenticated:
        in_watchlist = current_user.is_in_watchlist(movie)
    
    return render_template('movies/detail.html', movie=movie, in_watchlist=in_watchlist, has_streaming=has_streaming)

@movies_bp.route('/movie/<int:movie_id>/watch')
@login_required
def watch(movie_id):
    """
    Movie streaming page with Video.js player.
    
    This page provides full movie streaming with:
    - Secure token-based access
    - Progress tracking for "Continue Watching"
    - Quality selection (when HLS is available)
    """
    movie = Movie.query.get_or_404(movie_id)
    
    # Check if movie has streaming available
    has_streaming = bool(movie.video_url or movie.hls_url)
    
    in_watchlist = False
    if current_user.is_authenticated:
        in_watchlist = current_user.is_in_watchlist(movie)
    
    return render_template(
        'movies/watch.html', 
        movie=movie, 
        in_watchlist=in_watchlist,
        has_streaming=has_streaming
    )

@movies_bp.route('/movie/new', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin:
        abort(403)
    
    if request.method == 'POST':
        movie = Movie(
            title=request.form['title'],
            poster=request.form['poster'],
            trailer_url=request.form.get('trailer_url', ''),
            video_url=request.form.get('video_url', ''),
            hls_url=request.form.get('hls_url', ''),
            description=request.form['description'],
            category=request.form['category'],
            release_year=int(request.form['release_year']),
            rating=float(request.form.get('rating', 0))
        )
        db.session.add(movie)
        db.session.commit()
        flash('Movie added successfully!', 'success')
        return redirect(url_for('movies.index'))
    
    return render_template('movies/form.html', movie=None, title='Add New Movie')

@movies_bp.route('/movie/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    if not current_user.is_admin:
        abort(403)
    
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        movie.title = request.form['title']
        movie.poster = request.form['poster']
        movie.trailer_url = request.form.get('trailer_url', '')
        movie.video_url = request.form.get('video_url', '')
        movie.hls_url = request.form.get('hls_url', '')
        movie.description = request.form['description']
        movie.category = request.form['category']
        movie.release_year = int(request.form['release_year'])
        movie.rating = float(request.form.get('rating', 0))
        db.session.commit()
        flash('Movie updated successfully!', 'success')
        return redirect(url_for('movies.detail', movie_id=movie.id))
    
    return render_template('movies/form.html', movie=movie, title='Edit Movie')

@movies_bp.route('/movie/<int:movie_id>/delete', methods=['POST'])
@login_required
def delete(movie_id):
    if not current_user.is_admin:
        abort(403)
    
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted!', 'success')
    return redirect(url_for('movies.index'))

