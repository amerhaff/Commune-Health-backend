from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    User = get_user_model()
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'status': 'success',
            'user_id': user.id,
            'user_type': user.user_type
        })
    return Response(serializer.errors, status=400) 