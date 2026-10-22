"""CRUD Services médicaux (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ServiceMedicalForm
from ..models import JournalActivite, Organisme, ServiceMedical, User
from .utils import _paginer, _trier, journaliser, organisme_gestionnaire, role_required


def _services_organisme(organisme):
    """Retourne les services médicaux conventionnés avec l'organisme ou généraux."""
    if not organisme:
        return ServiceMedical.objects.none()
    filtres = (
        Q(prestataire__conventions_organismes__organisme=organisme)
        | Q(prestataire__isnull=True)
    )
    if organisme.code == Organisme.CODE_DEFAUT:
        filtres = filtres | Q(prestataire__conventions_organismes__isnull=True)
    return ServiceMedical.objects.filter(filtres).distinct()


@role_required(User.Role.GESTIONNAIRE)
def liste_services(request):
    organisme = organisme_gestionnaire(request)
    services_qs = _services_organisme(organisme)
    services = _trier(request, services_qs, ["nom", "prix"], "nom")
    return render(request, "liste_services.html", {"services": _paginer(request, services)})


@role_required(User.Role.GESTIONNAIRE)
def ajouter_service(request):
    organisme = organisme_gestionnaire(request)
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST, organisme=organisme)
        if form.is_valid():
            form.save()
            messages.success(request, "Service médical ajouté.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm(organisme=organisme)
    return render(request, "ajouter_service.html", {"form": form})


@role_required(User.Role.GESTIONNAIRE)
def modifier_service(request, pk):
    organisme = organisme_gestionnaire(request)
    service = get_object_or_404(_services_organisme(organisme), pk=pk)
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST, instance=service, organisme=organisme)
        if form.is_valid():
            form.save()
            messages.success(request, "Service médical modifié.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm(instance=service, organisme=organisme)
    return render(request, "modifier_service.html", {"form": form, "service": service})


@role_required(User.Role.GESTIONNAIRE)
def supprimer_service(request, pk):
    organisme = organisme_gestionnaire(request)
    service = get_object_or_404(_services_organisme(organisme), pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                nom_service = str(service)
                service.delete()
                journaliser(request, JournalActivite.Action.SUPPRESSION, f"Service médical : {nom_service}")
                messages.success(request, "Service médical supprimé.")
                return redirect("liste_services")
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce service médical : des consultations protégées y sont rattachées.")
            return redirect("liste_services")
    return render(request, "confirmer_suppression.html", {"objet": service, "type": "Service"})
