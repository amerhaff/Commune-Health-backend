from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserViewSet,
    ProviderViewSet,
    MDDOProviderViewSet,
    PAProviderViewSet,
    NPProviderViewSet,
    BrokerViewSet,
    EmployerViewSet,
    EmployeeViewSet,
    DependentViewSet,
    register_user,
    request_password_reset,
    reset_password_confirm,
    verify_email,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'providers', ProviderViewSet, basename='provider')
router.register(r'mddo-providers', MDDOProviderViewSet)
router.register(r'pa-providers', PAProviderViewSet)
router.register(r'np-providers', NPProviderViewSet)
router.register(r'brokers', BrokerViewSet, basename='broker')
router.register(r'employers', EmployerViewSet, basename='employer')
router.register(r'employees', EmployeeViewSet)
router.register(r'dependents', DependentViewSet)

urlpatterns = [
    path('register/', register_user, name='register'),
    path('password/reset/', request_password_reset, name='password_reset'),
    path('password/reset/confirm/', reset_password_confirm, name='password_reset_confirm'),
    path('verify-email/', verify_email, name='verify_email'),
    path('', include(router.urls)),
] 