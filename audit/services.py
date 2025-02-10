from .models import AuditLog, SecurityAuditLog
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from typing import Optional, Any, Dict

class AuditService:
    @staticmethod
    def log_action(
        user,
        action: str,
        details: Dict[str, Any] = None,
        request = None,
        target_object = None,
        status: str = 'SUCCESS',
        error_message: str = None
    ) -> AuditLog:
        """Log an action in the system"""
        
        audit_log = AuditLog(
            user=user,
            action=action,
            user_type=getattr(user, 'user_type', 'ANONYMOUS'),
            details=details or {},
            status=status,
            error_message=error_message
        )

        if request:
            audit_log.ip_address = request.META.get('REMOTE_ADDR')
            audit_log.user_agent = request.META.get('HTTP_USER_AGENT')

        if target_object:
            audit_log.content_type = ContentType.objects.get_for_model(target_object)
            audit_log.object_id = target_object.id

        audit_log.save()
        return audit_log

    @staticmethod
    def log_security_event(
        action: str,
        request,
        user = None,
        details: Dict[str, Any] = None,
        severity: str = 'INFO'
    ) -> SecurityAuditLog:
        """Log a security-related event"""
        
        security_log = SecurityAuditLog(
            action=action,
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details=details or {},
            severity=severity
        )
        security_log.save()
        return security_log 