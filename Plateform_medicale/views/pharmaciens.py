"""CRUD Pharmaciens (liste, modification d'affectation)."""

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PharmacienAffectationForm, PharmacienCreationForm
from ..models import JournalActivite, Pharmacien, User
from ..services.onboarding import construire_bilan_onboarding, envoyer_activation_utilisateur
from .utils import _paginer, _trier, journaliser, organisme_gestionnaire, role_required


def _pharmaciens_organisme(organisme):
    """Retourne les pharmaciens rattachés à l'organisme ou aux officines conventionnées de l'organisme."""
    return (
        Pharmacien.objects.select_related("user", "prestataire")
        .filter(
            Q(user__isnull=True)
            | Q(user__organisme__isnull=True)
            | Q(user__organisme=organisme)
            | Q(prestataire__conventions_organismes__organisme=organisme)
        )
        .distinct()
    )


@role_required(User.Role.GESTIONNAIRE)
def liste_pharmaciens(request):
    organisme = organisme_gestionnaire(request)
    pharmaciens = _pharmaciens_organisme(organisme)
    pharmaciens = _trier(
        request, pharmaciens, ["user__last_name", "user__email", "prestataire__nom"], "id",
    )
    return render(request, "liste_pharmaciens.html", {"pharmaciens": _paginer(request, pharmaciens)})


@role_required(User.Role.GESTIONNAIRE)
def ajouter_pharmacien(request):
    """Creation d'un pharmacien par le gestionnaire (compte + fiche + lien d'activation)."""
    organisme = organisme_gestionnaire(request)
    if request.method == "POST":
        form = PharmacienCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                utilisateur = form.save()
                if not utilisateur.organisme_id:
                    utilisateur.organisme = organisme
                    utilisateur.save(update_fields=["organisme"])
                statut_onboarding = envoyer_activation_utilisateur(utilisateur, request=request)
                journaliser(
                    request,
                    JournalActivite.Action.CREATION,
                    f"Pharmacien {utilisateur.email}",
                    f"{utilisateur.first_name} {utilisateur.last_name}",
                )
            bilan = statut_onboarding.get("bilan") or construire_bilan_onboarding(
                statut_onboarding, utilisateur, action="creation"
            )
            if bilan["niveau"] == "success":
                messages.success(request, bilan["texte_flash"])
            else:
                messages.warning(request, bilan["texte_flash"])
            return redirect("liste_pharmaciens")
    else:
        form = PharmacienCreationForm()
    return render(request, "ajouter_pharmacien.html", {"form": form})


@role_required(User.Role.GESTIONNAIRE)
def modifier_pharmacien(request, pk):
    organisme = organisme_gestionnaire(request)
    pharmacien = get_object_or_404(_pharmaciens_organisme(organisme), pk=pk)
    if request.method == "POST":
        form = PharmacienAffectationForm(request.POST, instance=pharmacien)
        if form.is_valid():
            pharmacien = form.save()
            if pharmacien.prestataire:
                messages.success(request, f"L'affectation à l'officine « {pharmacien.prestataire.nom} » a été enregistrée avec succès.")
            else:
                messages.success(request, "L'affectation du pharmacien a été enregistrée avec succès.")
            return redirect("liste_pharmaciens")
    else:
        form = PharmacienAffectationForm(instance=pharmacien)
    return render(request, "modifier_pharmacien.html", {"form": form, "pharmacien": pharmacien})
