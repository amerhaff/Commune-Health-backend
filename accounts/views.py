from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    User, 
    Broker,
    Provider,
    MDDOProvider,
    PAProvider,
    NPProvider,
    Employer,
    Employee,
    Dependent
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
    DependentSerializer
)

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

class EmployerViewSet(viewsets.ModelViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer
    permission_classes = [IsAuthenticated]

class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]

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
    queryset = Broker.objects.all()
    serializer_class = BrokerSerializer
    permission_classes = [IsAuthenticated]

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