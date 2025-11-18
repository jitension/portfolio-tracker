"""
DRF Serializers for Robinhood integration.
"""
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import RobinhoodAccount
from core.encryption import encrypt_credentials
import logging

logger = logging.getLogger('apps')


class RobinhoodAccountSerializer(serializers.Serializer):
    """
    Serializer for RobinhoodAccount MongoEngine Document.
    
    Note: Since we're using MongoEngine, we can't use ModelSerializer.
    We define fields manually and handle save/update logic.
    """
    
    id = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    account_number = serializers.CharField(read_only=True)
    account_type = serializers.ChoiceField(
        choices=['cash', 'margin', 'gold'],
        read_only=True
    )
    mfa_enabled = serializers.BooleanField(read_only=True)
    mfa_type = serializers.ChoiceField(
        choices=['sms', 'app'],
        read_only=True
    )
    last_sync = serializers.DateTimeField(read_only=True)
    sync_status = serializers.ChoiceField(
        choices=['never_synced', 'success', 'pending', 'failed'],
        read_only=True
    )
    sync_error = serializers.CharField(read_only=True, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def to_representation(self, instance):
        """Convert MongoEngine Document to dict."""
        return {
            'id': str(instance.id),
            'user_id': instance.user_id,
            'account_number': instance.account_number,
            'account_type': instance.account_type,
            'mfa_enabled': instance.mfa_enabled,
            'mfa_type': instance.mfa_type,
            'last_sync': instance.last_sync,
            'sync_status': instance.sync_status,
            'sync_error': instance.sync_error,
            'is_active': instance.is_active,
            'is_verified': instance.is_verified,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class LinkRobinhoodAccountSerializer(serializers.Serializer):
    """
    Serializer for linking a new Robinhood account.
    
    Handles credential encryption and account creation.
    """
    
    username = serializers.EmailField(
        required=True,
        help_text="Robinhood email address"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Robinhood password"
    )
    mfa_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=6,
        min_length=6,
        help_text="6-digit 2FA code (required if MFA is enabled)"
    )
    mfa_type = serializers.ChoiceField(
        choices=['sms', 'app'],
        default='sms',
        required=False,
        help_text="2FA delivery method"
    )
    
    def validate_mfa_code(self, value):
        """Validate MFA code format."""
        if value and not value.isdigit():
            raise ValidationError("MFA code must be 6 digits")
        return value
    
    def create(self, validated_data):
        """
        Create a new RobinhoodAccount after validating credentials.
        
        This method is called from the view after Robinhood authentication succeeds.
        """
        user = self.context['request'].user
        username = validated_data['username']
        password = validated_data['password']
        mfa_type = validated_data.get('mfa_type', 'sms')
        
        # Encrypt credentials
        try:
            credentials_encrypted = encrypt_credentials(username, password)
        except Exception as e:
            logger.error(f"Credential encryption failed: {str(e)}")
            raise ValidationError("Failed to encrypt credentials")
        
        # Account number will be set by the view after successful authentication
        account_number = self.context.get('account_number', 'PENDING')
        
        # Create RobinhoodAccount document
        account = RobinhoodAccount(
            user_id=user.id,
            account_number=account_number,
            credentials_encrypted=credentials_encrypted,
            mfa_enabled=bool(validated_data.get('mfa_code')),
            mfa_type=mfa_type,
            is_verified=True,  # Verified through successful auth
        )
        
        account.save()
        
        logger.info(
            f"Robinhood account linked: {account_number}",
            extra={'user_id': user.id, 'account_id': str(account.id)}
        )
        
        return account


class TestConnectionSerializer(serializers.Serializer):
    """Serializer for testing Robinhood account connection."""
    
    mfa_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=6,
        min_length=6,
        help_text="6-digit 2FA code"
    )
    
    def validate_mfa_code(self, value):
        """Validate MFA code format."""
        if value and not value.isdigit():
            raise ValidationError("MFA code must be 6 digits")
        return value
