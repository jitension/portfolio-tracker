"""
DRF Serializers for authentication.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'settings',
            'created_at',
            'last_login',
            'is_active',
        ]
        read_only_fields = ['id', 'created_at', 'last_login']
    
    def to_representation(self, instance):
        """Customize the serialized output."""
        data = super().to_representation(instance)
        # Ensure settings has default values
        if not data.get('settings'):
            data['settings'] = instance.default_settings
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
        ]
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Password fields didn\'t match.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        
        # Initialize default settings
        user.initialize_settings()
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that adds user data to token response."""
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to token."""
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        
        return token
    
    def validate(self, attrs):
        """Add user data to response."""
        data = super().validate(attrs)
        
        # Update last login
        self.user.update_last_login()
        
        # Add user data to response
        data['user'] = UserSerializer(self.user).data
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate passwords."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password': 'Password fields didn\'t match.'
            })
        return attrs
    
    def validate_old_password(self, value):
        """Validate that old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'settings',
        ]
    
    def validate_settings(self, value):
        """Validate settings dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Settings must be a dictionary')
        return value
