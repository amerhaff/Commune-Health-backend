from django.contrib import admin
from .models import (
    ProviderPlan, Enrollment, DependentEnrollment,
    Transaction, TransactionDetail
)

admin.site.register(ProviderPlan)
admin.site.register(Enrollment)
admin.site.register(DependentEnrollment)
admin.site.register(Transaction)
admin.site.register(TransactionDetail) 