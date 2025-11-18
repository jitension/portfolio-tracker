# Portfolio Tracker

A full-stack portfolio management application for tracking investments, holdings, and performance with Robinhood integration.

## 🚀 Features

- 📊 Real-time portfolio tracking and performance monitoring
- 📈 Investment analytics with charts and visualizations
- 🔄 Robinhood API integration for automated portfolio sync
- 📱 Responsive Material UI design
- 🔐 Secure credential encryption
- ⚡ Background task processing with Celery
- 🐳 Production-ready Docker deployment

## 🏗️ Tech Stack

**Frontend:**
- React 19 + TypeScript
- Material UI (MUI)
- Vite
- Redux Toolkit

**Backend:**
- Django 5 + Django REST Framework
- MongoEngine (MongoDB ODM)
- Celery for background tasks
- Redis for caching & message broker

**Infrastructure:**
- MongoDB 4.4
- Redis 7
- Nginx
- Docker & Docker Compose
- GitHub Actions for CI/CD

## 📦 Deployment

**Standard docker-compose deployment** using pre-built images from GitHub Container Registry.

### Quick Deploy (3 Steps)

```bash
# 1. One-time: Login to pull images (if private)
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u jitension --password-stdin

# 2. Clone and configure
git clone https://github.com/jitension/portfolio.git
cd portfolio
cp .env.example .env
nano .env  # Edit with your values

# 3. Deploy
docker-compose pull
docker-compose up -d
docker-compose exec django python manage.py createsuperuser
```

**See full deployment guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 🔧 Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (Local)
```bash
# Use dev docker-compose
docker-compose -f docker-compose.dev.yml up
```

## 📝 Configuration

Copy `.env.example` to `.env` and configure:

**Required Variables:**
- `DJANGO_SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Your domain
- `MONGO_ROOT_PASSWORD` - MongoDB password
- `REDIS_PASSWORD` - Redis password
- `ENCRYPTION_KEY` - Fernet encryption key for sensitive data
- `JWT_SECRET_KEY` - JWT signing secret
- `CORS_ALLOWED_ORIGINS` - Frontend URL
- `CSRF_TRUSTED_ORIGINS` - Frontend URL

**Generate secrets:**
```bash
# Django secret
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Passwords
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 🐳 Docker Architecture

**6 Containers:**
1. **mongodb** - Database
2. **redis** - Cache & message broker
3. **django** - Backend API
4. **celery_worker** - Background tasks
5. **celery_beat** - Scheduled tasks
6. **frontend** - Nginx serving React app

**Pre-built Images:**
- Backend: `ghcr.io/jitension/portfolio-backend:latest`
- Frontend: `ghcr.io/jitension/portfolio-frontend:latest`

**CI/CD:** GitHub Actions automatically builds and pushes images on every commit to main.

## 🔄 Updates

```bash
cd portfolio
git pull
docker-compose pull
docker-compose up -d
```

**Update time: ~30 seconds**

## 🌐 API Endpoints

- `/api/v1/auth/` - Authentication
- `/api/v1/portfolio/` - Portfolio data
- `/api/v1/holdings/` - Holdings management
- `/api/v1/robinhood/` - Robinhood integration
- `/api/v1/health/` - Health check
- `/admin/` - Django admin panel

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Full deployment instructions
- [Backend README](backend/README.md) - Backend development guide
- [Frontend README](frontend/README.md) - Frontend development guide

## 🛠️ Utility Scripts

Located in `scripts/`:
- `backup.sh` - Database backup utility
- `health-check.sh` - System health monitoring
- `test-local.sh` - Local testing helper

## 🔐 Security

- All sensitive data encrypted with Fernet
- HTTPS enforcement in production
- CORS and CSRF protection
- Secure cookie settings
- Non-root Docker containers
- MongoDB and Redis not exposed externally

## 📊 Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f django
docker-compose logs -f frontend

# Check container status
docker-compose ps

# Health check
curl http://localhost:8000/api/v1/health/
```

## 🎯 Access

After deployment:
- **Application:** `https://your-domain.synology.me`
- **Admin Panel:** `https://your-domain.synology.me/admin`

## 📝 License

Private Project

---

**Ready to deploy?** Check out the [Deployment Guide](docs/DEPLOYMENT.md)
