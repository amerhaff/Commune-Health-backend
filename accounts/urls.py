from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    ProviderViewSet,
    MDDOProviderViewSet,
    PAProviderViewSet,
    NPProviderViewSet,
    BrokerViewSet,
    EmployerViewSet,
    EmployeeViewSet,
    DependentViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'providers', ProviderViewSet)
router.register(r'mddo-providers', MDDOProviderViewSet)
router.register(r'pa-providers', PAProviderViewSet)
router.register(r'np-providers', NPProviderViewSet)
router.register(r'brokers', BrokerViewSet)
router.register(r'employers', EmployerViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'dependents', DependentViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 