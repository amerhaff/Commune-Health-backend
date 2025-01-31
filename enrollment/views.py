from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    ProviderPlan,
    Enrollment,
    DependentEnrollment,
    Transaction,
    TransactionDetail
)
from .serializers import (
    ProviderPlanSerializer,
    EnrollmentSerializer,
    DependentEnrollmentSerializer,
    TransactionSerializer,
    TransactionDetailSerializer
)

class ProviderPlanViewSet(viewsets.ModelViewSet):
    queryset = ProviderPlan.objects.all()
    serializer_class = ProviderPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ProviderPlan.objects.all()
        provider_id = self.request.query_params.get('provider', None)
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        return queryset

    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get all enrollments for a specific plan"""
        plan = self.get_object()
        enrollments = plan.enrollments.all()
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Enrollment.objects.all()
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset

    @action(detail=True, methods=['post'])
    def add_dependent(self, request, pk=None):
        """Add a dependent to an enrollment"""
        enrollment = self.get_object()
        serializer = DependentEnrollmentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(enrollment=enrollment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_dependent(self, request, pk=None):
        """Remove a dependent from an enrollment by setting end_date"""
        enrollment = self.get_object()
        dependent_id = request.data.get('dependent_id')
        end_date = request.data.get('end_date')

        try:
            dep_enrollment = enrollment.dependent_enrollments.get(
                dependent_id=dependent_id,
                end_date=None
            )
            dep_enrollment.end_date = end_date
            dep_enrollment.save()
            return Response(status=status.HTTP_200_OK)
        except DependentEnrollment.DoesNotExist:
            return Response(
                {"error": "Active dependent enrollment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class DependentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = DependentEnrollment.objects.all()
    serializer_class = DependentEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DependentEnrollment.objects.all()
        enrollment_id = self.request.query_params.get('enrollment', None)
        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        return queryset

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.all()
        enrollment_id = self.request.query_params.get('enrollment', None)
        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        return queryset

    @action(detail=False, methods=['get'])
    def provider_revenue(self, request):
        """Get total revenue for providers within a date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        revenue = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.PROVIDER_PAYMENT,
            status=Transaction.Status.COMPLETED,
            billing_period_start__gte=start_date,
            billing_period_end__lte=end_date
        ).aggregate(total_revenue=models.Sum('amount'))
        
        return Response(revenue)

class TransactionDetailViewSet(viewsets.ModelViewSet):
    queryset = TransactionDetail.objects.all()
    serializer_class = TransactionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TransactionDetail.objects.all()
        transaction_id = self.request.query_params.get('transaction', None)
        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)
        return queryset
