from django.contrib import admin
from django.contrib.auth.models import User

from .models import (
    Consultation,
    Medecin,
    Ordonnance,
    Patient,
    PriseEnCharge,
    ServiceMedical,
)


admin.site.register(Patient)
admin.site.register(Medecin)
admin.site.register(ServiceMedical)
admin.site.register(PriseEnCharge)
admin.site.register(Consultation)
admin.site.register(Ordonnance)
