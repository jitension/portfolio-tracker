# 🚀 Deployment Guide

Simple 3-step deployment to your Synology NAS using Docker pre-built images.

---

## Prerequisites

- Synology NAS with Docker installed
- SSH access enabled
- Domain configured (e.g., `portfolio.yourdomain.synology.me`)
- GitHub Personal Access Token with `read:packages` permission (for private repos)

---

## Step 1: One-Time Setup (Login to GitHub Container Registry)

```bash
# On your NAS, login to pull private Docker images
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u jitension --password-stdin
```

> **Note:** If your images are public, you can skip this step.

---

## Step 2: Clone & Configure

```bash
# Clone the repository
git clone https://github.com/jitension/portfolio.git
cd portfolio

# Copy and edit environment variables
cp .env.example .env
nano .env
```

**Edit `.env` file with your values:**
- `DJANGO_SECRET_KEY` - Generate a random secret
- `ALLOWED_HOSTS` - Your domain
- `CORS_ALLOWED_ORIGINS` - Your https domain
- `CSRF_TRUSTED_ORIGINS` - Your https domain
- `MONGO_ROOT_PASSWORD` - Strong password for MongoDB
- `REDIS_PASSWORD` - Strong password for Redis
- `ENCRYPTION_KEY` - Fernet encryption key
- `JWT_SECRET_KEY` - JWT signing secret

**Generate secrets with Python:**
```bash
# Django secret
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# MongoDB/Redis passwords
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Step 3: Deploy

```bash
# Pull latest images and start all containers
docker-compose pull
docker-compose up -d

# Wait a moment for services to start, then create admin user (first time only)
docker-compose exec django python manage.py createsuperuser
```

**That's it!** Your app is now running.

---

## Step 4: Configure Reverse Proxy

In Synology DSM:
1. Go to **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Click **Create** and configure:
   - **Source:**
     - Protocol: `HTTPS`
     - Hostname: `portfolio.yourdomain.synology.me`
     - Port: `443`
   - **Destination:**
     - Protocol: `HTTP`
     - Hostname: `localhost`
     - Port: `3001`
3. Click **Save**

---

## Access Your Application

- **Application:** `https://portfolio.yourdomain.synology.me`
- **Admin Panel:** `https://portfolio.yourdomain.synology.me/admin`

---

## Updates

When new versions are released:

```bash
cd portfolio
git pull
docker-compose pull
docker-compose up -d
```

**Update time: ~30 seconds!**

---

## Useful Commands

### View logs
```bash
docker-compose logs -f
```

### View specific service logs
```bash
docker-compose logs -f django
docker-compose logs -f frontend
```

### Check container status
```bash
docker-compose ps
```

### Restart services
```bash
docker-compose restart
```

### Stop all services
```bash
docker-compose down
```

### Full cleanup (removes volumes too)
```bash
docker-compose down -v
```

---

## Troubleshooting

### Containers won't start
```bash
# Check logs
docker-compose logs

# Verify environment variables
cat .env

# Check if ports are available
sudo netstat -tulpn | grep -E '3001|8000|27017|6379'
```

### Login not working (502 error)
- Verify all containers are running: `docker-compose ps`
- Check nginx logs: `docker-compose logs frontend`
- Verify reverse proxy configuration in DSM

### Database connection issues
- Check MongoDB logs: `docker-compose logs mongodb`
- Verify MongoDB password in `.env` matches docker-compose.yml

### Need to reset everything
```bash
docker-compose down -v
rm -rf .env
cp .env.example .env
nano .env
docker-compose up -d
docker-compose exec django python manage.py createsuperuser
```

---

## Architecture

Your deployment consists of 6 Docker containers:

1. **mongodb** - Database (port 27017, internal only)
2. **redis** - Cache & message broker (port 6379, internal only)
3. **django** - Backend API (port 8000, internal only)
4. **celery_worker** - Background tasks
5. **celery_beat** - Scheduled tasks
6. **frontend** - Nginx serving React app (port 3001, exposed)

All containers communicate via the `portfolio_network` bridge network.

---

## Security Notes

- All services use strong passwords defined in `.env`
- Frontend enforces HTTPS when behind reverse proxy
- MongoDB and Redis are not exposed to external network
- Only frontend (port 3001) is accessible from outside
- Django runs with non-root user
- Static files served by Nginx (not Django)

---

**Need help?** Check the logs first: `docker-compose logs -f`
