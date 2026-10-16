"""
Gestion et instruction des demandes de remboursement hors réseau (Gestionnaire IPM).
"""

from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import InstructionRemboursementForm
from ..models import DemandeRemboursement, JournalActivite
from ..services.notifications import (
    notifier_refus_remboursement,
    notifier_validation_remboursement,
)
from .utils import (
    _paginer,
    _trier,
    filtrer_par_organisme,
    gestionnaire_required,
    get_object_or_404_organisme,
    journaliser,
    organisme_gestionnaire,
)


@gestionnaire_required
def liste_demandes_remboursement(request):
    """Liste des demandes de remboursement hors réseau soumises par les assurés de l'organisme."""
    organisme = organisme_gestionnaire(request)
    qs_base = filtrer_par_organisme(
        request,
        DemandeRemboursement.objects.select_related("patient", "organisme", "traite_par"),
    )

    qs = qs_base
    statut_choisi = request.GET.get("statut", "")
    if statut_choisi in DemandeRemboursement.Statut.values:
        qs = qs.filter(statut=statut_choisi)
    else:
        statut_choisi = ""

    type_choisi = request.GET.get("type_soin", "")
    if type_choisi in DemandeRemboursement.TypeSoin.values:
        qs = qs.filter(type_soin=type_choisi)
    else:
        type_choisi = ""

    recherche = request.GET.get("q", "").strip()
    if recherche:
        qs = qs.filter(
            Q(numero_dossier__icontains=recherche)
            | Q(patient__nom__icontains=recherche)
            | Q(patient__prenom__icontains=recherche)
            | Q(patient__numero_carte__icontains=recherche)
            | Q(prestataire_nom__icontains=recherche)
        )

    qs = _trier(
        request,
        qs,
        ["date_demande", "date_soins", "montant_depense", "montant_rembourse_accorde", "statut"],
        "-date_demande",
    )

    nb_en_attente = qs_base.filter(statut=DemandeRemboursement.Statut.EN_ATTENTE).count()
    nb_validees = qs_base.filter(statut=DemandeRemboursement.Statut.VALIDEE).count()
    nb_remboursees = qs_base.filter(statut=DemandeRemboursement.Statut.REMBOURSEE).count()
    total_accorde = (
        qs_base.filter(
            statut__in=[DemandeRemboursement.Statut.VALIDEE, DemandeRemboursement.Statut.REMBOURSEE]
        ).aggregate(t=Sum("montant_rembourse_accorde"))["t"]
        or Decimal("0")
    )

    return render(
        request,
        "liste_demandes_remboursement.html",
        {
            "remboursements": _paginer(request, qs),
            "organisme": organisme,
            "statut_choisi": statut_choisi,
            "type_choisi": type_choisi,
            "recherche": recherche,
            "statuts_choices": DemandeRemboursement.Statut.choices,
            "types_soins": DemandeRemboursement.TypeSoin.choices,
            "nb_en_attente": nb_en_attente,
            "nb_validees": nb_validees,
            "nb_remboursees": nb_remboursees,
            "total_accorde": total_accorde,
        },
    )


