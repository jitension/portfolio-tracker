"""
robinhood app configuration.
"""
from django.apps import AppConfig


class RobinhoodConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.robinhood'
    verbose_name = 'Robinhood Integration'
