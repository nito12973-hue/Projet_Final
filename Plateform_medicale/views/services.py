"""CRUD Services médicaux (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ServiceMedicalForm
from ..models import JournalActivite, ServiceMedical
from .utils import _paginer, _trier, admin_required, journaliser


@admin_required
def liste_services(request):
    services = _trier(request, ServiceMedical.objects.all(), ["nom", "prix"], "nom")
    return render(request, "liste_services.html", {"services": _paginer(request, services)})


@admin_required
def ajouter_service(request):
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service médical ajouté.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm()
    return render(request, "ajouter_service.html", {"form": form})


@admin_required
def modifier_service(request, pk):
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


@admin_required
def supprimer_service(request, pk):
    service = get_object_or_404(ServiceMedical, pk=pk)
    if request.method == "POST":
        journaliser(request, JournalActivite.Action.SUPPRESSION, f"Service médical : {service}")
        service.delete()
        messages.success(request, "Service médical supprimé.")
        return redirect("liste_services")
    return render(request, "confirmer_suppression.html", {"objet": service, "type": "Service"})
