from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Consultation,
    Delivrance,
    Medecin,
    Notification,
    Ordonnance,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Rôle et permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["nom", "prenom", "type_beneficiaire", "numero_carte", "assure_principal", "plan_couverture"]
    list_filter = ["type_beneficiaire", "plan_couverture"]
    search_fields = ["nom", "prenom", "numero_carte"]


@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ["nom", "prenom", "specialite", "email", "prestataire", "user"]
    list_filter = ["specialite", "prestataire"]
    search_fields = ["nom", "prenom", "email"]


@admin.register(Pharmacien)
class PharmacienAdmin(admin.ModelAdmin):
    list_display = ["user", "prestataire"]
    list_filter = ["prestataire"]


@admin.register(Prestataire)
class PrestataireAdmin(admin.ModelAdmin):
    list_display = ["nom", "type_prestataire", "ville", "partenaire"]
    list_filter = ["type_prestataire", "partenaire"]
    search_fields = ["nom", "ville"]


@admin.register(PlanCouverture)
class PlanCouvertureAdmin(admin.ModelAdmin):
    list_display = ["nom", "taux_couverture", "plafond_annuel"]


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ["patient", "medecin", "prestataire", "date_heure", "statut"]
    list_filter = ["statut", "prestataire"]
    search_fields = ["patient__nom", "patient__prenom", "medecin__nom", "medecin__prenom"]


@admin.register(Delivrance)
class DelivranceAdmin(admin.ModelAdmin):
    list_display = ["ordonnance", "pharmacien", "date_delivrance"]
    list_filter = ["pharmacien"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["destinataire", "message", "date_creation", "lue"]
    list_filter = ["lue"]
    search_fields = ["destinataire__email", "message"]


admin.site.register(ServiceMedical)
admin.site.register(PriseEnCharge)
admin.site.register(Consultation)
admin.site.register(Ordonnance)
