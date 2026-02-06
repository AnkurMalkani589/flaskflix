"""
Seed script to populate the database with sample movies.
Run this after setting up PostgreSQL and creating the database.

Usage:
    python seed_data.py
"""

from app import create_app
from models import db, Movie

def seed_movies():
    app = create_app()
    with app.app_context():
        # Check if movies already exist
        if Movie.query.first():
            print("Movies already exist in database. Skipping seed.")
            return
        
        movies = [
            {
                "title": "Big Buck Bunny",
                "poster": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Big_buck_bunny_poster_big.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=YE7VzlLtp-4",
                "video_url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "description": "A large and lovable rabbit deals with three tiny bullies, led by a flying squirrel, in this animated short film.",
                "category": "Animation",
                "release_year": 2008,
                "rating": 7.8,
                "duration_seconds": 596
            },
            {
                "title": "Inception",
                "poster": "https://image.tmdb.org/t/p/w500/9gk7admal4zlWH9t0bY0J8C7GYS.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=YoHD9XEInc0",
                "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                "category": "Action",
                "release_year": 2010,
                "rating": 8.8,
                "duration_seconds": 8880
            },
            {
                "title": "The Dark Knight",
                "poster": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
                "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                "category": "Action",
                "release_year": 2008,
                "rating": 9.0,
                "duration_seconds": 8820
            },
            {
                "title": "Interstellar",
                "poster": "https://image.tmdb.org/t/p/w500/gEU2QniL6C8z6W2XWMr2i9dV6X5.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=zSWdZVtXT7E",
                "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
                "category": "Sci-Fi",
                "release_year": 2014,
                "rating": 8.6,
                "duration_seconds": 9720
            },
            {
                "title": "Parasite",
                "poster": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=5xH0HfJHsaY",
                "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
                "category": "Drama",
                "release_year": 2019,
                "rating": 8.5,
                "duration_seconds": 7800
            },
            {
                "title": "The Shawshank Redemption",
                "poster": "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=6hB3S9bIaco",
                "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                "category": "Drama",
                "release_year": 1994,
                "rating": 9.3,
                "duration_seconds": 8520
            },
            {
                "title": "Pulp Fiction",
                "poster": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=s7EdQ4FqbhY",
                "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                "category": "Crime",
                "release_year": 1994,
                "rating": 8.9,
                "duration_seconds": 9180
            },
            {
                "title": "Forrest Gump",
                "poster": "https://image.tmdb.org/t/p/w500/saHP97rTPS5eLmrLQEcANmKrsFl.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=bLvqoHBptjg",
                "description": "The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate and other historical events unfold from the perspective of an Alabama man with an IQ of 75.",
                "category": "Drama",
                "release_year": 1994,
                "rating": 8.8,
                "duration_seconds": 8520
            },
            {
                "title": "The Matrix",
                "poster": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpQBjQF.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
                "description": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth.",
                "category": "Sci-Fi",
                "release_year": 1999,
                "rating": 8.7,
                "duration_seconds": 8160
            },
            {
                "title": "Goodfellas",
                "poster": "https://image.tmdb.org/t/p/w500/pKTnyjM7dQ7x7r7H9teQQj7F7e.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=2ilz-f1KnFY",
                "description": "The story of Henry Hill and his family in the Italian-American crime syndicate.",
                "category": "Crime",
                "release_year": 1990,
                "rating": 8.7,
                "duration_seconds": 8580
            },
            {
                "title": "Fight Club",
                "poster": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7efjplsX1ec.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=qtRKdVHc-cE",
                "description": "An insomniac office worker and a devil-may-care soap maker form an underground fight club.",
                "category": "Drama",
                "release_year": 1999,
                "rating": 8.8,
                "duration_seconds": 8340
            },
            {
                "title": "Gladiator",
                "poster": "https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=owK1qxDselE",
                "description": "A former Roman General sets out to exact vengeance against the corrupt emperor.",
                "category": "Action",
                "release_year": 2000,
                "rating": 8.5,
                "duration_seconds": 10200
            },
            {
                "title": "The Godfather",
                "poster": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=sY1S34973zA",
                "description": "The aging patriarch of an organized crime dynasty transfers control to his reluctant son.",
                "category": "Crime",
                "release_year": 1972,
                "rating": 9.2,
                "duration_seconds": 10500
            },
            {
                "title": "Avengers: Infinity War",
                "poster": "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=6ZfuNTqbHE8",
                "description": "The Avengers and their allies must sacrifice all to defeat Thanos.",
                "category": "Action",
                "release_year": 2018,
                "rating": 8.4,
                "duration_seconds": 8940
            },
            {
                "title": "Coco",
                "poster": "https://image.tmdb.org/t/p/w500/e64WCd7KQrevP7S3ysW7Rj589.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=xlnPHQ3TLX8",
                "description": "Aspiring musician Miguel enters the Land of the Dead to find his great-great-grandfather.",
                "category": "Animation",
                "release_year": 2017,
                "rating": 8.4,
                "duration_seconds": 6300
            },
            {
                "title": "The Silence of the Lambs",
                "poster": "https://image.tmdb.org/t/p/w500/r6i6U5lF7WW1l4KiiXI1uC8U4QZ.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=W6Mm8Sbe__o",
                "description": "A young FBI cadet must receive help from an incarcerated cannibal killer.",
                "category": "Thriller",
                "release_year": 1991,
                "rating": 8.6,
                "duration_seconds": 7080
            }
        ]
        
        for movie_data in movies:
            movie = Movie(**movie_data)
            db.session.add(movie)
        
        db.session.commit()
        print(f"Successfully added {len(movies)} movies to the database!")

if __name__ == "__main__":
    seed_movies()

