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
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_token_created = models.DateTimeField(null=True, blank=True)

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
    accepting_patients = models.BooleanField(
        default=True,
        help_text="Whether the provider is currently accepting new patients"
    )
    max_patient_capacity = models.IntegerField(
        default=1000,
        help_text="Maximum number of patients you will accept"
    )
    current_patient_count = models.IntegerField(
        default=0,
        help_text="Current number of active patients"
    )

    def __str__(self):
        return f"Provider: {self.user.get_full_name()} ({self.get_provider_type_display()})"

    @property
    def is_accepting_patients(self):
        """Check if provider can accept new patients based on capacity and settings"""
        return (
            self.accepting_patients and 
            self.current_patient_count < self.max_patient_capacity
        )

    @property
    def active_membership_tiers(self):
        """Return all active membership tiers"""
        return self.membership_tiers.filter(is_active=True)

    def get_membership_tier_by_name(self, tier_name):
        """Get a specific membership tier by name"""
        return self.membership_tiers.filter(name=tier_name).first()

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
    contact_person = models.OneToOneField(
        User,
        on_delete=models.PROTECT,  # Prevent deletion of user if they're a contact person
        related_name='employer_contact_for'
    )
    company_name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=50)
    industry = models.CharField(max_length=100)
    company_size = models.IntegerField()
    website = models.URLField(blank=True)
    employer_identification_number = models.CharField(max_length=20)
    
    # Contact info
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.company_name} (Contact: {self.contact_person.get_full_name()})"

class Employee(models.Model):
    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employee_profile',
        help_text="Associated user account, if this employee has system access"
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
    
    # Personal/Enrollment fields
    sex = models.CharField(max_length=1)
    date_of_birth = models.DateField()
    enrollment_date = models.DateField()
    enrollment_status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def is_contact_person(self):
        """Check if this employee is the employer's contact person"""
        return self.user and self.user == self.employer.contact_person

class EmployeeMembership(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    membership_tier = models.ForeignKey(
        ProviderMembershipTier,
        on_delete=models.PROTECT,
        related_name='employee_memberships'
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name='employee_memberships'
    )
    membership_id = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee} - {self.membership_tier.name} ({self.membership_id})"

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

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_relationship_display()} of {self.employee.first_name} {self.employee.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']

class DependentMembership(models.Model):
    dependent = models.ForeignKey(
        Dependent,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    membership_tier = models.ForeignKey(
        ProviderMembershipTier,
        on_delete=models.PROTECT,
        related_name='dependent_memberships'
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name='dependent_memberships'
    )
    membership_id = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.dependent} - {self.membership_tier.name} ({self.membership_id})"

class ProviderOperatingHours(models.Model):
    class DayOfWeek(models.TextChoices):
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        SUNDAY = 'sunday', 'Sunday'

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='operating_hours'
    )
    day = models.CharField(
        max_length=10,
        choices=DayOfWeek.choices
    )
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ['provider', 'day']
        ordering = ['day']

    def __str__(self):
        if not self.is_open:
            return f"{self.provider.practice_name} - {self.get_day_display()}: Closed"
        return f"{self.provider.practice_name} - {self.get_day_display()}: {self.open_time} to {self.close_time}"

class ProviderMembershipTier(models.Model):
    provider = models.ForeignKey(
        'Provider',
        on_delete=models.CASCADE,
        related_name='membership_tiers',
        help_text="The provider offering this membership tier"
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the membership tier (e.g., 'Basic', 'Premium', 'Gold')"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly price for this membership tier"
    )
    description = models.TextField(
        help_text="Description of what's included in this membership tier"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this tier is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']
        unique_together = ['provider', 'name']

    def __str__(self):
        return f"{self.provider.get_full_name()} - {self.name} (${self.price:.2f}/month)"

    @property
    def annual_price(self):
        """Calculate the annual price for this tier"""
        return self.price * 12

    @property
    def formatted_price(self):
        """Return formatted monthly price"""
        return f"${self.price:.2f}/month"

    def toggle_active_status(self):
        """Toggle the active status of this tier"""
        self.is_active = not self.is_active
        self.save()