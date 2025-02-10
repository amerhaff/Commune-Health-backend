from functools import wraps
from .services import AuditService
from django.utils.decorators import method_decorator

def audit_action(action_type: str):
    def decorator(func):
        @wraps(func)
        def wrapped_func(view_func, *args, **kwargs):
            request = args[0]
            try:
                result = func(view_func, *args, **kwargs)
                
                # Log successful action
                AuditService.log_action(
                    user=request.user,
                    action=action_type,
                    request=request,
                    target_object=getattr(view_func, 'get_object', lambda: None)(),
                    details={'method': request.method, 'path': request.path}
                )
                
                return result
            except Exception as e:
                # Log failed action
                AuditService.log_action(
                    user=request.user,
                    action=action_type,
                    request=request,
                    status='ERROR',
                    error_message=str(e),
                    details={'method': request.method, 'path': request.path}
                )
                raise
                
        return wrapped_func
    return decorator

def audit_security(severity='INFO'):
    def decorator(func):
        @wraps(func)
        def wrapped_func(view_func, *args, **kwargs):
            request = args[0]
            try:
                result = func(view_func, *args, **kwargs)
                return result
            except Exception as e:
                # Log security event
                AuditService.log_security_event(
                    action='PERMISSION_DENIED',
                    request=request,
                    user=request.user if hasattr(request, 'user') else None,
                    details={'error': str(e)},
                    severity=severity
                )
                raise
                
        return wrapped_func
    return decorator 