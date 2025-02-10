from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache
import psutil
import os

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    # Check database connection
    db_healthy = True
    try:
        connections['default'].cursor()
    except OperationalError:
        db_healthy = False

    # Check system resources
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    health_status = {
        'status': 'healthy' if db_healthy else 'unhealthy',
        'database': 'connected' if db_healthy else 'disconnected',
        'email_service': os.getenv('EMAIL_HOST_USER') is not None,
        'system': {
            'memory_used': f"{memory.percent}%",
            'disk_used': f"{disk.percent}%",
        }
    }

    if not db_healthy:
        return Response(health_status, status=503)  # Service Unavailable
    
    return Response(health_status) 