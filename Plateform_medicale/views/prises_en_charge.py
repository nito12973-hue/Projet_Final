"""CRUD Prises en charge (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PriseEnChargeForm
from ..models import JournalActivite, PriseEnCharge
from .utils import _paginer, _trier, admin_required, journaliser


@admin_required
def liste_prises_en_charge(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        pks = request.POST.getlist("selection")
        if action in ("valider_selection", "refuser_selection") and pks:
            nouveau_statut = "validee" if action == "valider_selection" else "refusee"
            libelle_statut = "validée(s)" if nouveau_statut == "validee" else "refusée(s)"
            modifiees = PriseEnCharge.objects.filter(pk__in=pks, statut="en_attente")
            count = modifiees.count()
            if count > 0:
                from django.utils import timezone
                from ..models import Paiement
                from ..services.notifications import (
                    notifier_refus_prise_en_charge,
                    notifier_validation_prise_en_charge,
                )
                modifiees_list = list(modifiees)
                modifiees.update(
                    statut=nouveau_statut,
                    valide_par=request.user,
                    date_validation=timezone.now(),
                )
                for item in modifiees_list:
                    item.statut = nouveau_statut
                    if nouveau_statut == "validee":
                        notifier_validation_prise_en_charge(item)
                        for c in item.consultation_set.all():
                            if hasattr(c, "paiement"):
                                if c.paiement.statut == Paiement.Statut.NON_REGLE:
                                    p_calc = Paiement.calculer_pour(c)
                                    c.paiement.montant_part_assurance = p_calc.montant_part_assurance
                                    c.paiement.montant_part_patient = p_calc.montant_part_patient
                                    c.paiement.taux_applique = p_calc.taux_applique
                                    c.paiement.save()
                                else:
                                    paiement_id = c.paiement.pk
                                    part_patient_actuelle = c.paiement.montant_part_patient
                                    p_calc = Paiement.calculer_pour(c)
                                    trop_percu = part_patient_actuelle - p_calc.montant_part_patient
                                    if trop_percu > 0:
                                        journaliser(
                                            request,
                                            JournalActivite.Action.MODIFICATION,
                                            f"Régularisation comptable — Paiement #{paiement_id} ({c.patient})",
                                            f"Prise en charge #{item.pk} validée a posteriori. Trop-perçu constaté à rembourser : {trop_percu} FCFA (nouvelle part assurance : {p_calc.montant_part_assurance} FCFA)",
                                        )
                    elif nouveau_statut == "refusee":
                        notifier_refus_prise_en_charge(item)

                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    "Prises en charge (Traitement en masse)",
                    f"{count} demande(s) passa(ient) au statut : {nouveau_statut}",
                )
                messages.success(request, f"{count} prise(s) en charge {libelle_statut}.")
            else:
                messages.warning(request, "Aucune demande en attente sélectionnée.")
        return redirect("liste_prises_en_charge")

    prises_en_charge = PriseEnCharge.objects.select_related("patient")

    recherche = request.GET.get("q", "").strip()
    if recherche:
        prises_en_charge = prises_en_charge.filter(
            Q(patient__nom__icontains=recherche) | Q(patient__prenom__icontains=recherche)
        )

    statut = request.GET.get("statut", "")
    urgent = request.GET.get("urgent", "")

    if urgent == "1":
        from django.utils import timezone
        import datetime
        il_y_a_48h = timezone.now() - datetime.timedelta(hours=48)
        prises_en_charge = prises_en_charge.filter(statut="en_attente", date_demande__lte=il_y_a_48h)
    elif statut:
        prises_en_charge = prises_en_charge.filter(statut=statut)

    prises_en_charge = _trier(
        request, prises_en_charge, ["patient__nom", "date_demande", "statut"], "-date_demande",
    )
    return render(
        request,
        "liste_prises_en_charge.html",
        {
            "prises_en_charge": _paginer(request, prises_en_charge),
            "recherche": recherche,
            "statut_choisi": statut,
            "statuts": PriseEnCharge.STATUT_CHOICES,
            "urgent": urgent,
        },
    )


@admin_required
def valider_prise_en_charge(request, pk):
    """Validation unitaire rapide d une prise en charge par l administration."""
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        from django.utils import timezone
        from ..models import Paiement
        from ..services.notifications import notifier_validation_prise_en_charge
        prise_en_charge.statut = "validee"
        prise_en_charge.valide_par = request.user
        prise_en_charge.date_validation = timezone.now()
        prise_en_charge.save()

        # Recalculer les paiements des consultations rattachées
        for c in prise_en_charge.consultation_set.all():
            if hasattr(c, "paiement"):
                if c.paiement.statut == Paiement.Statut.NON_REGLE:
                    p_calc = Paiement.calculer_pour(c)
                    c.paiement.montant_part_assurance = p_calc.montant_part_assurance
                    c.paiement.montant_part_patient = p_calc.montant_part_patient
                    c.paiement.taux_applique = p_calc.taux_applique
                    c.paiement.save()
                else:
                    paiement_id = c.paiement.pk
                    part_patient_actuelle = c.paiement.montant_part_patient
                    p_calc = Paiement.calculer_pour(c)
                    trop_percu = part_patient_actuelle - p_calc.montant_part_patient
                    if trop_percu > 0:
                        journaliser(
                            request,
                            JournalActivite.Action.MODIFICATION,
                            f"Régularisation comptable — Paiement #{paiement_id} ({c.patient})",
                            f"Prise en charge validée a posteriori. Trop-perçu constaté à rembourser : {trop_percu} FCFA (nouvelle part assurance : {p_calc.montant_part_assurance} FCFA)",
                        )

        notifier_validation_prise_en_charge(prise_en_charge)
        journaliser(
            request,
            JournalActivite.Action.DECISION,
            f"Prise en charge validée : {prise_en_charge.patient}",
            f"Motif : {prise_en_charge.motif}",
        )
        messages.success(request, f"La prise en charge de {prise_en_charge.patient} a été validée avec succès.")
    return redirect("liste_prises_en_charge")


@admin_required
def refuser_prise_en_charge(request, pk):
    """Refus unitaire rapide avec motif d une prise en charge."""
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        from django.utils import timezone
        from ..services.notifications import notifier_refus_prise_en_charge
        motif_refus = request.POST.get("motif_refus", "").strip() or "Non conforme aux critères de couverture"
        prise_en_charge.statut = "refusee"
        prise_en_charge.motif_refus = motif_refus
        prise_en_charge.valide_par = request.user
        prise_en_charge.date_validation = timezone.now()
        prise_en_charge.save()

        notifier_refus_prise_en_charge(prise_en_charge)
        journaliser(
            request,
            JournalActivite.Action.DECISION,
            f"Prise en charge refusée : {prise_en_charge.patient}",
            f"Motif du refus : {motif_refus}",
        )
        messages.warning(request, f"La prise en charge de {prise_en_charge.patient} a été refusée.")
    return redirect("liste_prises_en_charge")


@admin_required
def ajouter_prise_en_charge(request):
    """A la creation, le statut est toujours 'en_attente' : le champ n'est pas propose."""
    if request.method == "POST":
        form = PriseEnChargeForm(request.POST)
        form.fields.pop("statut")
        if form.is_valid():
            prise_en_charge = form.save(commit=False)
            prise_en_charge.statut = "en_attente"
            prise_en_charge.save()
            from ..services.notifications import notifier_demande_prise_en_charge
            notifier_demande_prise_en_charge(prise_en_charge)
            messages.success(request, "Prise en charge ajoutée.")
            return redirect("liste_prises_en_charge")
    else:
        form = PriseEnChargeForm()
        form.fields.pop("statut")
    return render(request, "ajouter_prise_en_charge.html", {"form": form})


