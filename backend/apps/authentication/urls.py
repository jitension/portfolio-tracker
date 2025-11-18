"""
URL routing for authentication app.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    AuthViewSet,
    UserViewSet,
    HealthCheckViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register('', AuthViewSet, basename='auth')
router.register('user', UserViewSet, basename='user')
router.register('health', HealthCheckViewSet, basename='health')

# URL patterns
urlpatterns = [
    # JWT token endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Add router URLs
urlpatterns += router.urls
