#!/bin/bash
set -e

echo "🚀 Starting Django container..."

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB..."
until python -c "import mongoengine; mongoengine.connect(host='${MONGODB_URI}')" 2>/dev/null; do
  echo "MongoDB is unavailable - sleeping"
  sleep 2
done
echo "✅ MongoDB is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until python -c "import redis; r=redis.from_url('${REDIS_URL}'); r.ping()" 2>/dev/null; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done
echo "✅ Redis is ready!"

# Run migrations for Django's internal tables (admin, sessions, celery_beat, etc.)
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (only for Django container)
if [ "${COLLECT_STATIC}" = "true" ]; then
  echo "📦 Collecting static files..."
  python manage.py collectstatic --noinput --clear
fi

echo "✅ Initialization complete!"

# Execute the main command
exec "$@"
