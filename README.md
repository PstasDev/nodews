# Nodews - Django ASGI Apps Collection

A collection of non-critical Django ASGI applications powered by Daphne.

## Project Structure

```
nodews/
├── nodews_project/          # Main Django project
│   ├── settings.py         # Django settings with ASGI configuration
│   ├── urls.py            # Main URL routing
│   ├── asgi.py            # ASGI application configuration
│   └── wsgi.py            # WSGI application (fallback)
├── authentication/         # Authentication app & app index
│   ├── views.py           # Index view for app collection
│   ├── urls.py            # Authentication URLs
│   └── templates/         # HTML templates
├── bufe/                   # Büfé app (empty, for future development)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Apps

### 1. Authentication
- **Purpose**: User authentication and serves as the main index/collection page
- **URL**: `/` and `/auth/`
- **Status**: Active

### 2. Büfé
- **Purpose**: Empty Django app for future development
- **URL**: `/bufe/`
- **Status**: In Development

## Setup

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your settings
```

### 3. Database Setup
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 4. Static Files
```bash
# Collect static files
python manage.py collectstatic
```

## Running the Application

### Development Server (Django)
```bash
python manage.py runserver
```

### ASGI Server (Daphne)
```bash
daphne -p 8000 nodews_project.asgi:application
```

### With Channels/WebSocket support
```bash
# Start Redis server first (required for channels)
redis-server

# Then start Daphne
daphne nodews_project.asgi:application
```

## Features

- **ASGI Support**: Full ASGI compatibility with Daphne server
- **WebSocket Ready**: Configured for WebSocket connections via Channels
- **Static Files**: WhiteNoise for efficient static file serving
- **Environment Config**: python-decouple for environment variable management
- **Responsive UI**: Clean, modern interface for the app collection page

## Development

### Adding New Apps
```bash
# Create new Django app
python manage.py startapp your_app_name

# Add to INSTALLED_APPS in settings.py
# Create URLs and add to main urls.py
```

### Redis Configuration
For WebSocket functionality, ensure Redis is running:
```bash
# Windows (if Redis is installed)
redis-server

# Or use Docker
docker run -p 6379:6379 redis:alpine
```

## Production Notes

- Configure proper SECRET_KEY in production
- Set DEBUG=False
- Configure proper ALLOWED_HOSTS
- Use PostgreSQL or another production database
- Set up proper Redis instance
- Configure reverse proxy (nginx) for static files

## Technologies

- **Django 5.2.7**: Web framework
- **Daphne**: ASGI server
- **Channels**: WebSocket support
- **Redis**: Channel layer backend
- **WhiteNoise**: Static file serving
- **python-decouple**: Environment configuration