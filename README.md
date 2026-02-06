# FlaskFlix - Netflix-like Movie Streaming App

A full-featured Netflix clone built with Flask, SQLAlchemy, PostgreSQL, and Bootstrap 5.

## Features

- 🎬 **Movie Catalog** - Browse movies with title, poster, description, and category
- 👤 **User Authentication** - Sign up, login, logout with secure password hashing
- 📋 **Watchlist** - Add/remove movies to personal watchlist
- 🔍 **Search & Filter** - Search movies by title or filter by category
- ⚡ **Admin CRUD** - Admin can add, edit, and delete movies
- 📱 **Responsive Design** - Bootstrap 5 powered modern UI
- 🎨 **Netflix-like Dark Theme** - Professional dark UI with red accents

## Project Structure

```
flask_website/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions (db, login, migrate)
├── models.py           # SQLAlchemy models (User, Movie)
├── seed_data.py        # Database seeding script
├── requirements.txt    # Python dependencies
│
├── routes/
│   ├── __init__.py     # Blueprint initialization
│   ├── auth.py         # Authentication routes
│   ├── movies.py       # Movie CRUD routes
│   └── watchlist.py    # Watchlist routes
│
├── static/
│   └── css/
│       └── main.css    # Custom styles
│
├── templates/
│   ├── base.html       # Base template with navbar
│   ├── home.html       # Home page
│   ├── auth/
│   │   ├── login.html  # Login form
│   │   └── signup.html # Signup form
│   ├── movies/
│   │   ├── index.html  # Movie listing
│   │   ├── detail.html # Movie details
│   │   └── form.html   # Add/Edit movie form
│   └── watchlist/
│       └── index.html  # User watchlist
│
└── virtual_env/        # Python virtual environment
```

## Database Models

### User
- `id` - Integer, Primary Key
- `username` - String(80), Unique, Not Null
- `email` - String(120), Unique, Not Null
- `password_hash` - String(256), Not Null
- `is_admin` - Boolean, Default False
- `created_at` - DateTime, Default now

### Movie
- `id` - Integer, Primary Key
- `title` - String(200), Not Null
- `poster` - String(500), Not Null
- `description` - Text, Not Null
- `category` - String(50), Not Null
- `release_year` - Integer
- `rating` - Float, Default 0.0
- `created_at` - DateTime, Default now
- `updated_at` - DateTime, Auto update

### Watchlist (Many-to-Many)
- Association table linking User and Movie
- `added_at` - Timestamp when added

## Setup Instructions

### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

### 2. Create Database
```sql
CREATE DATABASE flaskflix;
CREATE USER flaskuser WITH PASSWORD 'flaskpass';
GRANT ALL PRIVILEGES ON DATABASE flaskflix TO flaskuser;
ALTER USER flaskuser CREATEDB;
```

### 3. Install Dependencies
```bash
cd flask_website
source virtual_env/bin/activate
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
flask --app app db init
flask --app app db migrate
flask --app app db upgrade
```

### 5. Seed Sample Data
```bash
python seed_data.py
```

### 6. Run the Application
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Default Admin Account
- **Username:** admin
- **Password:** admin123

## Routes

| Route | Method | Description | Auth Required |
|-------|--------|-------------|---------------|
| `/` | GET | Home page | No |
| `/movies` | GET | Browse movies | No |
| `/movie/<id>` | GET | Movie details | No |
| `/movie/new` | GET/POST | Add movie (Admin) | Yes |
| `/movie/<id>/edit` | GET/POST | Edit movie (Admin) | Yes |
| `/movie/<id>/delete` | POST | Delete movie (Admin) | Yes |
| `/watchlist` | GET | User watchlist | Yes |
| `/watchlist/add/<id>` | GET | Add to watchlist | Yes |
| `/watchlist/remove/<id>` | GET | Remove from watchlist | Yes |
| `/login` | GET/POST | Login | No |
| `/signup` | GET/POST | Signup | No |
| `/logout` | GET | Logout | Yes |

## Environment Variables

Set these in your environment or `.env` file:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://flaskuser:flaskpass@localhost/flaskflix
```

## Technologies Used

- **Backend:** Flask 3.x
- **Database:** PostgreSQL with SQLAlchemy 2.x
- **ORM:** Flask-SQLAlchemy
- **Migrations:** Flask-Migrate
- **Auth:** Flask-Login
- **Frontend:** Bootstrap 5, Custom CSS
- **Templating:** Jinja2
- **Python:** 3.12

## License

MIT License

