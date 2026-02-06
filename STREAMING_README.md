# FlaskFlix OTT Streaming Implementation

## Overview

This document describes the full movie streaming implementation for FlaskFlix, a Netflix-like OTT platform built with Flask, PostgreSQL, and SQLAlchemy.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S BROWSER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────────────────────────────────┐    │
│  │  Video.js    │────▶│  Get Stream Token (JWT-like)             │    │
│  │  Player      │◀────│  /stream/{movie_id}/token               │    │
│  └──────────────┘     └──────────────┬───────────────────────────┘    │
│                                       │                                │
│  ┌────────────────────────────────────▼──────────────────────────────┐│
│  │                     VIDEO STREAMING FLOW                          ││
│  │                                                                  ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ││
│  │  │ HLS (.m3u8) │ or │  MP4 Range  │ or │ External (S3/CDN)│    ││
│  │  │ Adaptive    │    │  Streaming  │    │  Signed URL     │    ││
│  │  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘    ││
│  │         │                   │                    │             ││
│  └─────────│───────────────────┼────────────────────┼─────────────┘│
│            │                   │                    │               │
└────────────│───────────────────┼────────────────────┼───────────────┘
             │                   │                    │
             ▼                   ▼                    ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   FLASK BACKEND                             │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  Token Validation & Access Control                  │    │
    │  │  • Validate session                                 │    │
    │  │  • Check subscription (extensible)                   │    │
    │  │  • Rate limiting                                     │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                                                              │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  Progress Tracking                                  │    │
    │  │  • Store current position                           │    │
    │  │  • Track completion percentage                      │    │
    │  │  • Enable "Continue Watching" feature              │    │
    │  └─────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────┘
             │                   │                    │
             ▼                   ▼                    ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   DATA STORAGE                              │
    │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
    │  │ PostgreSQL  │    │   Videos    │    │  Static Files   │  │
    │  │  Database   │    │  Directory  │    │  (CDN Ready)   │  │
    │  └─────────────┘    └─────────────┘    └─────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
```

## Database Model Changes

### Movie Model

Added streaming-related fields:

```python
class Movie(db.Model):
    # ... existing fields ...
    
    # Streaming URLs
    video_url = db.Column(db.String(500), nullable=True)    # Direct MP4 URL
    hls_url = db.Column(db.String(500), nullable=True)     # HLS .m3u8 playlist
    
    # Quality variants (for multi-quality HLS)
    quality_variants = db.Column(db.Text, nullable=True)   # "360p:url,720p:url,1080p:url"
    
    # Duration
    duration_seconds = db.Column(db.Integer, nullable=True)
```

### WatchProgress Model

New model for tracking user watch progress:

```python
class WatchProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    current_time = db.Column(db.Float, default=0.0)  # Position in seconds
    total_duration = db.Column(db.Float, default=0.0)
    last_watched_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Database Migration

```bash
# Create migration
flask db migrate -m "Add streaming fields to Movie model"

# Apply migration
flask db upgrade
```

Or manually add columns in PostgreSQL:

```sql
ALTER TABLE movies ADD COLUMN video_url VARCHAR(500);
ALTER TABLE movies ADD COLUMN hls_url VARCHAR(500);
ALTER TABLE movies ADD COLUMN quality_variants TEXT;
ALTER TABLE movies ADD COLUMN duration_seconds INTEGER;

CREATE TABLE watch_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    movie_id INTEGER NOT NULL REFERENCES movies(id),
    current_time FLOAT DEFAULT 0,
    total_duration FLOAT DEFAULT 0,
    last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);
```

## FFmpeg HLS Conversion Commands

### Install FFmpeg

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Convert MP4 to HLS (Single Quality)

```bash
ffmpeg -i input.mp4 \
  -codec: copy \
  -start_number 0 \
  -hls_time 10 \
  -hls_list_size 0 \
  -f hls \
  output.m3u8
```

### Convert MP4 to HLS (Multi-Quality/Adaptive Bitrate)

