"""
Script to create placeholder app structures for Django apps.
This ensures Django can start while we develop features incrementally.
"""
import os
from pathlib import Path

# Define apps to create
APPS = [
    ('portfolio', 'Portfolio'),
    ('transactions', 'Transactions'),
    ('options', 'Options'),
    ('dividends', 'Dividends'),
    ('watchlists', 'Watchlists'),
    ('robinhood', 'Robinhood Integration'),
]

# Base directory
BASE_DIR = Path(__file__).parent / 'apps'

# Templates for files
APPS_PY_TEMPLATE = '''"""
{app_name} app configuration.
"""
from django.apps import AppConfig


class {class_name}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app_name}'
    verbose_name = '{verbose_name}'
'''

MODELS_PY_TEMPLATE = '''"""
{verbose_name} models - placeholder.
Will be implemented in later phases.
"""
from django.db import models

# TODO: Implement models in Phase 2+
'''

ADMIN_PY_TEMPLATE = '''"""
Admin configuration for {app_name} app.
"""
from django.contrib import admin

# TODO: Register models when implemented
'''

URLS_PY_TEMPLATE = '''"""
URL routing for {app_name} app.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    # TODO: Add URL patterns in later phases
]

urlpatterns += router.urls
'''

INIT_PY_TEMPLATE = '''"""
{verbose_name} app.
"""
default_app_config = 'apps.{app_name}.apps.{class_name}Config'
'''

def create_app_structure(app_name, verbose_name):
    """Create directory structure and files for an app."""
    app_dir = BASE_DIR / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert app_name to CamelCase for class name
    class_name = ''.join(word.capitalize() for word in app_name.split('_'))
    
    files = {
        '__init__.py': INIT_PY_TEMPLATE,
        'apps.py': APPS_PY_TEMPLATE,
        'models.py': MODELS_PY_TEMPLATE,
        'admin.py': ADMIN_PY_TEMPLATE,
        'urls.py': URLS_PY_TEMPLATE,
    }
    
    for filename, template in files.items():
        filepath = app_dir / filename
        content = template.format(
            app_name=app_name,
            verbose_name=verbose_name,
            class_name=class_name
        )
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Created: {filepath}")

if __name__ == '__main__':
    print("Creating placeholder app structures...")
    
    for app_name, verbose_name in APPS:
        if app_name == 'portfolio':
            # Portfolio already partially created, skip
            print(f"Skipping {app_name} (already exists)")
            continue
        
        print(f"\nCreating {app_name} app...")
        create_app_structure(app_name, verbose_name)
    
    print("\n✅ All placeholder apps created successfully!")
    print("These apps will be fully implemented in subsequent development phases.")
