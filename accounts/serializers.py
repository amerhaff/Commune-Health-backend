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
    Employer,
    ProviderOperatingHours,
    ProviderMembershipTier,
    EmployeeMembership,
    DependentMembership,
    Message
)
from django.utils import timezone
import uuid

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
        fields = [
            'id', 'user', 'brokerage_name', 'website',
            'national_producer_number', 'states_licensed', 
            'licensure_number'
        ]

class EmployeeMembershipSerializer(serializers.ModelSerializer):
    membership_tier_name = serializers.CharField(source='membership_tier.name', read_only=True)
    provider_name = serializers.CharField(source='provider.practice_name', read_only=True)
    
    class Meta:
        model = EmployeeMembership
        fields = [
            'id', 'membership_id', 'membership_tier', 'membership_tier_name',
            'provider', 'provider_name', 'start_date', 'end_date', 'is_active'
        ]

class DependentMembershipSerializer(serializers.ModelSerializer):
    membership_tier_name = serializers.CharField(source='membership_tier.name', read_only=True)
    provider_name = serializers.CharField(source='provider.practice_name', read_only=True)
    
    class Meta:
        model = DependentMembership
        fields = [
            'id', 'membership_id', 'membership_tier', 'membership_tier_name',
            'provider', 'provider_name', 'start_date', 'end_date', 'is_active'
        ]

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_contact_person = serializers.BooleanField(read_only=True)
    memberships = EmployeeMembershipSerializer(many=True, read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employer', 'user', 'first_name', 'last_name', 
            'email', 'address_line1', 'address_line2',
            'city', 'state', 'zip_code', 'sex',
            'date_of_birth', 'enrollment_date',
            'enrollment_status', 'is_contact_person',
            'memberships'
        ]

class EmployerSerializer(serializers.ModelSerializer):
    contact_person = UserSerializer(read_only=True)
    employees = EmployeeSerializer(many=True, read_only=True)
    contact_employee = serializers.SerializerMethodField()
    
    class Meta:
        model = Employer
        fields = [
            'id', 'contact_person', 'company_name', 'company_type', 
            'industry', 'company_size', 'website', 
            'employer_identification_number', 'phone', 'email',
            'address_line1', 'address_line2', 'city', 'state', 'zip_code',
            'employees', 'contact_employee'
        ]

    def get_contact_employee(self, obj):
        """Get the employee record for the contact person"""
        try:
            contact_employee = obj.employees.get(user=obj.contact_person)
            return EmployeeSerializer(contact_employee).data
        except Employee.DoesNotExist:
            return None

class EmployerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an employer with contact person"""
    contact_person_email = serializers.EmailField(write_only=True)
    contact_person_first_name = serializers.CharField(write_only=True)
    contact_person_last_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Employer
        fields = [
            'company_name', 'company_type', 'industry',
            'company_size', 'website', 'employer_identification_number',
            'phone', 'email', 'address_line1', 'address_line2',
            'city', 'state', 'zip_code',
            'contact_person_email', 'contact_person_first_name',
            'contact_person_last_name'
        ]

    def create(self, validated_data):
        # Extract contact person data
        contact_email = validated_data.pop('contact_person_email')
        contact_first_name = validated_data.pop('contact_person_first_name')
        contact_last_name = validated_data.pop('contact_person_last_name')

        # Create or get user for contact person
        user, created = User.objects.get_or_create(
            email=contact_email,
            defaults={
                'username': contact_email,
                'first_name': contact_first_name,
                'last_name': contact_last_name,
                'user_type': User.UserType.EMPLOYER
            }
        )

        # Create employer
        employer = Employer.objects.create(
            contact_person=user,
            **validated_data
        )

        # Create employee record for contact person
        employee = Employee.objects.create(
            employer=employer,
            user=user,
            first_name=contact_first_name,
            last_name=contact_last_name,
            email=contact_email,
            enrollment_status='ACTIVE',
            enrollment_date=timezone.now().date(),
        )

        return employer

class OperatingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderOperatingHours
        fields = ['day', 'is_open', 'open_time', 'close_time']

class MembershipTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderMembershipTier
        fields = [
            'id', 'name', 'price', 'description', 
            'is_active', 'created_at', 'updated_at',
            'annual_price', 'formatted_price'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_accepting_patients = serializers.BooleanField(read_only=True)
    operating_hours = OperatingHoursSerializer(many=True, read_only=True)
    membership_tiers = MembershipTierSerializer(many=True, read_only=True)
    
    class Meta:
        model = Provider
        fields = [
            'id', 'user', 'provider_type', 'practice_name', 'website',
            'years_experience', 'npi_number', 'dea_number',
            'states_licensed', 'license_number', 'accepting_patients',
            'max_patient_capacity', 'current_patient_count', 
            'is_accepting_patients', 'operating_hours', 'membership_tiers'
        ]
        read_only_fields = ['current_patient_count']
        extra_kwargs = {
            'max_patient_capacity': {'required': True}
        }

    def validate_max_patient_capacity(self, value):
        """
        Validate that max_patient_capacity is not less than current_patient_count
        """
        if self.instance and value < self.instance.current_patient_count:
            raise serializers.ValidationError(
                "Maximum capacity cannot be less than current patient count"
            )
        if value < 1:
            raise serializers.ValidationError(
                "Maximum capacity must be at least 1"
            )
        return value

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

class DependentSerializer(serializers.ModelSerializer):
    memberships = DependentMembershipSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dependent
        fields = [
            'id', 'employee', 'first_name', 'last_name',
            'date_of_birth', 'sex', 'relationship',
            'enrollment_date', 'enrollment_status',
            'memberships'
        ]

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message  # Create Message model if not exists
        fields = ['id', 'sender', 'content', 'timestamp', 'seen'] 