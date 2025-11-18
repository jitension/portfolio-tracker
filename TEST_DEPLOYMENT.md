# 🧪 Test Deployment on NAS

Quick test guide to verify the simplified docker-compose workflow works correctly.

---

## Test Checklist

### 1. Clean Slate Test (Recommended)

SSH into your NAS and test from scratch:

```bash
# Remove old deployment
cd /volume1/docker/portfolio
docker-compose down -v
cd ..
rm -rf portfolio

# Test new deployment (the 3-step way)
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u jitension --password-stdin
git clone https://github.com/jitension/portfolio-tracker.git
cd portfolio
cp .env.example .env
nano .env  # Fill in your values

# Deploy
docker-compose pull
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Check all containers are running
docker-compose ps
# Should see 6 containers: mongodb, redis, django, celery_worker, celery_beat, frontend

# Check logs for any errors
docker-compose logs django
docker-compose logs frontend

# Create superuser
docker-compose exec django python manage.py createsuperuser
```

### 2. Verify Network Connectivity

```bash
# All containers should be on portfolio_network
docker network inspect portfolio_network

# Django should be able to reach MongoDB
docker-compose exec django python -c "import mongoengine; mongoengine.connect(host='mongodb://admin:YOUR_MONGO_PASSWORD@mongodb:27017/portfolio?authSource=admin'); print('✅ MongoDB connected')"

# Django should be able to reach Redis
docker-compose exec django python -c "import redis; r=redis.from_url('redis://:YOUR_REDIS_PASSWORD@redis:6379/0'); r.ping(); print('✅ Redis connected')"
```

### 3. Test Login

1. Open browser: `https://portfolio.jitension.synology.me`
2. Login with your superuser credentials
3. Should see dashboard (not 502 error)

### 4. Test Update Workflow

```bash
# Simulate an update
cd /volume1/docker/portfolio
git pull
docker-compose pull
docker-compose up -d

# Should complete in ~30 seconds
```

---

## Expected Results

✅ **All 6 containers running**
```
portfolio_mongodb       Up
portfolio_redis         Up  
portfolio_django        Up (healthy)
portfolio_celery_worker Up
portfolio_celery_beat   Up
portfolio_frontend      Up (healthy)
```

✅ **Network check shows all containers on `portfolio_network`**

✅ **Django can connect to MongoDB and Redis**

✅ **Login works without 502 errors**

✅ **Update completes in ~30 seconds**

---

## If Something Fails

### Containers not starting
```bash
docker-compose logs
```

### 502 Error on login
```bash
docker-compose logs frontend
docker-compose logs django
docker-compose ps  # Check if all containers are Up
```

### Network issues
```bash
docker-compose down
docker-compose up -d  # Recreate with proper network
```

---

## Success Criteria

- ✅ Deployment takes 5 minutes max (not 30+ minutes)
- ✅ No git needed on NAS (uses pre-built images)
- ✅ Standard `docker-compose` commands work
- ✅ All containers on same network
- ✅ Login functionality works
- ✅ Updates take ~30 seconds

---

**If all tests pass, the simplification is complete! 🎉**
