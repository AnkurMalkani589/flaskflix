"""
Streaming routes for secure video delivery.
Implements HLS streaming, progress tracking, and access control.
"""

from flask import Blueprint, send_file, request, jsonify, session, Response, current_app
from flask_login import login_required, current_user
from models import Movie, WatchProgress
from extensions import db
import os
import secrets
import time
from datetime import datetime, timedelta

streaming_bp = Blueprint('streaming', __name__)

# Token-based streaming security
# In production, use Redis for token storage with expiry
STREAM_TOKENS = {}


def generate_stream_token(movie_id, user_id):
    """
    Generate a secure streaming token for a movie.
    
    Architecture:
    - Token is generated when user accesses the movie
    - Token is valid for a limited time (e.g., 4 hours)
    - Token is tied to specific movie and user
    - Prevents sharing of direct video URLs
    
    Production Enhancement:
    - Use Redis with TTL for token storage
    - Add rate limiting per user
    - Track streaming sessions
    """
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=4)
    
    STREAM_TOKENS[token] = {
        'movie_id': movie_id,
        'user_id': user_id,
        'expiry': expiry,
        'created_at': datetime.utcnow()
    }
    return token


def validate_stream_token(token, movie_id):
    """
    Validate a streaming token.
    
    Returns True if valid, False otherwise.
    """
    token_data = STREAM_TOKENS.get(token)
    if not token_data:
        return False
    
    # Check expiry
    if token_data['expiry'] < datetime.utcnow():
        del STREAM_TOKENS[token]
        return False
    
    # Verify movie match
    if token_data['movie_id'] != movie_id:
        return False
    
    return True


def cleanup_expired_tokens():
    """Remove expired tokens from memory."""
    now = datetime.utcnow()
    expired = [t for t, data in STREAM_TOKENS.items() if data['expiry'] < now]
    for t in expired:
        del STREAM_TOKENS[t]


@streaming_bp.route('/stream/<int:movie_id>/token')
@login_required
def get_stream_token(movie_id):
    """
    Generate a secure streaming token for a movie.
    This token is used to access the video stream.
    """
    movie = Movie.query.get_or_404(movie_id)
    
    # Check if movie has streaming available
    if not movie.video_url and not movie.hls_url:
        return jsonify({'error': 'Streaming not available for this movie'}), 404
    
    # Check subscription/access (extend for subscription system)
    # For now, any authenticated user can stream
    
    # Generate token
    token = generate_stream_token(movie_id, current_user.id)
    
    # Determine stream URL based on available sources
    if movie.hls_url:
        # Use HLS streaming with token protection
        stream_base = url_for('streaming.stream_hls_manifest', 
                              movie_id=movie_id, token=token, _external=True)
        stream_type = 'hls'
    else:
        # Use direct MP4 with token protection
        stream_base = url_for('streaming.stream_video', 
                              movie_id=movie_id, token=token, _external=True)
        stream_type = 'mp4'
    
    # Get or create watch progress
    progress = current_user.get_watch_progress(movie_id)
    if not progress:
        progress = WatchProgress(user_id=current_user.id, movie_id=movie_id)
        db.session.add(progress)
        db.session.commit()
    
    return jsonify({
        'token': token,
        'stream_url': stream_base,
        'stream_type': stream_type,
        'movie': movie.to_dict(),
        'progress': progress.to_dict() if progress else None
    })


@streaming_bp.route('/stream/<int:movie_id>/hls/playlist.m3u8')
def stream_hls_manifest(movie_id):
    """
    Serve HLS playlist (.m3u8) with token validation.
    
    Architecture:
    - User requests playlist with valid token
    - Server validates token
    - Returns master playlist with quality variants
    - Player requests segments from segment endpoint
    """
    token = request.args.get('token')
    if not token or not validate_stream_token(token, movie_id):
        return jsonify({'error': 'Invalid or expired token'}), 403
    
    movie = Movie.query.get_or_404(movie_id)
    
    # Master playlist with quality variants
    base_url = request.host_url.rstrip('/')
    
    master_playlist = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
{base_url}{url_for('streaming.stream_hls_quality', movie_id=movie_id, quality='360p', token=token, _external=True)}
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
{base_url}{url_for('streaming.stream_hls_quality', movie_id=movie_id, quality='720p', token=token, _external=True)}
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
{base_url}{url_for('streaming.stream_hls_quality', movie_id=movie_id, quality='1080p', token=token, _external=True)}
"""
    
    return Response(master_playlist, mimetype='application/vnd.apple.mpegurl')


@streaming_bp.route('/stream/<int:movie_id>/hls/<quality>/playlist.m3u8')
def stream_hls_quality(movie_id, quality):
    """
    Serve HLS playlist for specific quality.
    In production, this would point to pre-processed HLS files.
    """
    token = request.args.get('token')
    if not token or not validate_stream_token(token, movie_id):
        return jsonify({'error': 'Invalid or expired token'}), 403
    
    movie = Movie.query.get_or_404(movie_id)
    
    # For demo, create segments from MP4 or placeholder
    # In production, these would be pre-processed .ts files
    base_url = request.host_url.rstrip('/')
    
    # Generate segment playlist (simplified)
    segment_playlist = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
"""
    
    # Add segment entries (demo - 10 segments)
    for i in range(10):
        segment_playlist += f"#EXTINF:10.0,\n"
        segment_playlist += f"{base_url}{url_for('streaming.stream_hls_segment', movie_id=movie_id, quality=quality, segment=i, token=token, _external=True)}\n"
    
    segment_playlist += "#EXT-X-ENDLIST"
    
    return Response(segment_playlist, mimetype='application/vnd.apple.mpegurl')


