from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import (
    User, 
    Broker,
    Provider,
    MDDOProvider,
    PAProvider,
    NPProvider,
    Employer,
    Employee,
    Dependent,
    ProviderMembershipTier,
    ProviderOperatingHours,
    Enrollment,
    EmployeeMembership,
    DependentMembership,
    Client
)
from .serializers import (
    UserSerializer,
    BrokerSerializer,
    ProviderSerializer,
    MDDOProviderSerializer,
    PAProviderSerializer,
    NPProviderSerializer,
    EmployerSerializer,
    EmployeeSerializer,
    DependentSerializer,
    MembershipTierSerializer,
    OperatingHoursSerializer,
    ProviderProfileSerializer,
    PracticeInfoSerializer,
    PasswordUpdateSerializer,
    EmployerEnrollmentSerializer,
    PendingEnrollmentSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    ContactSerializer,
    DashboardMetricsSerializer,
    RevenueMetricsSerializer,
    ClientSerializer,
    HealthcareSpendSerializer,
    EnrollmentSerializer
)
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
from django.db import transaction
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
from .permissions import IsEmployer, IsProvider, IsBroker, IsAdmin, IsOwnerOrAdmin
from .decorators import require_user_type, require_object_ownership
from audit.decorators import audit_action, audit_security
from audit.services import AuditService

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def brokers(self, request):
        brokers = User.objects.filter(user_type=User.UserType.BROKER)
        serializer = self.get_serializer(brokers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def providers(self, request):
        providers = User.objects.filter(user_type=User.UserType.PROVIDER)
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['PUT', 'PATCH'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsEmployer | IsAdmin]
    serializer_class = EmployerSerializer
    
    @require_user_type('EMPLOYER', 'ADMIN')
    def get_queryset(self):
        if self.request.user.user_type == 'ADMIN':
            return Employer.objects.all()
        return Employer.objects.filter(user=self.request.user)

    @audit_action('VIEW')
    @require_user_type('EMPLOYER', 'ADMIN')
    @require_object_ownership()
    @action(detail=True, methods=['GET'])
    def employee_roster(self, request, pk=None):
        """Get all employees and their dependents"""
        employer = self.get_object()
        employees = employer.employees.all().prefetch_related('dependents')
        
        roster_data = []
        for employee in employees:
            employee_data = EmployeeSerializer(employee).data
            employee_data['dependents'] = DependentSerializer(
                employee.dependents.all(), 
                many=True
            ).data
            roster_data.append(employee_data)
            
        return Response(roster_data)

    @audit_action('CREATE')
    @require_user_type('EMPLOYER', 'ADMIN')
    @require_object_ownership()
    @action(detail=True, methods=['POST'])
    def add_employee(self, request, pk=None):
        """Add a new employee"""
        employer = self.get_object()
        serializer = EmployeeSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(employer=employer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'])
    def healthcare_spend(self, request, pk=None):
        """Get healthcare spending metrics"""
        employer = self.get_object()
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        metrics = {
            'total_spend': 0,
            'employee_spend': 0,
            'dependent_spend': 0,
            'average_per_employee': 0,
            'monthly_trends': [],
            'spend_by_tier': []
        }
        
        # Calculate metrics
        employees = employer.employees.filter(status='enrolled')
        
        for employee in employees:
            metrics['employee_spend'] += employee.membership_amount or 0
            dependent_spend = sum(d.membership_amount or 0 for d in employee.dependents.filter(is_enrolled=True))
            metrics['dependent_spend'] += dependent_spend
            
        metrics['total_spend'] = metrics['employee_spend'] + metrics['dependent_spend']
        if employees.count() > 0:
            metrics['average_per_employee'] = metrics['total_spend'] / employees.count()
            
        return Response(metrics)

    @action(detail=True, methods=['GET'])
    def enrollment_stats(self, request, pk=None):
        """Get enrollment statistics"""
        employer = self.get_object()
        
        stats = {
            'total_employees': employer.employees.count(),
            'enrolled_employees': employer.employees.filter(status='enrolled').count(),
            'pending_enrollments': employer.employees.filter(status='pending').count(),
            'total_dependents': sum(e.dependents.count() for e in employer.employees.all()),
            'enrolled_dependents': sum(
                e.dependents.filter(is_enrolled=True).count() 
                for e in employer.employees.all()
            )
        }
        
        return Response(stats)

    @action(detail=True, methods=['GET'])
    def provider_directory(self, request, pk=None):
        """Get list of available providers"""
        from .models import Provider  # Import here to avoid circular import
        
        providers = Provider.objects.filter(
            accepting_patients=True
        ).select_related('user')
        
        return Response({
            'providers': [{
                'id': provider.id,
                'name': f"{provider.user.first_name} {provider.user.last_name}",
                'practice_name': provider.practice_name,
                'specialty': provider.get_provider_type_display(),
                'location': f"{provider.user.city}, {provider.user.state}",
                'accepting_patients': provider.is_accepting_patients,
                'current_patient_count': provider.current_patient_count,
                'max_patient_capacity': provider.max_patient_capacity
            } for provider in providers]
        })

    @action(detail=True, methods=['GET', 'POST'])
    def messages(self, request, pk=None):
        """Handle employer messages"""
        employer = self.get_object()
        
        if request.method == 'GET':
            messages = employer.messages.all().order_by('-timestamp')
            return Response({
                'messages': [{
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'sender': msg.sender,
                    'seen': msg.seen
                } for msg in messages]
            })
        
        # Handle sending new message
        recipient_type = request.data.get('recipient_type')
        recipient_id = request.data.get('recipient_id')
        content = request.data.get('content')
        
        message = employer.messages.create(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            content=content
        )
        
        return Response({
            'id': message.id,
            'status': 'sent'
        })

    @audit_action('UPDATE')
    @audit_security(severity='HIGH')
    @require_user_type('EMPLOYER', 'ADMIN')
    @require_object_ownership()
    @action(detail=True, methods=['PUT'])
    def update_settings(self, request, pk=None):
        """Update employer settings"""
        employer = self.get_object()
        serializer = EmployerSerializer(employer, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProviderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsProvider | IsAdmin]
    serializer_class = ProviderSerializer
    
    @require_user_type('PROVIDER', 'ADMIN')
    def get_queryset(self):
        if self.request.user.user_type == 'ADMIN':
            return Provider.objects.all()
        return Provider.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_accepting_patients(self, request, pk=None):
        """
        Toggle the provider's accepting_patients status
        """
        provider = self.get_object()
        provider.accepting_patients = not provider.accepting_patients
        provider.save()
        
        return Response({
            'accepting_patients': provider.accepting_patients,
            'is_accepting_patients': provider.is_accepting_patients
        })

    @action(detail=True, methods=['GET', 'PUT'])
    def operating_hours(self, request, pk=None):
        """Manage provider's operating hours"""
        provider = self.get_object()
        
        if request.method == 'GET':
            serializer = OperatingHoursSerializer(provider.operating_hours.all(), many=True)
            return Response(serializer.data)
        
        serializer = OperatingHoursSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            provider.operating_hours.all().delete()
            serializer.save(provider=provider)
        
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Get provider statistics (patient count, capacity, etc.)
        """
        provider = self.get_object()
        return Response({
            'current_patient_count': provider.current_patient_count,
            'max_patient_capacity': provider.max_patient_capacity,
            'available_capacity': provider.max_patient_capacity - provider.current_patient_count,
            'is_accepting_patients': provider.is_accepting_patients,
        })

    @action(detail=True, methods=['get'])
    def dashboard_metrics(self, request, pk=None):
        """Endpoint for provider dashboard metrics"""
        provider = self.get_object()
        
        # Calculate metrics
        total_patients = EmployeeMembership.objects.filter(
            provider=provider,
            is_active=True
        ).count() + DependentMembership.objects.filter(
            provider=provider,
            is_active=True
        ).count()

        revenue = (
            EmployeeMembership.objects.filter(
                provider=provider,
                is_active=True
            ).aggregate(
                total=Sum('membership_tier__price')
            )['total'] or 0
        ) + (
            DependentMembership.objects.filter(
                provider=provider,
                is_active=True
            ).aggregate(
                total=Sum('membership_tier__price')
            )['total'] or 0
        )

        appointments = 0  # Add appointment logic when implemented
        messages = 0  # Add message count logic when implemented

        data = {
            'total_patients': total_patients,
            'revenue': revenue,
            'appointments': appointments,
            'messages': messages
        }
        
        return Response(data)

    @action(detail=True, methods=['get'])
    def revenue_metrics(self, request, pk=None):
        """Endpoint for provider revenue metrics"""
        provider = self.get_object()
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        # Calculate revenue metrics
        employer_revenues = []
        total_monthly_revenue = 0
        total_annual_revenue = 0

        # Get all active memberships
        memberships = EmployeeMembership.objects.filter(
            provider=provider,
            is_active=True
        ).select_related('employee__employer')

        # Group by employer and calculate revenues
        employer_data = {}
        for membership in memberships:
            employer = membership.employee.employer
            if employer.id not in employer_data:
                employer_data[employer.id] = {
                    'name': employer.company_name,
                    'monthly_revenue': 0,
                    'annual_revenue': 0,
                    'enrollee_count': 0
                }
            
            employer_data[employer.id]['monthly_revenue'] += membership.membership_tier.price
            employer_data[employer.id]['annual_revenue'] += membership.membership_tier.annual_price
            employer_data[employer.id]['enrollee_count'] += 1

        # Format response data
        employer_revenues = [
            {
                'employer_id': emp_id,
                'name': data['name'],
                'monthly_revenue': data['monthly_revenue'],
                'annual_revenue': data['annual_revenue'],
                'enrollee_count': data['enrollee_count']
            }
            for emp_id, data in employer_data.items()
        ]

        total_monthly_revenue = sum(emp['monthly_revenue'] for emp in employer_revenues)
        total_annual_revenue = sum(emp['annual_revenue'] for emp in employer_revenues)

        data = {
            'employer_revenues': employer_revenues,
            'total_monthly_revenue': total_monthly_revenue,
            'total_annual_revenue': total_annual_revenue
        }

        return Response(data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Endpoint for provider messages"""
        provider = self.get_object()
        # Implement message retrieval logic
        messages = []  # Add message retrieval from your message model
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Endpoint for sending messages"""
        provider = self.get_object()
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            # Implement message sending logic
            return Response({'status': 'message sent'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def update_profile(self, request, pk=None):
        """Endpoint for updating provider profile"""
        provider = self.get_object()
        serializer = ProviderSerializer(provider, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MDDOProviderViewSet(viewsets.ModelViewSet):
    queryset = MDDOProvider.objects.all()
    serializer_class = MDDOProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MDDOProvider.objects.filter(
            provider__provider_type=Provider.ProviderType.MDDO
        )

class PAProviderViewSet(viewsets.ModelViewSet):
    queryset = PAProvider.objects.all()
    serializer_class = PAProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PAProvider.objects.filter(
            provider__provider_type=Provider.ProviderType.PA
        )

class NPProviderViewSet(viewsets.ModelViewSet):
    queryset = NPProvider.objects.all()
    serializer_class = NPProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NPProvider.objects.filter(
            provider__provider_type=Provider.ProviderType.NP
        )

class BrokerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsBroker | IsAdmin]
    serializer_class = BrokerSerializer
    
    @require_user_type('BROKER', 'ADMIN')
    def get_queryset(self):
        if self.request.user.user_type == 'ADMIN':
            return Broker.objects.all()
        return Broker.objects.filter(user=self.request.user)

    @action(detail=True, methods=['GET'])
    def client_roster(self, request, pk=None):
        """Get all clients for the broker"""
        broker = self.get_object()
        clients = broker.clients.all()
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def client_enrollments(self, request, pk=None):
        """Get enrollment status for all clients"""
        broker = self.get_object()
        clients = broker.clients.all().prefetch_related(
            'employees',
            'employees__dependents'
        )
        
        enrollment_data = []
        for client in clients:
            enrollment_data.append({
                'id': client.id,
                'name': client.name,
                'total_employees': client.total_employees,
                'enrolled_employees': client.enrolled_employees,
                'enrolled_dependents': client.enrolled_dependents,
                'enrollment_rate': (client.enrolled_employees / client.total_employees * 100 
                                  if client.total_employees > 0 else 0)
            })
        
        return Response(enrollment_data)

    @action(detail=True, methods=['GET'])
    def revenue_metrics(self, request, pk=None):
        """Get revenue metrics for the broker"""
        broker = self.get_object()
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        metrics = broker.get_revenue_metrics(year, month)
        serializer = RevenueMetricsSerializer(metrics)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def enrollment_center(self, request, pk=None):
        """Get enrollment statistics and pending enrollments"""
        broker = self.get_object()
        
        pending_enrollments = Employee.objects.filter(
            client__broker=broker,
            status='pending'
        ).select_related('client')
        
        return Response({
            'pending_count': pending_enrollments.count(),
            'enrollments': [{
                'id': enrollment.id,
                'employee_name': f"{enrollment.first_name} {enrollment.last_name}",
                'client_name': enrollment.client.name,
                'submission_date': enrollment.created_at,
                'status': enrollment.status
            } for enrollment in pending_enrollments]
        })

    @action(detail=True, methods=['GET', 'POST'])
    def messages(self, request, pk=None):
        """Handle broker messages"""
        broker = self.get_object()
        
        if request.method == 'GET':
            messages = broker.messages.all().order_by('-timestamp')
            return Response({
                'messages': [{
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'sender': msg.sender,
                    'seen': msg.seen
                } for msg in messages]
            })
        
        # Handle sending new message
        recipient_type = request.data.get('recipient_type')
        recipient_id = request.data.get('recipient_id')
        content = request.data.get('content')
        
        message = broker.messages.create(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            content=content
        )
        
        return Response({
            'id': message.id,
            'status': 'sent'
        })

    @action(detail=True, methods=['PUT'])
    def update_settings(self, request, pk=None):
        """Update broker settings"""
        broker = self.get_object()
        serializer = BrokerSerializer(broker, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.all()
        employer_id = self.request.query_params.get('employer', None)
        if employer_id:
            queryset = queryset.filter(employer_id=employer_id)
        return queryset

class DependentViewSet(viewsets.ModelViewSet):
    queryset = Dependent.objects.all()
    serializer_class = DependentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Dependent.objects.all()
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    data = request.data.copy()
    defaults = {
        'phone': '',
        'address_line1': '',
        'city': '',
        'state': '',
        'zip_code': '',
    }
    for field, value in defaults.items():
        if field not in data:
            data[field] = value

    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        if user:
            # Generate verification token
            token = str(uuid.uuid4())
            user.email_verification_token = token
            user.email_verification_token_created = timezone.now()
            user.save()

            # Send verification email
            verification_url = f"http://localhost:3000/verify-email?token={token}"
            send_mail(
                'Verify your email',
                f'Click the following link to verify your email: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # Create token for the new user
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Please check your email to verify your account.'
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.query_params.get('token')
    try:
        user = User.objects.get(
            email_verification_token=token,
            email_verified=False,
            email_verification_token_created__gte=timezone.now() - timedelta(days=1)
        )
        user.email_verified = True
        user.email_verification_token = ''
        user.save()
        return Response({'message': 'Email verified successfully'})
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired verification token'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        reset_url = f"http://localhost:3000/reset-password?token={token}&email={email}"
        
        send_mail(
            'Password Reset Request',
            f'Click the following link to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({"message": "Password reset email sent"})
    except User.DoesNotExist:
        # Return success even if user doesn't exist for security
        return Response({"message": "Password reset email sent"})

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    token = request.data.get('token')
    email = request.data.get('email')
    new_password = request.data.get('new_password')
    
    try:
        user = User.objects.get(email=email)
        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successful"})
        return Response(
            {"error": "Invalid token"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except User.DoesNotExist:
        return Response(
            {"error": "Invalid email"}, 
            status=status.HTTP_400_BAD_REQUEST
        ) 