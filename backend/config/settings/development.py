"""
Development settings for Portfolio Performance Tracker.
"""
from .base import *

# Debug mode enabled for development
DEBUG = True

# Allowed hosts for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# MongoEngine settings for development
import mongoengine

MONGODB_SETTINGS = {
    'db': 'portfolio_dev',
    'host': os.environ.get('MONGODB_URI', 'mongodb://mongodb:27017/portfolio_dev'),
    'connect': False,
}

# Reconnect with development settings
mongoengine.connection.disconnect()
mongoengine.connect(**MONGODB_SETTINGS)

# CORS - allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (if needed)
INSTALLED_APPS += [
    'django_extensions',
    # 'debug_toolbar',  # Uncomment if you want to use it
]

# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Internal IPs for debug toolbar
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery - eager mode for development (tasks run synchronously)
# Uncomment to test actual async behavior
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True

# Logging - more verbose in development
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# DRF - Add browsable API renderer in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # For easy API testing
]

# Cache - use dummy cache for development (or use Redis if available)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }

print(f"🚀 Running in DEVELOPMENT mode")
print(f"📊 MongoDB: {MONGODB_SETTINGS['host']}")
print(f"🔴 Redis: {CELERY_BROKER_URL}")
