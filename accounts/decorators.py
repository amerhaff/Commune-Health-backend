from functools import wraps
from django.http import HttpResponseForbidden
from rest_framework.response import Response
from rest_framework import status

def require_user_type(*allowed_types):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if request.user.user_type not in allowed_types:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def require_object_ownership():
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            obj = view_func.get_object()
            if not hasattr(obj, 'user'):
                return Response(
                    {'error': 'Object ownership cannot be verified'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            if obj.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator 