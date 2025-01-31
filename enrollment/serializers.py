from rest_framework import serializers
from .models import (
    ProviderPlan,
    Enrollment,
    DependentEnrollment,
    Transaction,
    TransactionDetail
)
from accounts.serializers import (
    ProviderSerializer,
    EmployeeSerializer,
    DependentSerializer,
    BrokerSerializer
)

class ProviderPlanSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    
    class Meta:
        model = ProviderPlan
        fields = [
            'id', 'provider', 'name', 'description', 
            'monthly_amount', 'is_active', 'created_at', 
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class EnrollmentSerializer(serializers.ModelSerializer):
    plan = ProviderPlanSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)
    broker = BrokerSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'plan', 'employee', 'broker', 'status',
            'start_date', 'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DependentEnrollmentSerializer(serializers.ModelSerializer):
    enrollment = EnrollmentSerializer(read_only=True)
    dependent = DependentSerializer(read_only=True)
    
    class Meta:
        model = DependentEnrollment
        fields = [
            'id', 'enrollment', 'dependent', 'start_date',
            'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'enrollment', 'transaction_type', 'amount',
            'status', 'billing_period_start', 'billing_period_end',
            'provider', 'broker', 'reference_id', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetail
        fields = [
            'id', 'transaction', 'description', 'amount',
            'dependent_enrollment', 'created_at'
        ]
        read_only_fields = ['created_at']
