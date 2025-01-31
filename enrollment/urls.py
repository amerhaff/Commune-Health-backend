from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProviderPlanViewSet,
    EnrollmentViewSet,
    DependentEnrollmentViewSet,
    TransactionViewSet,
    TransactionDetailViewSet
)

router = DefaultRouter()
router.register(r'provider-plans', ProviderPlanViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'dependent-enrollments', DependentEnrollmentViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'transaction-details', TransactionDetailViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