@admin_required
def modifier_prise_en_charge(request, pk):
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        ancien_statut_code = prise_en_charge.statut
        ancien_statut = prise_en_charge.get_statut_display()
        form = PriseEnChargeForm(request.POST, instance=prise_en_charge)
        if form.is_valid():
            prise_en_charge = form.save()
            nouveau_statut_code = prise_en_charge.statut
            nouveau_statut = prise_en_charge.get_statut_display()

            if nouveau_statut_code != ancien_statut_code:
                from django.utils import timezone
                from ..models import Paiement
                from ..services.notifications import (
                    notifier_refus_prise_en_charge,
                    notifier_validation_prise_en_charge,
                )
                if nouveau_statut_code == "validee":
                    prise_en_charge.valide_par = request.user
                    prise_en_charge.date_validation = timezone.now()
                    prise_en_charge.save(update_fields=["valide_par", "date_validation"])
                    for c in prise_en_charge.consultation_set.all():
                        if hasattr(c, "paiement"):
                            if c.paiement.statut == Paiement.Statut.NON_REGLE:
                                p_calc = Paiement.calculer_pour(c)
                                c.paiement.montant_part_assurance = p_calc.montant_part_assurance
                                c.paiement.montant_part_patient = p_calc.montant_part_patient
                                c.paiement.taux_applique = p_calc.taux_applique
                                c.paiement.save()
                            else:
                                paiement_id = c.paiement.pk
                                part_patient_actuelle = c.paiement.montant_part_patient
                                p_calc = Paiement.calculer_pour(c)
                                trop_percu = part_patient_actuelle - p_calc.montant_part_patient
                                if trop_percu > 0:
                                    journaliser(
                                        request,
                                        JournalActivite.Action.MODIFICATION,
                                        f"Régularisation comptable — Paiement #{paiement_id} ({c.patient})",
                                        f"Prise en charge #{prise_en_charge.pk} validée a posteriori. Trop-perçu constaté à rembourser : {trop_percu} FCFA (nouvelle part assurance : {p_calc.montant_part_assurance} FCFA)",
                                    )
                    notifier_validation_prise_en_charge(prise_en_charge)
                elif nouveau_statut_code == "refusee":
                    prise_en_charge.valide_par = request.user
                    prise_en_charge.date_validation = timezone.now()
                    prise_en_charge.save(update_fields=["valide_par", "date_validation"])
                    notifier_refus_prise_en_charge(prise_en_charge)

            journaliser(
                request,
                JournalActivite.Action.DECISION if nouveau_statut != ancien_statut else JournalActivite.Action.MODIFICATION,
                f"Prise en charge : {prise_en_charge}",
                "" if nouveau_statut == ancien_statut
                else f"statut : {ancien_statut} -> {nouveau_statut}",
            )
            messages.success(request, "Prise en charge modifiée.")
            return redirect("liste_prises_en_charge")
    else:
        form = PriseEnChargeForm(instance=prise_en_charge)
    return render(
        request,
        "modifier_prise_en_charge.html",
        {"form": form, "prise_en_charge": prise_en_charge},
    )


@admin_required
def supprimer_prise_en_charge(request, pk):
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        journaliser(request, JournalActivite.Action.SUPPRESSION, f"Prise en charge : {prise_en_charge}")
        prise_en_charge.delete()
        messages.success(request, "Prise en charge supprimée.")
        return redirect("liste_prises_en_charge")
    return render(request, "confirmer_suppression.html", {"objet": prise_en_charge, "type": "Prise en charge"})