```bash
#!/bin/bash
# hls_transcode.sh

input="$1"
output_dir="hls_output"

mkdir -p "$output_dir"

# 1080p
ffmpeg -i "$input" \
  -vf scale=-1:1080 \
  -c:v libx264 -crf 23 -c:a aac \
  -hls_time 10 \
  -hls_list_size 0 \
  -f hls \
  -hls_segment_filename "$output_dir/1080p_%03d.ts" \
  "$output_dir/1080p.m3u8"

# 720p
ffmpeg -i "$input" \
  -vf scale=-1:720 \
  -c:v libx264 -crf 23 -c:a aac \
  -hls_time 10 \
  -hls_list_size 0 \
  -f hls \
  -hls_segment_filename "$output_dir/720p_%03d.ts" \
  "$output_dir/720p.m3u8"

# 360p
ffmpeg -i "$input" \
  -vf scale=-1:360 \
  -c:v libx264 -crf 28 -c:a aac \
  -hls_time 10 \
  -hls_list_size 0 \
  -f hls \
  -hls_segment_filename "$output_dir/360p_%03d.ts" \
  "$output_dir/360p.m3u8"

# Create master playlist
cat > "$output_dir/master.m3u8" <<EOF
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p.m3u8
EOF

echo "HLS files created in $output_dir/"
```

Usage:
```bash
chmod +x hls_transcode.sh
./hls_transcode.sh mymovie.mp4
```

### Extract Video Duration

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
```

## Streaming Security

### Token-Based Access Control

The implementation uses time-limited tokens for streaming access:

```python
# Token generation (valid for 4 hours)
token = generate_stream_token(movie_id, user_id)

# Token validation
validate_stream_token(token, movie_id)
```

### Production Security Enhancements

1. **Use Redis for Token Storage**
   ```python
   import redis
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   def generate_stream_token(movie_id, user_id):
       token = secrets.token_urlsafe(32)
       redis_client.setex(
           f"stream_token:{token}",
           14400,  # 4 hours
           json.dumps({'movie_id': movie_id, 'user_id': user_id})
       )
       return token
   ```

2. **Signed URLs for CDN**
   ```python
   from itsdangerous import URLSafeTimedSerializer
   
   def generate_signed_url(video_path, expires=3600):
       signer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
       data = {'path': video_path, 'exp': time.time() + expires}
       signature = signer.dumps(data)
       return f"/protected_video/{signature}"
   ```

3. **IP-Based Restrictions**
   ```python
   @streaming_bp.route('/stream/<int:movie_id>/video')
   @login_required
   def stream_video(movie_id):
       # Rate limit per IP
       if is_rate_limited(request.remote_addr, limit=10, window=3600):
           abort(429)
       
       # Validate token
       # Stream video
   ```

## Nginx Configuration (Production)

For efficient video serving, use nginx with X-Accel-Redirect:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Serve static content
    location /static/videos/ {
        internal;
        alias /path/to/your/static/videos/;
        mp4;
        flv;
    }

    # HLS segments
    location /hls/ {
        internal;
        alias /path/to/hls/;
        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t ts;
        }
        add_header Cache-Control "public, max-age=31536000";
    }

    # Gzip compression for playlists
    location ~* \.m3u8$ {
        gzip on;
        gzip_types application/vnd.apple.mpegurl;
    }

    # Flask app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## CDN Integration

### AWS CloudFront

1. Create CloudFront distribution with S3 origin
2. Set up origin access identity
3. Configure caching behaviors

### Video.js Configuration for CDN

```javascript
player.src([
    {
        src: 'https://your-cdn.cloudfront.net/videos/' + movieId + '/master.m3u8',
        type: 'application/vnd.apple.mpegurl',
        label: 'Auto',
        withCredentials: true
    }
]);
```

## Frontend Integration

### Video Player Setup

```javascript
// Initialize player
var player = videojs('video-player', {
    controls: true,
    autoplay: false,
    preload: 'auto',
    fluid: true,
    playbackRates: [0.5, 1, 1.25, 1.5, 2]
});

// Handle stream type
if (streamType === 'hls') {
    player.src({
        type: 'application/vnd.apple.mpegurl',
        src: streamUrl
    });
} else {
    player.src({
        type: 'video/mp4',
        src: streamUrl
    });
}

// Resume playback position
if (savedProgress && savedProgress.current_time > 0) {
    player.currentTime(savedProgress.current_time);
}
```

### Progress Tracking

```javascript
// Save progress every 5 seconds
player.on('timeupdate', function() {
    var currentTime = player.currentTime();
    var duration = player.duration();
    
    if (Math.floor(currentTime) % 5 === 0) {
        saveProgress(currentTime, duration);
    }
});

// Save on pause
player.on('pause', function() {
    saveProgress(player.currentTime(), player.duration());
});

// Mark as completed
player.on('ended', function() {
    saveProgress(player.duration(), player.duration());
});
```

## Continue Watching Feature

### API Endpoint

```
GET /continue-watching
Response:
[
    {
        "movie": {
            "id": 1,
            "title": "Movie Title",
            "poster": "url",
            ...
        },
        "progress": {
            "current_time": 125.5,
            "total_duration": 7200,
            "percentage": 1.74,
            ...
        }
    },
    ...
]
```

### Display Component

```javascript
// In homepage template
<div id="continueWatching" class="row">
    <!-- Populated by JavaScript -->
