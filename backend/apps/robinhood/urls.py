"""
URL routing for Robinhood integration app.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RobinhoodAccountViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register('accounts', RobinhoodAccountViewSet, basename='robinhood-account')

urlpatterns = [
    # Link account endpoint (handled by ViewSet action)
    # POST /link-account/ -> RobinhoodAccountViewSet.link_account
]

# Add router URLs
urlpatterns += router.urls
