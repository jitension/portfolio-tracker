"""
Custom exception handlers and exceptions for Portfolio Performance Tracker.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('apps')
security_logger = logging.getLogger('security')


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides consistent error responses.
    
    Returns responses in the format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {...}
        }
    }
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': {
                'code': get_error_code(exc),
                'message': get_error_message(exc, response.data),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        
        response.data = custom_response_data
        
        # Log the error
        log_exception(exc, context, response.status_code)
    
    else:
        # Handle non-DRF exceptions
        custom_response_data = {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An internal server error occurred.',
                'details': {'detail': str(exc)}
            }
        }
        
        response = Response(
            custom_response_data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        # Log the exception
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={'context': context}
        )
    
    return response


def get_error_code(exc) -> str:
    """Get appropriate error code based on exception type."""
    exc_class = exc.__class__.__name__
    
    error_code_map = {
        'NotAuthenticated': 'AUTH_001',
        'AuthenticationFailed': 'AUTH_001',
        'PermissionDenied': 'AUTH_003',
        'NotFound': 'RES_001',
        'ValidationError': 'VAL_001',
        'ParseError': 'VAL_002',
        'MethodNotAllowed': 'REQ_001',
        'Throttled': 'RATE_LIMIT',
    }
    
    return error_code_map.get(exc_class, 'UNKNOWN_ERROR')


def get_error_message(exc, response_data) -> str:
    """Extract human-readable error message from exception."""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail
        elif isinstance(exc.detail, dict):
            # Get first error message
            for key, value in exc.detail.items():
                if isinstance(value, list) and value:
                    return f"{key}: {value[0]}"
                return f"{key}: {value}"
    
    return str(exc)


def log_exception(exc, context, status_code):
    """Log exceptions for monitoring and debugging."""
    view = context.get('view')
    request = context.get('request')
    
    log_data = {
        'exception': exc.__class__.__name__,
        'status_code': status_code,
        'view': view.__class__.__name__ if view else 'Unknown',
        'path': request.path if request else 'Unknown',
        'method': request.method if request else 'Unknown',
        'user': str(request.user) if request and hasattr(request, 'user') else 'Anonymous',
    }
    
    # Log based on status code
    if status_code >= 500:
        logger.error(f"Server error: {exc}", extra=log_data, exc_info=True)
    elif status_code >= 400:
        if status_code == 401 or status_code == 403:
            security_logger.warning(f"Auth error: {exc}", extra=log_data)
        else:
            logger.warning(f"Client error: {exc}", extra=log_data)


# Custom Exceptions

class RobinhoodAPIError(Exception):
    """Raised when there's an error communicating with Robinhood API."""
    pass


class CredentialDecryptionError(Exception):
    """Raised when credentials cannot be decrypted."""
    pass


class SyncInProgressError(Exception):
    """Raised when a sync is already in progress for a user."""
    pass


class MFARequiredError(Exception):
    """Raised when MFA code is required but not provided."""
    pass


class PortfolioSyncError(Exception):
    """Raised when portfolio data synchronization fails."""
    pass