@streaming_bp.route('/stream/<int:movie_id>/hls/<quality>/<int:segment>.ts')
def stream_hls_segment(movie_id, quality, segment):
    """
    Serve HLS video segment (.ts file).
    
    Production Optimization:
    - Serve from CDN/static file server
    - Use nginx with X-Accel-Redirect for efficient delivery
    - Cache segments at CDN edge
    """
    token = request.args.get('token')
    if not token or not validate_stream_token(token, movie_id):
        return jsonify({'error': 'Invalid or expired token'}), 403
    
    movie = Movie.query.get_or_404(movie_id)
    
    # In production, serve actual .ts files
    # For demo, return a small video chunk
    
    # Demo: Return placeholder response
    # In production: send_file(f"/path/to/hls/{movie_id}/{quality}/{segment}.ts")
    
    return Response(
        b'\x00' * 1024,  # Dummy segment data
        mimetype='video/mp2t',
        headers={'Content-Length': '1024'}
    )


@streaming_bp.route('/stream/<int:movie_id>/video')
@login_required
def stream_video(movie_id):
    """
    Direct MP4 video streaming with range support.
    
    Features:
    - Supports HTTP Range requests for seeking
    - Streams in chunks (4MB by default)
    - Token validated for each request
    
    Production Enhancement:
    - Use nginx X-Accel-Redirect for efficient file serving
    - Implement proper chunked transfer encoding
    - Add CDN support
    """
    token = request.args.get('token')
    if not token or not validate_stream_token(token, movie_id):
        return jsonify({'error': 'Invalid or expired token'}), 403
    
    movie = Movie.query.get_or_404(movie_id)
    
    if not movie.video_url:
        return jsonify({'error': 'Direct streaming not available'}), 404
    
    # For external URLs (e.g., AWS S3, CDN)
    if movie.video_url.startswith(('http://', 'https://')):
        # Redirect to signed URL for external storage
        # In production, generate time-limited signed URL
        return jsonify({
            'stream_url': movie.video_url,
            'type': 'redirect'
        })
    
    # Local file streaming
    video_path = os.path.join(
        current_app.root_path,
        'static',
        'videos',
        movie.video_url.lstrip('/static/videos/')
    )
    
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    # Get file size
    file_size = os.path.getsize(video_path)
    
    # Handle range requests for seeking
    range_header = request.headers.get('Range')
    
    if range_header:
        # Parse range header
        range_spec = range_header.replace('bytes=', '')
        start, end = range_spec.split('-')
        start = int(start)
        end = int(end) if end else file_size - 1
        
        # Limit chunk size (4MB)
        chunk_size = 4 * 1024 * 1024
        end = min(end, start + chunk_size - 1)
        
        # Open file and seek to position
        video_file = open(video_path, 'rb')
        video_file.seek(start)
        
        def generate():
            while video_file.tell() <= end:
                chunk = video_file.read(8192)
                if not chunk:
                    break
                yield chunk
            video_file.close()
        
        return Response(
            generate(),
            status=206,
            mimetype='video/mp4',
            headers={
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(end - start + 1)
            }
        )
    
    # Full file download (fallback)
    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True
    )


@streaming_bp.route('/stream/<int:movie_id>/progress', methods=['POST'])
@login_required
def update_progress(movie_id):
    """
    Update user's watch progress for a movie.
    
    Called periodically by JavaScript as video plays.
    
    Frequency recommendations:
    - Every 5-10 seconds during playback
    - On pause
    - On video ended
    """
    data = request.get_json()
    
    current_time = data.get('current_time', 0)
    total_duration = data.get('total_duration', 0)
    
    # Get or create progress record
    progress = current_user.get_watch_progress(movie_id)
    if not progress:
        progress = WatchProgress(user_id=current_user.id, movie_id=movie_id)
        db.session.add(progress)
    
    # Update progress
    progress.update_progress(current_time, total_duration)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'progress': progress.to_dict()
    })


@streaming_bp.route('/stream/<int:movie_id>/progress')
@login_required
def get_progress(movie_id):
    """Get user's watch progress for a movie."""
    progress = current_user.get_watch_progress(movie_id)
    
    if progress:
        return jsonify(progress.to_dict())
    
    return jsonify({
        'current_time': 0,
        'total_duration': 0,
        'percentage': 0,
        'is_completed': False
    })


@streaming_bp.route('/continue-watching')
@login_required
def continue_watching():
    """
    Get list of movies the user is currently watching.
    Used for "Continue Watching" section on homepage.
    
    Returns movies sorted by last watch time,
    excluding fully watched movies.
    """
    from sqlalchemy import desc
    
    # Get progress records sorted by last watched
    progress_list = current_user.watch_progress.order_by(
        desc(WatchProgress.last_watched_at)
    ).limit(10).all()
    
    continue_watching = []
    for progress in progress_list:
        if not progress.is_completed():
            movie = Movie.query.get(progress.movie_id)
            if movie:
                continue_watching.append({
                    'movie': movie.to_dict(),
                    'progress': progress.to_dict()
                })
    
    return jsonify(continue_watching)


@streaming_bp.route('/streaming-stats')
@login_required
def streaming_stats():
    """Get streaming statistics for admin."""
    cleanup_expired_tokens()
    
    stats = {
        'active_tokens': len(STREAM_TOKENS),
        'active_users': len(set(t['user_id'] for t in STREAM_TOKENS.values())),
        'server_time': datetime.utcnow().isoformat()
    }
    
    return jsonify(stats)


# Import url_for at module level to avoid circular imports
from flask import url_for

