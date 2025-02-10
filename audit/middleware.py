from .services import AuditService

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pre-processing
        if hasattr(request, 'user') and request.user.is_authenticated:
            AuditService.log_action(
                user=request.user,
                action='ACCESS',
                request=request,
                details={
                    'method': request.method,
                    'path': request.path,
                }
            )

        response = self.get_response(request)

        # Post-processing
        if response.status_code >= 400:
            AuditService.log_security_event(
                action='PERMISSION_DENIED' if response.status_code == 403 else 'ERROR',
                request=request,
                user=request.user if hasattr(request, 'user') else None,
                details={
                    'status_code': response.status_code,
                    'method': request.method,
                    'path': request.path,
                },
                severity='HIGH' if response.status_code in [401, 403] else 'MEDIUM'
            )

        return response 