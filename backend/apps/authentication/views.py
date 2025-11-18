"""
DRF Views for authentication and user management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
import logging

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer,
)

User = get_user_model()
logger = logging.getLogger('apps')
security_logger = logging.getLogger('security')


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view that includes user data in response."""
    serializer_class = CustomTokenObtainPairSerializer


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user authentication operations.
    
    Provides endpoints for:
    - User registration
    - Logout (token blacklisting)
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """
        Register a new user.
        
        POST /api/v1/auth/register
        {
            "username": "john_investor",
            "email": "john@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        """
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Log successful registration
            logger.info(
                f"New user registered: {user.email}",
                extra={'user_id': user.id}
            )
            
            return Response({
                'success': True,
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': {
                'code': 'VAL_001',
                'message': 'Validation failed',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user by blacklisting the refresh token.
        
        POST /api/v1/auth/logout
        {
            "refresh": "refresh_token_here"
        }
        """
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VAL_002',
                        'message': 'Refresh token is required',
                        'details': {}
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log logout
            logger.info(
                f"User logged out: {request.user.email}",
                extra={'user_id': request.user.id}
            )
            
            return Response({
                'success': True,
                'data': {
                    'message': 'Logged out successfully'
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'AUTH_002',
                    'message': 'Token is invalid or expired',
                    'details': {'detail': str(e)}
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user profile management.
    
    Provides endpoints for:
    - Get current user profile
    - Update user profile
    - Change password
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only access their own profile."""
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """
        Get current user profile.
        
        GET /api/v1/auth/me
        """
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['put', 'patch'], url_path='me/update')
    def update_profile(self, request):
        """
        Update current user profile.
        
        PUT/PATCH /api/v1/auth/me/update
        {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "settings": {...}
        }
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            
            logger.info(
                f"User profile updated: {request.user.email}",
                extra={'user_id': request.user.id}
            )
            
            return Response({
                'success': True,
                'data': UserSerializer(request.user).data
            })
        
        return Response({
            'success': False,
            'error': {
                'code': 'VAL_001',
                'message': 'Validation failed',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        """
        Change user password.
        
        POST /api/v1/auth/me/change-password
        {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!"
        }
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            # Log password change
            security_logger.info(
                f"Password changed: {request.user.email}",
                extra={'user_id': request.user.id}
            )
            
            return Response({
                'success': True,
                'data': {
                    'message': 'Password changed successfully'
                }
            })
        
        return Response({
            'success': False,
            'error': {
                'code': 'VAL_001',
                'message': 'Validation failed',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)


class HealthCheckViewSet(viewsets.GenericViewSet):
    """Simple health check endpoint."""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        Health check endpoint.
        
        GET /api/v1/auth/health
        """
        return Response({
            'status': 'healthy',
            'service': 'portfolio-tracker-api',
            'version': '1.0.0'
        })
