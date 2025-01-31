from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class UserType(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        PROVIDER = 'PROVIDER', 'Provider'
        EMPLOYER = 'EMPLOYER', 'Employer'
        BROKER = 'BROKER', 'Broker'

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices
    )
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Provider(models.Model):
    class ProviderType(models.TextChoices):
        MDDO = 'MDDO', 'MD/DO'
        NP = 'NP', 'Nurse Practitioner'
        PA = 'PA', 'Physician Assistant'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='provider'
    )
    provider_type = models.CharField(
        max_length=10,
        choices=ProviderType.choices
    )
    practice_name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    years_experience = models.IntegerField()
    npi_number = models.CharField(max_length=10)
    dea_number = models.CharField(max_length=9)
    states_licensed = models.JSONField(default=list)
    license_number = models.CharField(max_length=50)

    def __str__(self):
        return f"Provider: {self.user.get_full_name()} ({self.get_provider_type_display()})"

class MDDOProvider(models.Model):
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='mddo_details'
    )
    medical_school = models.CharField(max_length=255)
    medical_school_graduation_year = models.IntegerField()
    residency_institution = models.CharField(max_length=255)
    residency_specialty = models.CharField(max_length=255)
    residency_graduation_year = models.IntegerField()
    fellowship_institution = models.CharField(max_length=255, blank=True)
    fellowship_specialty = models.CharField(max_length=255, blank=True)
    fellowship_graduation_year = models.IntegerField(null=True, blank=True)

class PAProvider(models.Model):
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='pa_details'
    )
    pa_school = models.CharField(max_length=255)
    pa_school_graduation_year = models.IntegerField()

class NPProvider(models.Model):
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='np_details'
    )
    np_school = models.CharField(max_length=255)
    np_school_graduation_year = models.IntegerField()

class Broker(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='broker'
    )
    # Brokerage info
    brokerage_name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    national_producer_number = models.CharField(max_length=100)
    states_licensed = models.JSONField(default=list)
    licensure_number = models.CharField(max_length=100)

    def __str__(self):
        return f"Broker: {self.user.get_full_name()}"

class Employer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employer'
    )
    company_name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=50)
    industry = models.CharField(max_length=100)
    company_size = models.IntegerField()
    website = models.URLField(blank=True)
    employer_identification_number = models.CharField(max_length=20)

class Employee(models.Model):
    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    
    # Address fields
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    
    # Existing fields
    sex = models.CharField(max_length=1)
    date_of_birth = models.DateField()
    enrollment_date = models.DateField()
    enrollment_status = models.CharField(max_length=20)
    dpc_membership_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']

class Dependent(models.Model):
    class Relationship(models.TextChoices):
        SPOUSE = 'SPOUSE', 'Spouse'
        PARTNER = 'PARTNER', 'Partner'
        CHILD = 'CHILD', 'Child'

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='dependents'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1)
    relationship = models.CharField(
        max_length=20,
        choices=Relationship.choices
    )
    enrollment_date = models.DateField()
    enrollment_status = models.CharField(max_length=20)
    dpc_membership_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_relationship_display()} of {self.employee.first_name} {self.employee.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']