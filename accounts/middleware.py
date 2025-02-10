from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Decode the JWT token
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=['HS256']
                )
                User = get_user_model()
                request.user = User.objects.get(id=payload['user_id'])
            except (jwt.InvalidTokenError, User.DoesNotExist):
                return JsonResponse(
                    {'error': 'Invalid token'}, 
                    status=401
                )
                
        return self.get_response(request) 