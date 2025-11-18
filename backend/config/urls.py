"""
URL configuration for Portfolio Performance Tracker.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from django.http import JsonResponse

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Application is running'
    })

# Create DRF router
router = routers.DefaultRouter()

# API URL patterns
api_v1_patterns = [
    path('health/', health_check, name='health-check'),
    path('auth/', include('apps.authentication.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('options/', include('apps.options.urls')),
    path('dividends/', include('apps.dividends.urls')),
    path('watchlists/', include('apps.watchlists.urls')),
    path('robinhood/', include('apps.robinhood.urls')),
]

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include(api_v1_patterns)),
    
    # DRF router (if needed for additional ViewSets)
    path('api/v1/', include(router.urls)),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar if installed
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Customize admin site
admin.site.site_header = 'Portfolio Performance Tracker Admin'
admin.site.site_title = 'Portfolio Admin'
admin.site.index_title = 'Administration'
