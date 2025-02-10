from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
import logging
import time

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration': f'{duration:.2f}s',
                'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                'ip': request.META.get('REMOTE_ADDR'),
            }
            
            if response.status_code >= 400:
                logger.error(f'Request failed: {log_data}')
            else:
                logger.info(f'Request completed: {log_data}')
        return response

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip authentication for certain paths
        if request.path.startswith('/admin/') or \
           request.path.startswith('/api/token/') or \
           request.path.startswith('/api/accounts/register/') or \
           request.path.startswith('/api/accounts/password/reset/') or \
           request.path.startswith('/api/accounts/verify-email/') or \
           request.path.startswith('/api/health/'):
            return None

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Authentication credentials were not provided.'}, 
                status=401
            )

        try:
            token = auth_header.split(' ')[1]
            AccessToken(token)
        except (InvalidToken, TokenError, IndexError):
            return JsonResponse(
                {'error': 'Invalid or expired token.'}, 
                status=401
            )

class EmailVerificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip verification for certain paths
        if request.path.startswith('/admin/') or \
           request.path.startswith('/api/token/') or \
           request.path.startswith('/api/accounts/register/') or \
           request.path.startswith('/api/accounts/password/reset/') or \
           request.path.startswith('/api/accounts/verify-email/'):
            return None

        if hasattr(request, 'user') and request.user.is_authenticated:
            if not request.user.email_verified:
                return JsonResponse(
                    {'error': 'Please verify your email address.'}, 
                    status=403
                ) 