@gestionnaire_required
def instruire_demande_remboursement(request, pk):
    """Examen détaillé d'une facture hors réseau, calcul de la part assurance et décision."""
    organisme = organisme_gestionnaire(request)
    demande = get_object_or_404_organisme(
        request,
        DemandeRemboursement.objects.select_related(
            "patient",
            "patient__plan_couverture",
            "patient__assure_principal",
            "patient__assure_principal__plan_couverture",
            "organisme",
            "traite_par",
        ),
        pk=pk,
    )

    taux_calcule, montant_estime = demande.calculer_estimation()
    plafond_restant = demande.patient.plafond_annuel_restant(
        annee=demande.date_soins.year if demande.date_soins else None
    )

    if request.method == "POST":
        form = InstructionRemboursementForm(request.POST, demande=demande)
        if form.is_valid():
            decision = form.cleaned_data["decision"]
            maintenant = timezone.now()
            with transaction.atomic():
                demande_verrouillee = (
                    DemandeRemboursement.objects.select_for_update()
                    .select_related("patient", "organisme")
                    .get(pk=demande.pk)
                )
                if decision == "valider":
                    demande_verrouillee.statut = DemandeRemboursement.Statut.VALIDEE
                    demande_verrouillee.montant_rembourse_accorde = form.cleaned_data["montant_rembourse_accorde"]
                    demande_verrouillee.taux_applique = taux_calcule
                    demande_verrouillee.mode_remboursement = form.cleaned_data.get("mode_remboursement") or ""
                    demande_verrouillee.reference_reglement = form.cleaned_data.get("reference_reglement") or ""
                    demande_verrouillee.date_decision = maintenant
                    demande_verrouillee.traite_par = request.user
                    demande_verrouillee.motif_refus = ""
                    demande_verrouillee.save()

                    notifier_validation_remboursement(demande_verrouillee)
                    journaliser(
                        request,
                        JournalActivite.Action.DECISION,
                        f"Remboursement {demande_verrouillee.numero_dossier} ({demande_verrouillee.patient})",
                        f"Approuvé : {demande_verrouillee.montant_rembourse_accorde:,.0f} FCFA sur {demande_verrouillee.montant_depense:,.0f} FCFA".replace(",", " "),
                        organisme=organisme,
                    )
                    messages.success(
                        request,
                        f"Demande {demande_verrouillee.numero_dossier} validée ({demande_verrouillee.montant_rembourse_accorde:,.0f} FCFA).".replace(",", " "),
                    )

                elif decision == "rembourser":
                    demande_verrouillee.statut = DemandeRemboursement.Statut.REMBOURSEE
                    demande_verrouillee.montant_rembourse_accorde = form.cleaned_data["montant_rembourse_accorde"]
                    demande_verrouillee.taux_applique = taux_calcule
                    demande_verrouillee.mode_remboursement = form.cleaned_data["mode_remboursement"]
                    demande_verrouillee.reference_reglement = form.cleaned_data.get("reference_reglement") or ""
                    if not demande_verrouillee.date_decision:
                        demande_verrouillee.date_decision = maintenant
                    demande_verrouillee.date_reglement = maintenant
                    demande_verrouillee.traite_par = request.user
                    demande_verrouillee.motif_refus = ""
                    demande_verrouillee.save()

                    notifier_validation_remboursement(demande_verrouillee)
                    journaliser(
                        request,
                        JournalActivite.Action.REGLEMENT,
                        f"Remboursement {demande_verrouillee.numero_dossier} ({demande_verrouillee.patient})",
                        f"Réglé : {demande_verrouillee.montant_rembourse_accorde:,.0f} FCFA via {demande_verrouillee.get_mode_remboursement_display()}".replace(",", " "),
                        organisme=organisme,
                    )
                    messages.success(
                        request,
                        f"Demande {demande_verrouillee.numero_dossier} approuvée et marquée comme remboursée.",
                    )

                elif decision == "refuser":
                    demande_verrouillee.statut = DemandeRemboursement.Statut.REFUSEE
                    demande_verrouillee.motif_refus = form.cleaned_data["motif_refus"]
                    demande_verrouillee.montant_rembourse_accorde = Decimal("0")
                    demande_verrouillee.date_decision = maintenant
                    demande_verrouillee.traite_par = request.user
                    demande_verrouillee.save()

                    notifier_refus_remboursement(demande_verrouillee)
                    journaliser(
                        request,
                        JournalActivite.Action.DECISION,
                        f"Remboursement {demande_verrouillee.numero_dossier} ({demande_verrouillee.patient})",
                        f"Refusé — Motif : {demande_verrouillee.motif_refus}",
                        organisme=organisme,
                    )
                    messages.warning(
                        request,
                        f"Demande {demande_verrouillee.numero_dossier} refusée.",
                    )

            return redirect("liste_demandes_remboursement")
    else:
        form = InstructionRemboursementForm(demande=demande)

    return render(
        request,
        "instruire_demande_remboursement.html",
        {
            "demande": demande,
            "form": form,
            "taux_calcule": taux_calcule,
            "montant_estime": montant_estime,
            "plafond_restant": plafond_restant,
        },
    )


@gestionnaire_required
@require_POST
def marquer_remboursement_regle(request, pk):
    """Action rapide pour confirmer le virement/règlement d'un remboursement déjà validé."""
    organisme = organisme_gestionnaire(request)
    demande = get_object_or_404_organisme(
        request,
        DemandeRemboursement.objects.select_related("patient", "organisme"),
        pk=pk,
    )
    if demande.statut != DemandeRemboursement.Statut.VALIDEE:
        messages.error(request, "Seule une demande préalablement validée peut être marquée comme remboursée.")
        return redirect("liste_demandes_remboursement")

    mode = request.POST.get("mode_remboursement") or demande.mode_remboursement or DemandeRemboursement.ModeRemboursement.MOBILE_MONEY
    if mode not in DemandeRemboursement.ModeRemboursement.values:
        mode = DemandeRemboursement.ModeRemboursement.MOBILE_MONEY
    reference = (request.POST.get("reference_reglement") or demande.reference_reglement or "").strip()

    with transaction.atomic():
        demande.statut = DemandeRemboursement.Statut.REMBOURSEE
        demande.mode_remboursement = mode
        demande.reference_reglement = reference
        demande.date_reglement = timezone.now()
        demande.traite_par = request.user
        demande.save(update_fields=["statut", "mode_remboursement", "reference_reglement", "date_reglement", "traite_par"])

        notifier_validation_remboursement(demande)
        journaliser(
            request,
            JournalActivite.Action.REGLEMENT,
            f"Remboursement {demande.numero_dossier} ({demande.patient})",
            f"Liquidation confirmée : {demande.montant_rembourse_accorde:,.0f} FCFA ({demande.get_mode_remboursement_display()})".replace(",", " "),
            organisme=organisme,
        )

    messages.success(request, f"Le remboursement {demande.numero_dossier} a été marqué comme réglé.")
    return redirect("liste_demandes_remboursement")
