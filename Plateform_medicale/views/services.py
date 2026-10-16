"""CRUD Services médicaux (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ServiceMedicalForm
from ..models import JournalActivite, ServiceMedical, User
from .utils import _paginer, _trier, journaliser, organisme_gestionnaire, role_required


@role_required(User.Role.GESTIONNAIRE)
def liste_services(request):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    services = _trier(request, ServiceMedical.objects.all(), ["nom", "prix"], "nom")
    return render(request, "liste_services.html", {"services": _paginer(request, services)})


@role_required(User.Role.GESTIONNAIRE)
def ajouter_service(request):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service médical ajouté.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm()
    return render(request, "ajouter_service.html", {"form": form})


@role_required(User.Role.GESTIONNAIRE)
def modifier_service(request, pk):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    service = get_object_or_404(ServiceMedical, pk=pk)
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service médical modifié.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm(instance=service)
    return render(request, "modifier_service.html", {"form": form, "service": service})


@role_required(User.Role.GESTIONNAIRE)
def supprimer_service(request, pk):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    service = get_object_or_404(ServiceMedical, pk=pk)
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
