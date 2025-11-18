"""
Robinhood Account models using MongoEngine.
Stores encrypted Robinhood credentials and account metadata.
"""
from mongoengine import Document, fields, signals
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

logger = logging.getLogger('apps')

User = get_user_model()


class RobinhoodAccount(Document):
    """
    MongoEngine Document for storing Robinhood account information.
    
    Credentials are encrypted using AES-256 before storage.
    """
    
    # Reference to Django User
    user_id = fields.IntField(required=True)
    
    # Account Information
    account_number = fields.StringField(required=True, unique=True)
    account_type = fields.StringField(choices=['cash', 'margin', 'gold'], default='cash')
    
    # Encrypted Credentials
    credentials_encrypted = fields.StringField(required=True)
    
    # Token Storage (for persistent sessions)
    auth_token_encrypted = fields.StringField()
    token_expires_at = fields.DateTimeField()
    refresh_token_encrypted = fields.StringField()
    
    # Multi-Factor Authentication
    mfa_enabled = fields.BooleanField(default=False)
    mfa_type = fields.StringField(choices=['sms', 'app'], default='sms')
    
    # Sync Status
    last_sync = fields.DateTimeField()
    sync_status = fields.StringField(
        choices=['never_synced', 'success', 'pending', 'failed'],
        default='never_synced'
    )
    sync_error = fields.StringField()
    
    # Account Status
    is_active = fields.BooleanField(default=True)
    is_verified = fields.BooleanField(default=False)
    
    # Metadata
    created_at = fields.DateTimeField(default=timezone.now)
    updated_at = fields.DateTimeField(default=timezone.now)
    
    # Database configuration
    meta = {
        'collection': 'robinhood_accounts',
        'indexes': [
            'user_id',
            'account_number',
            {'fields': ['user_id', 'is_active']},
            '-created_at',
        ],
        'ordering': ['-created_at']
    }
    
    def __str__(self):
        return f"RobinhoodAccount({self.account_number}) - User ID: {self.user_id}"
    
    def clean(self):
        """Validate before saving."""
        if not self.credentials_encrypted:
            raise ValueError("Credentials must be encrypted before saving")
        
        # Update timestamp
        self.updated_at = timezone.now()
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation."""
        self.clean()
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_user_accounts(cls, user):
        """Get all active Robinhood accounts for a user."""
        return cls.objects(user_id=user.id, is_active=True)
    
    @classmethod
    def get_account_by_number(cls, account_number):
        """Get account by account number."""
        return cls.objects(account_number=account_number).first()
    
    def update_sync_status(self, status, error=None):
        """Update sync status and timestamp."""
        self.sync_status = status
        self.last_sync = timezone.now()
        if error:
            self.sync_error = str(error)
        else:
            self.sync_error = None
        self.save()
        
        logger.info(
            f"Sync status updated for account {self.account_number}: {status}",
            extra={'user_id': self.user_id, 'account_id': str(self.id)}
        )
    
    def deactivate(self):
        """Deactivate the account (soft delete)."""
        self.is_active = False
        self.save()
        
        logger.info(
            f"Robinhood account deactivated: {self.account_number}",
            extra={'user_id': self.user_id}
        )
