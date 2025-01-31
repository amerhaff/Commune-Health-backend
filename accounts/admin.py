from django.contrib import admin
from .models import (
    User, Provider, MDDOProvider, PAProvider, NPProvider,
    Broker, Employer, Employee, Dependent
)

admin.site.register(User)
admin.site.register(Provider)
admin.site.register(MDDOProvider)
admin.site.register(PAProvider)
admin.site.register(NPProvider)
admin.site.register(Broker)
admin.site.register(Employer)
admin.site.register(Employee)
admin.site.register(Dependent) 