from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ACCESS', 'Access'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('ROLE_CHANGE', 'Role Change'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    user_type = models.CharField(max_length=50)  # EMPLOYER, PROVIDER, BROKER, ADMIN
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(null=True)
    
    # For object-level tracking
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional details
    details = models.JSONField(default=dict)
    status = models.CharField(max_length=50, default='SUCCESS')
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp']),
            models.Index(fields=['user_type', 'action']),
        ]

class SecurityAuditLog(models.Model):
    ACTION_TYPES = [
        ('PERMISSION_DENIED', 'Permission Denied'),
        ('INVALID_TOKEN', 'Invalid Token'),
        ('SUSPICIOUS_ACCESS', 'Suspicious Access'),
        ('RATE_LIMIT_EXCEEDED', 'Rate Limit Exceeded'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('FAILED_LOGIN', 'Failed Login'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    details = models.JSONField(default=dict)
    severity = models.CharField(max_length=20, default='INFO') 