from rest_framework import serializers
from .models import (
    User,
    Broker,
    Provider,
    MDDOProvider,
    PAProvider,
    NPProvider,
    Employee,
    Dependent,
    Employer
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'phone', 'address_line1', 'address_line2',
                 'city', 'state', 'zip_code']

class BrokerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Broker
        fields = ['id', 'user', 'brokerage_name', 'website',
                 'national_producer_number', 'states_licensed', 'licensure_number']

class EmployerSerializer(serializers.ModelSerializer):
    admin = UserSerializer(read_only=True)
    
    class Meta:
        model = Employer
        fields = ['id', 'admin', 'company_name', 'company_type', 'industry',
                 'company_size', 'website', 'employer_identification_number',
                 'address_line1', 'address_line2', 'city', 'state', 'zip_code',
                 'phone', 'email']

class ProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Provider
        fields = ['id', 'user', 'provider_type', 'practice_name', 'website',
                 'years_experience', 'npi_number', 'dea_number',
                 'states_licensed', 'license_number']

class MDDOProviderSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    
    class Meta:
        model = MDDOProvider
        fields = ['id', 'provider', 'medical_school', 'medical_school_graduation_year',
                 'residency_institution', 'residency_specialty',
                 'residency_graduation_year', 'fellowship_institution',
                 'fellowship_specialty', 'fellowship_graduation_year']

class PAProviderSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    
    class Meta:
        model = PAProvider
        fields = ['id', 'provider', 'pa_school', 'pa_school_graduation_year']

class NPProviderSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    
    class Meta:
        model = NPProvider
        fields = ['id', 'provider', 'np_school', 'np_school_graduation_year']

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'id', 'employer', 'first_name', 'last_name', 
            'email', 'address_line1', 'address_line2',
            'city', 'state', 'zip_code', 'sex',
            'date_of_birth', 'enrollment_date',
            'enrollment_status', 'dpc_membership_id'
        ]

class DependentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependent
        fields = [
            'id', 'employee', 'first_name', 'last_name',
            'date_of_birth', 'sex', 'relationship',
            'enrollment_date', 'enrollment_status',
            'dpc_membership_id'
        ] 