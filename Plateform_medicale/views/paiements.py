"""
Gestion des paiements : liste, export CSV et règlement manuel.
"""

import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..forms import PaiementReglementForm
from ..models import JournalActivite, Paiement, User
from .utils import _cellule_csv, _paginer, _trier, admin_required, journaliser


def _filtrer_paiements(request):
    """Filtres partages entre la liste et l'export CSV des paiements."""
    paiements = Paiement.objects.select_related(
        "consultation", "consultation__patient", "consultation__service"
    )

    statut = request.GET.get("statut", "")
    if statut:
        paiements = paiements.filter(statut=statut)

    recherche = request.GET.get("q", "").strip()
    if recherche:
        paiements = paiements.filter(
            Q(consultation__patient__nom__icontains=recherche)
            | Q(consultation__patient__prenom__icontains=recherche)
        )

    paiements = _trier(
        request, paiements,
        ["consultation__patient__nom", "montant_total", "montant_part_assurance", "montant_part_patient", "statut"],
        "-consultation__date_consultation",
    )

    return paiements, {"statut": statut, "recherche": recherche}


@admin_required
def liste_paiements(request):
    paiements, filtres = _filtrer_paiements(request)

    totaux = Paiement.objects.aggregate(
        total_regle=Sum("montant_part_patient", filter=Q(statut=Paiement.Statut.REGLE)),
        total_non_regle=Sum("montant_part_patient", filter=Q(statut=Paiement.Statut.NON_REGLE)),
    )

    contexte = {
        "paiements": _paginer(request, paiements),
        "statut_choisi": filtres["statut"],
        "statuts": Paiement.Statut.choices,
        "recherche": filtres["recherche"],
        "total_regle": totaux["total_regle"] or 0,
        "total_non_regle": totaux["total_non_regle"] or 0,
    }
    return render(request, "liste_paiements.html", contexte)


@admin_required
def exporter_paiements_csv(request):
    paiements, _ = _filtrer_paiements(request)

    reponse = HttpResponse(content_type="text/csv")
    reponse["Content-Disposition"] = 'attachment; filename="paiements_santesn.csv"'
    reponse.write("\ufeff")  # BOM : Excel (FR) detecte l'UTF-8 sans le confondre avec l'encodage local.
    ecrivain = csv.writer(reponse, delimiter=";")
    ecrivain.writerow([
        "Reference", "Patient", "Date de consultation", "Montant total",
        "Part assurance", "Part patient", "Statut", "Mode de reglement",
        "Date de reglement",
    ])
    for paiement in paiements:
        ecrivain.writerow([_cellule_csv(v) for v in [
            paiement.pk,
            str(paiement.consultation.patient),
            paiement.consultation.date_consultation.strftime("%d/%m/%Y %H:%M"),
            paiement.montant_total,
            paiement.montant_part_assurance,
            paiement.montant_part_patient,
            paiement.get_statut_display(),
            paiement.get_mode_reglement_display() if paiement.mode_reglement else "",
            paiement.date_reglement.strftime("%d/%m/%Y %H:%M") if paiement.date_reglement else "",
        ]])
    return reponse


@admin_required
def marquer_paiement_regle(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    if paiement.statut == Paiement.Statut.REGLE:
        messages.info(request, "Ce paiement est déjà réglé.")
        return redirect("liste_paiements")

    if request.method == "POST":
        form = PaiementReglementForm(request.POST, instance=paiement)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.statut = Paiement.Statut.REGLE
            paiement.date_reglement = timezone.now()
            # Qui a constate l'encaissement : jamais saisi, toujours deduit
            # du compte connecte. En especes, c'est la seule trace de la
            # personne qui a recu l'argent.
            paiement.enregistre_par = request.user
            paiement.save()
            journaliser(
                request, JournalActivite.Action.REGLEMENT,
                f"Paiement #{paiement.pk} · {paiement.consultation.patient}",
                f"{paiement.montant_part_patient} F CFA · {paiement.get_mode_reglement_display()}",
            )
            messages.success(request, f"Paiement #{paiement.pk} marqué comme réglé.")
            return redirect("liste_paiements")
    else:
        form = PaiementReglementForm(instance=paiement)

    return render(request, "marquer_paiement_regle.html", {
        "paiement": paiement,
        "form": form,
    })


@login_required
def recu_paiement(request, pk):
    """Reçu / Quittance officielle de paiement au format A5/Ticket."""
    paiement = get_object_or_404(
        Paiement.objects.select_related(
            "consultation__patient",
            "consultation__medecin",
            "consultation__service",
            "consultation__prise_en_charge",
            "consultation__patient__plan_couverture",
            "consultation__patient__assure_principal__plan_couverture",
            "enregistre_par",
        ),
        pk=pk,
    )

    est_admin = request.user.role == User.Role.ADMIN
    est_medecin = (
        request.user.role == User.Role.MEDECIN
        and hasattr(request.user, "medecin")
        and paiement.consultation.medecin == request.user.medecin
    )
    est_assure = False
    if request.user.role == User.Role.ASSURE and hasattr(request.user, "patient"):
        patient_assure = request.user.patient
        membres = [patient_assure.pk] + list(patient_assure.ayants_droit.values_list("pk", flat=True))
        if paiement.consultation.patient_id in membres:
            est_assure = True

    if not (est_admin or est_medecin or est_assure):
        raise PermissionDenied("Vous n'avez pas accès à ce reçu de paiement.")

    date_ref = paiement.date_reglement or paiement.consultation.date_consultation
    reference_recu = f"REC-{date_ref.strftime('%Y%m%d')}-{paiement.pk:05d}"

    return render(request, "recu_paiement.html", {
        "paiement": paiement,
        "reference_recu": reference_recu,
    })




