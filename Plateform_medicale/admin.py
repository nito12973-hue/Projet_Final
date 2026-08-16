from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Consultation,
    Delivrance,
    JournalActivite,
    Medecin,
    Notification,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
)


class SuppressionGereeParLAppMixin:
    """
    Bloque la suppression depuis /admin/ pour les modeles dont la vue
    supprimer_* de l'app porte une logique metier que /admin/ ignore
    completement (desactivation du User lie, avertissements de cascade,
    garde-fou anti-auto-suppression sur l'utilisateur courant -- voir
    supprimer_patient/supprimer_medecin/supprimer_utilisateur dans
    views.py). Verifie manuellement avant ce correctif : le compte admin
    de la plateforme (is_staff=True via create_superuser du setup_wizard)
    pouvait supprimer un Patient depuis /admin/ sans que le User associe
    soit desactive -- exactement le bug que "Symetrie a la suppression"
    (CLAUDE.md) corrige cote app, silencieusement contourne ici.
    """

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(SuppressionGereeParLAppMixin, BaseUserAdmin):
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
class PatientAdmin(SuppressionGereeParLAppMixin, admin.ModelAdmin):
    list_display = ["nom", "prenom", "type_beneficiaire", "numero_carte", "assure_principal", "plan_couverture"]
    list_filter = ["type_beneficiaire", "plan_couverture"]
    search_fields = ["nom", "prenom", "numero_carte"]


@admin.register(Medecin)
class MedecinAdmin(SuppressionGereeParLAppMixin, admin.ModelAdmin):
    list_display = ["nom", "prenom", "specialite", "email", "prestataire", "user"]
    list_filter = ["specialite", "prestataire"]
    search_fields = ["nom", "prenom", "email"]


@admin.register(Pharmacien)
class PharmacienAdmin(admin.ModelAdmin):
    list_display = ["user", "prestataire"]
    list_filter = ["prestataire"]


@admin.register(Prestataire)
class PrestataireAdmin(SuppressionGereeParLAppMixin, admin.ModelAdmin):
    list_display = ["nom", "type_prestataire", "ville", "partenaire"]
    list_filter = ["type_prestataire", "partenaire"]
    search_fields = ["nom", "ville"]


@admin.register(PlanCouverture)
class PlanCouvertureAdmin(SuppressionGereeParLAppMixin, admin.ModelAdmin):
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


@admin.register(ServiceMedical)
class ServiceMedicalAdmin(SuppressionGereeParLAppMixin, admin.ModelAdmin):
    list_display = ["nom", "prix", "prestataire"]
    search_fields = ["nom"]


@admin.register(PriseEnCharge)
class PriseEnChargeAdmin(SuppressionGereeParLAppMixin, admin.ModelAdmin):
    list_display = ["patient", "date_demande", "statut"]
    list_filter = ["statut"]
    search_fields = ["patient__nom", "patient__prenom"]


@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    """Strictement en lecture seule, ici comme dans l'application.

    Un journal d'audit qu'un administrateur peut retoucher ne vaut rien : il
    ne prouve plus que ce que son dernier lecteur a bien voulu y laisser. Les
    trois permissions sont donc refusees -- pas seulement la suppression,
    contrairement a SuppressionGereeParLAppMixin (qui, lui, redirige vers une
    logique metier existante ; ici il n'y a rien vers quoi rediriger).
    Les entrees sont creees exclusivement par journaliser() (views.py).
    """

    list_display = ["date", "auteur_libelle", "action", "objet", "details"]
    list_filter = ["action"]
    search_fields = ["auteur_libelle", "objet", "details"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Consultation)
admin.site.register(Ordonnance)


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ["consultation", "montant_total", "montant_part_patient", "statut", "date_reglement"]
    list_filter = ["statut", "mode_reglement"]
