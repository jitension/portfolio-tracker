# Portfolio Performance Tracker - Backend

Django REST Framework API for Robinhood portfolio tracking and analytics.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB 6.0+
- Redis 7.0+
- Docker & Docker Compose (recommended)

### Local Development Setup

#### Option 1: Using Docker (Recommended)

```bash
# From project root
docker-compose up -d mongodb redis

# Install dependencies in virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements/development.txt

# Copy environment file
cp .env.example .env

# Generate secure keys
python -c "from django.core.management.utils import get_random_secret_key; print('SECRET_KEY=' + get_random_secret_key())" >> .env
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" >> .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

#### Option 2: Full Docker

```bash
# Build and start all services
docker-compose up --build

# In another terminal, run migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser
```

### Access Points

- **API Base URL:** http://localhost:8000/api/v1/
- **Django Admin:** http://localhost:8000/admin/
- **API Documentation:** http://localhost:8000/api/v1/ (browsable API)

## 📁 Project Structure

```
backend/
├── config/                  # Django project configuration
│   ├── settings/           # Split settings (base, dev, prod)
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI application
│   └── celery.py          # Celery configuration
├── apps/                   # Django applications
│   ├── authentication/    # User auth & JWT
│   ├── portfolio/         # Portfolio management
│   ├── transactions/      # Transaction history
│   ├── options/           # Options trading
│   ├── dividends/         # Dividend tracking
│   ├── watchlists/        # Watchlist management
│   └── robinhood/         # Robinhood API integration
├── core/                   # Core utilities
│   ├── encryption.py      # Credential encryption
│   └── exceptions.py      # Custom exceptions
├── requirements/           # Python dependencies
├── Dockerfile             # Docker image definition
└── manage.py              # Django management script
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/authentication/tests/test_views.py
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8
pylint apps/

# Type checking
mypy apps/

# Security check
bandit -r apps/
safety check
```

### Django Management Commands

```bash
# Create new app
python manage.py startapp app_name

# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Celery Tasks

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (scheduler)
celery -A config beat -l info

# Monitor tasks with Flower
celery -A config flower
```

## 🔐 Security

### Generate Secure Keys

```bash
# SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Important Security Notes

- **Never commit .env files** to version control
- **Rotate keys regularly** (quarterly recommended)
- **Use strong passwords** for MongoDB and Redis in production
- **Enable HTTPS** in production

## 📝 API Documentation

### Authentication Endpoints

```
POST   /api/v1/auth/register        - Register new user
POST   /api/v1/auth/login           - Login (get JWT tokens)
POST   /api/v1/auth/refresh         - Refresh access token
POST   /api/v1/auth/logout          - Logout (blacklist token)
GET    /api/v1/auth/user/me         - Get current user
PUT    /api/v1/auth/user/me/update  - Update profile
POST   /api/v1/auth/user/me/change-password - Change password
GET    /api/v1/auth/health/health   - Health check
```

### Example: Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "investor",
    "email": "investor@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Example: Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investor@example.com",
    "password": "SecurePassword123!"
  }'
```

## 🐛 Troubleshooting

### Django Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements/development.txt --force-reinstall

# Check for migration issues
python manage.py showmigrations
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker ps | grep mongodb

# Test connection
docker exec -it portfolio_mongodb_dev mongosh

# Check connection string in .env
cat .env | grep MONGODB_URI
```

### Celery Issues

```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli ping

# Check Celery worker
celery -A config inspect active
```

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Djongo Documentation](https://www.djongomapper.com/)
- [robin-stocks Documentation](https://www.robin-stocks.com/)
- [Celery Documentation](https://docs.celeryproject.org/)

## 🤝 Contributing

See [DEVELOPMENT_ROADMAP.md](../docs/prd/DEVELOPMENT_ROADMAP.md) for development phases and tasks.

## 📄 License

[Your License Here]
