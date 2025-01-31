from django.db import models
from accounts.models import Provider, Employee, Dependent, Broker

class ProviderPlan(models.Model):
    """Membership plans offered by providers"""
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='membership_plans'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    monthly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly membership fee"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider.practice_name} - {self.name}"

class Enrollment(models.Model):
    """Primary enrollment record for employees"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        CANCELLED = 'CANCELLED', 'Cancelled'

    plan = models.ForeignKey(
        ProviderPlan,
        on_delete=models.PROTECT,
        related_name='enrollments'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='plan_enrollments'
    )
    broker = models.ForeignKey(
        Broker,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='managed_enrollments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.plan.name}"

class DependentEnrollment(models.Model):
    """Tracks dependents enrolled under an employee's plan"""
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='dependent_enrollments'
    )
    dependent = models.ForeignKey(
        Dependent,
        on_delete=models.PROTECT,
        related_name='plan_enrollments'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dependent.full_name} - {self.enrollment.plan.name}"

    class Meta:
        unique_together = ['enrollment', 'dependent']

class Transaction(models.Model):
    """Tracks all financial transactions for enrollments"""
    class TransactionType(models.TextChoices):
        PROVIDER_PAYMENT = 'PROVIDER', 'Provider Payment'
        BROKER_COMMISSION = 'BROKER', 'Broker Commission'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,
        blank=True
    )
    broker = models.ForeignKey(
        Broker,
        on_delete=models.PROTECT,
        related_name='commissions',
        null=True,
        blank=True
    )
    reference_id = models.CharField(max_length=100, unique=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.reference_id}"

    class Meta:
        indexes = [
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['billing_period_start']),
        ]

class TransactionDetail(models.Model):
    """Itemized breakdown of transaction amounts"""
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='details'
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    dependent_enrollment = models.ForeignKey(
        DependentEnrollment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transaction_details'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction.reference_id} - {self.description}"
