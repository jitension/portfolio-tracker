"""
Admin configuration for Robinhood app.
"""
from django.contrib import admin
from mongoengine import Document
from .models import RobinhoodAccount


class RobinhoodAccountAdmin:
    """
    Admin interface for RobinhoodAccount (MongoEngine Document).
    
    Note: MongoEngine documents can't use standard Django admin,
    but we can create a custom view or use a package like django-mongoengine.
    For now, we'll manage through the API and Django shell.
    """
    pass

# Note: To properly integrate MongoEngine with Django Admin,
# you would need django-mongoengine package. For now, accounts
# are managed through the API endpoints and can be viewed/edited
# via MongoDB Compass or Django shell.

# Future: Add django-mongoengine for better admin integration
