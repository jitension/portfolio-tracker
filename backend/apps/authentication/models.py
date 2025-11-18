"""
User models for Portfolio Performance Tracker.
Custom User model with additional fields for portfolio tracking.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for the User model."""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for Portfolio Performance Tracker.
    
    Extends Django's AbstractUser with additional fields for portfolio tracking.
    Uses email as the unique identifier instead of username.
    """
    
    # Override email to make it required and unique
    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        }
    )
    
    # Additional user fields
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # User preferences stored as JSON
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='User preferences and settings'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Use email for authentication
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username
    
    @property
    def default_settings(self):
        """Return default user settings."""
        return {
            'theme': 'dark',
            'default_view': 'dashboard',
            'notifications_enabled': True,
            'timezone': 'America/New_York',
            'currency': 'USD',
            'date_format': 'MM/DD/YYYY',
        }
    
    def initialize_settings(self):
        """Initialize user settings with defaults if not set."""
        if not self.settings:
            self.settings = self.default_settings
            self.save()
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
