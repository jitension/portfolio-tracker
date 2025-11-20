#!/usr/bin/env python
"""Script to create a superuser for the Django application."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = '***'
password = '***'

if User.objects.filter(email=email).exists():
    print(f'✅ Superuser with email {email} already exists.')
else:
    User.objects.create_superuser(email=email, password=password)
    print(f'✅ Superuser created successfully with email: {email}')
