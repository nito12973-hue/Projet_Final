"""CRUD Pharmaciens (liste, modification d'affectation)."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PharmacienAffectationForm
from ..models import Pharmacien
from .utils import _paginer, _trier, admin_required


@admin_required
def liste_pharmaciens(request):
    pharmaciens = Pharmacien.objects.select_related("user", "prestataire")
    pharmaciens = _trier(
        request, pharmaciens, ["user__last_name", "user__email", "prestataire__nom"], "id",
    )
    return render(request, "liste_pharmaciens.html", {"pharmaciens": _paginer(request, pharmaciens)})


@admin_required
def modifier_pharmacien(request, pk):
    pharmacien = get_object_or_404(Pharmacien, pk=pk)
    if request.method == "POST":
        form = PharmacienAffectationForm(request.POST, instance=pharmacien)
        if form.is_valid():
            form.save()
            messages.success(request, "Pharmacien modifié.")
            return redirect("liste_pharmaciens")
    else:
        form = PharmacienAffectationForm(instance=pharmacien)
    return render(request, "modifier_pharmacien.html", {"form": form, "pharmacien": pharmacien})