</div>

<script>
fetch('/continue-watching')
    .then(response => response.json())
    .then(data => {
        data.forEach(item => {
            // Render movie card with progress bar
        });
    });
</script>
```

## Testing

### Unit Tests

```python
import pytest

class TestStreaming:
    def test_get_stream_token(self, client, logged_in_user):
        response = client.get('/stream/1/token')
        assert response.status_code == 200
        assert 'token' in response.json
        
    def test_stream_token_requires_login(self, client):
        response = client.get('/stream/1/token')
        assert response.status_code == 401
        
    def test_progress_tracking(self, client, logged_in_user):
        # Update progress
        response = client.post('/stream/1/progress', 
            json={'current_time': 100, 'total_duration': 1000})
        assert response.status_code == 200
        
        # Get progress
        response = client.get('/stream/1/progress')
        assert response.json['current_time'] == 100
```

### Manual Testing

1. Add a movie with video_url (test video URL)
2. Go to movie detail page
3. Click "Watch Now"
4. Verify player loads and video plays
5. Pause at some point
6. Refresh page
7. Verify playback resumes from same position

## Scalability Considerations

### Horizontal Scaling

1. **Session Storage**: Use Redis for session storage
2. **Token Storage**: Use Redis for streaming tokens
3. **Database**: Use connection pooling (PgBouncer)

### Video Storage Tiers

```
┌─────────────────────────────────────────────────────────────┐
│                    VIDEO STORAGE TIERS                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  HOT: Recently accessed videos                       │     │
│  │  • SSD storage                                     │     │
│  │  • CDN edge caching                                │     │
│  │  • In-memory cache (Redis)                          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  WARM: Popular videos                               │     │
│  │  • HDD storage                                     │     │
│  │  • CDN standard tier                               │     │
│  │  • Weekly access patterns                           │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  COLD: Archive videos                               │     │
│  │  • Object storage (S3 Glacier)                     │     │
│  │  • On-demand transcoding                           │     │
│  │  • Longer retrieval time acceptable                │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Bandwidth Optimization

1. **Adaptive Bitrate Streaming**: Automatically select quality based on network
2. **Content Compression**: Gzip for manifest files
3. **Caching**: CDN caching for frequently accessed segments
4. **Preloading**: Preload first segments for faster start

## Performance Benchmarks

| Metric | Target | Optimization |
|--------|--------|--------------|
| Video Start Time | < 2 seconds | CDN edge, preload |
| Seek Response | < 500ms | Cached segments |
| Buffer Ratio | < 5% | Adaptive bitrate |
| Concurrent Users | 1000+/server | Horizontal scaling |

## Deployment Checklist

- [ ] Install FFmpeg on servers
- [ ] Configure nginx for video streaming
- [ ] Set up Redis for token storage
- [ ] Configure CDN for video distribution
- [ ] Set up monitoring for stream health
- [ ] Implement analytics for stream quality
- [ ] Configure SSL/TLS certificates
- [ ] Set up database migration scripts
- [ ] Configure backup and disaster recovery

## Monitoring & Analytics

### Key Metrics

1. **Stream Health**
   - Bitrate
   - Buffer ratio
   - Startup time
   - Rebuffering events

2. **User Experience**
   - Completion rate
   - Drop-off points
   - Quality preferences

3. **System Performance**
   - CDN hit ratio
   - Storage I/O
   - Database queries/second

### Logging

```python
import logging

logger = logging.getLogger('streaming')

@streaming_bp.route('/stream/<int:movie_id>/token')
@login_required
def get_stream_token(movie_id):
    logger.info(f"Stream token requested: movie={movie_id}, user={current_user.id}")
    # ...
```

## Related Files

| File | Description |
|------|-------------|
| `models.py` | Movie and WatchProgress models |
| `routes/streaming.py` | Streaming endpoints and token management |
| `templates/movies/watch.html` | Video player page |
| `routes/movies.py` | Movie routes including /watch |
| `app.py` | Blueprint registration |

## Quick Start

```bash
# 1. Install dependencies
pip install flask flask-sqlalchemy flask-login psycopg2-binary

# 2. Run migrations
flask db upgrade

# 3. Add a movie with streaming URL (use test video)
# Admin → Add Movie → Enter video_url

# 4. Start server
python app.py

# 5. Visit http://localhost:5000/movie/1
# Click "Watch Now" to stream
```

