"""
DRF Views for Robinhood integration.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from .models import RobinhoodAccount
from .serializers import (
    RobinhoodAccountSerializer,
    LinkRobinhoodAccountSerializer,
    TestConnectionSerializer
)
from .client import RobinhoodClient
from core.exceptions import (
    RobinhoodAPIError,
    MFARequiredError,
    CredentialDecryptionError
)

logger = logging.getLogger('apps')
security_logger = logging.getLogger('security')


class RobinhoodAccountViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing Robinhood account connections.
    
    Provides endpoints for:
    - Linking Robinhood accounts (with 2FA)
    - Listing linked accounts
    - Testing connections
    - Unlinking accounts
    """
    
    serializer_class = RobinhoodAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own Robinhood accounts."""
        return RobinhoodAccount.get_user_accounts(self.request.user)
    
    @action(detail=False, methods=['post'], url_path='link-account')
    def link_account(self, request):
        """
        Link a new Robinhood account.
        
        POST /api/v1/robinhood/link-account/
        {
            "username": "your-robinhood-email@example.com",
            "password": "your-robinhood-password",
            "mfa_code": "123456",  // Required if 2FA is enabled
            "mfa_type": "sms"      // or "app"
        }
        
        Returns:
            Account details if successful
            MFA requirement if 2FA code needed
            Error if credentials invalid
        """
        serializer = LinkRobinhoodAccountSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VAL_001',
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        mfa_code = serializer.validated_data.get('mfa_code')
        
        try:
            # Attempt authentication with Robinhood
            client = RobinhoodClient()
            auth_result = client.authenticate(
                username=username,
                password=password,
                mfa_code=mfa_code
            )
            
            # Get account information
            account_info = client.get_account_info()
            account_number = account_info.get('account_number', 'UNKNOWN')
            
            # Don't logout - keep session active for subsequent API calls
            # Robin-stocks will handle session caching automatically
            
            # Check if account already linked (only check active accounts)
            existing = RobinhoodAccount.objects(
                account_number=account_number,
                is_active=True
            ).first()
            
            if existing and existing.user_id == request.user.id:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'RES_002',
                        'message': 'This Robinhood account is already linked',
                        'details': {'account_number': account_number}
                    }
                }, status=status.HTTP_409_CONFLICT)
            
            # Create account
            serializer.context['account_number'] = account_number
            account = serializer.save()
            
            # Log successful linking
            security_logger.info(
                f"Robinhood account linked: {account_number}",
                extra={'user_id': request.user.id, 'account_id': str(account.id)}
            )
            
            return Response({
                'success': True,
                'data': {
                    'account': RobinhoodAccountSerializer(account).data,
                    'message': 'Robinhood account linked successfully'
                }
            }, status=status.HTTP_201_CREATED)
        
        except MFARequiredError as e:
            security_logger.warning(
                f"MFA required for account linking: {username}",
                extra={'user_id': request.user.id}
            )
            
            return Response({
                'success': False,
                'error': {
                    'code': 'AUTH_004',
                    'message': '2FA code is required',
                    'details': {
                        'mfa_required': True,
                        'mfa_type': request.data.get('mfa_type', 'sms')
                    }
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except RobinhoodAPIError as e:
            logger.error(
                f"Robinhood API error during linking: {str(e)}",
                extra={'user_id': request.user.id}
            )
            
            return Response({
                'success': False,
                'error': {
                    'code': 'SYNC_003',
                    'message': 'Failed to connect to Robinhood',
                    'details': {'error': str(e)}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(
                f"Unexpected error during account linking: {str(e)}",
                exc_info=True,
                extra={'user_id': request.user.id}
            )
            
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': {'error': str(e)}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def list(self, request):
        """
        List all linked Robinhood accounts for current user.
        
        GET /api/v1/robinhood/accounts/
        """
        accounts = self.get_queryset()
        serializer = RobinhoodAccountSerializer(accounts, many=True)
        
        return Response({
            'success': True,
            'data': {
                'accounts': serializer.data,
                'count': len(serializer.data)
            }
        })
    
    def retrieve(self, request, pk=None):
        """
        Get details of a specific Robinhood account.
        
        GET /api/v1/robinhood/accounts/:id/
        """
        try:
            account = RobinhoodAccount.objects(id=pk, user_id=request.user.id).first()
            
            if not account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'RES_001',
                        'message': 'Account not found',
                        'details': {}
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = RobinhoodAccountSerializer(account)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Error retrieving account: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve account',
                    'details': {'error': str(e)}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """
        Unlink and delete a Robinhood account along with all related data.
        
        DELETE /api/v1/robinhood/accounts/:id/
        
        This will permanently delete:
        - The Robinhood account
        - All holdings
        - All portfolio snapshots
        - Portfolio data
        """
        try:
            account = RobinhoodAccount.objects(id=pk, user_id=request.user.id).first()
            
            if not account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'RES_001',
                        'message': 'Account not found',
                        'details': {}
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Delete account and all related data (hard delete)
            deleted_counts = account.delete_with_related_data()
            
            security_logger.info(
                f"Robinhood account deleted by user {request.user.id}",
                extra={
                    'user_id': request.user.id,
                    'deleted_counts': deleted_counts
                }
            )
            
            return Response({
                'success': True,
                'data': {
                    'message': 'Robinhood account and all related data unlinked successfully',
                    'deleted': deleted_counts
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error unlinking account: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to unlink account',
                    'details': {'error': str(e)}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='test-connection')
    def test_connection(self, request, pk=None):
        """
        Test if Robinhood account credentials are still valid.
        
        POST /api/v1/robinhood/accounts/:id/test-connection/
        {
            "mfa_code": "123456"  // Required if 2FA enabled
        }
        """
        try:
            account = RobinhoodAccount.objects(id=pk, user_id=request.user.id).first()
            
            if not account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'RES_001',
                        'message': 'Account not found',
                        'details': {}
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = TestConnectionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VAL_001',
                        'message': 'Validation failed',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            mfa_code = serializer.validated_data.get('mfa_code')
            
            # Test connection
            client = RobinhoodClient(account)
            connection_valid = client.test_connection(mfa_code=mfa_code)
            
            if connection_valid:
                account.update_sync_status('success')
                
                return Response({
                    'success': True,
                    'data': {
                        'connection_valid': True,
                        'message': 'Connection test successful',
                        'tested_at': timezone.now()
                    }
                })
            else:
                account.update_sync_status('failed', 'Connection test failed')
                
                return Response({
                    'success': False,
                    'error': {
                        'code': 'SYNC_002',
                        'message': 'Connection test failed',
                        'details': {
                            'connection_valid': False,
                            'suggestion': 'Check credentials or provide MFA code'
                        }
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except MFARequiredError:
            return Response({
                'success': False,
                'error': {
                    'code': 'AUTH_004',
                    'message': '2FA code is required',
                    'details': {'mfa_required': True}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Connection test failed',
                    'details': {'error': str(e)}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
