"""
Espace Pharmacien : dashboard, scanner d'ordonnance, validation de délivrance,
historique des délivrances.
"""

import datetime
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ..models import Delivrance, JournalActivite, Ordonnance, User
from .utils import (
    _paginer,
    RECHERCHE_ORDONNANCE_MAX,
    RECHERCHE_ORDONNANCE_MIN,
    journaliser,
    role_required,
)


def _pharmacien_courant(request):
    return getattr(request.user, "pharmacien", None)


@role_required(User.Role.PHARMACIEN)
def dashboard_pharmacien(request):
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")

    delivrances = Delivrance.objects.filter(pharmacien=pharmacien)
    aujourd_hui = timezone.localdate()
    delivrances_du_jour = delivrances.filter(
        date_delivrance__date=aujourd_hui
    ).select_related(
        "ordonnance__consultation__patient",
        "ordonnance__consultation__medecin",
    ).order_by("-date_delivrance")

    stats_financieres = delivrances_du_jour.aggregate(
        total=Sum("montant_total"),
        part_assurance=Sum("montant_part_assurance"),
        part_patient=Sum("montant_part_patient"),
    )

    contexte = {
        "pharmacien": pharmacien,
        "delivrances_du_jour": delivrances_du_jour,
        "total_delivrances_jour": delivrances_du_jour.count(),
        "total_delivrances_global": delivrances.count(),
        "montant_total_jour": stats_financieres["total"] or Decimal("0.00"),
        "part_assurance_jour": stats_financieres["part_assurance"] or Decimal("0.00"),
        "part_patient_jour": stats_financieres["part_patient"] or Decimal("0.00"),
        "dernieres_delivrances": delivrances.select_related(
            "ordonnance__consultation__patient",
            "ordonnance__consultation__medecin",
        ).order_by("-date_delivrance")[:6],
    }
    return render(request, "dashboard_pharmacien.html", contexte)


@role_required(User.Role.PHARMACIEN)
def scanner_ordonnance(request):
    """Comptoir du pharmacien : verification d'une ordonnance avant delivrance.

    DEUX chemins, volontairement dissymetriques :

    1. Le code (scanne ou saisi) fait une correspondance EXACTE. Un code
       identifie une ordonnance et une seule : on peut donc l'ouvrir
       directement. C'est le chemin normal, inchange.

    2. La recherche manuelle (nom du patient ou fragment de code) est le
       repli quand le QR est illisible, l'impression pale ou le code mal
       recopie. Elle ne selectionne JAMAIS d'ordonnance, meme s'il n'y a
       qu'un seul resultat : elle affiche une liste et le pharmacien
       designe explicitement la bonne. Delivrer le mauvais traitement
       parce qu'un logiciel a "devine" est un risque qu'on n'accepte pas.

    Le bouton de selection d'un resultat renvoie simplement le code exact
    dans le chemin 1 : une seule logique d'ouverture, donc une seule
    surface a securiser.
    """
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")

    ordonnance = None
    resultats = None
    recherche = ""
    trop_de_resultats = False

    if request.method == "POST":
        code = request.POST.get("code_qr", "").strip().upper()
        recherche = request.POST.get("recherche", "").strip()

        if code:
            try:
                ordonnance = Ordonnance.objects.select_related(
                    "consultation__patient", "consultation__medecin", "delivrance"
                ).get(code_qr=code)
            except Ordonnance.DoesNotExist:
                messages.error(request, "Aucune ordonnance ne correspond à ce code.")

        elif recherche:
            # Longueur minimale : une recherche d'un caractere listerait une
            # bonne partie des patients de la plateforme. Ce sont des donnees
            # medicales, on ne les enumere pas.
            if len(recherche) < RECHERCHE_ORDONNANCE_MIN:
                messages.error(
                    request,
                    f"Saisissez au moins {RECHERCHE_ORDONNANCE_MIN} caractères "
                    "pour lancer une recherche.",
                )
            else:
                trouvees = list(
                    Ordonnance.objects.select_related(
                        "consultation__patient", "consultation__medecin", "delivrance"
                    )
                    .filter(
                        Q(consultation__patient__nom__icontains=recherche)
                        | Q(consultation__patient__prenom__icontains=recherche)
                        | Q(code_qr__icontains=recherche)
                    )
                    .order_by("-date_creation")[: RECHERCHE_ORDONNANCE_MAX + 1]
                )
                # On demande un element de plus que la limite : sa presence
                # signale qu'il y en avait davantage, sans second COUNT.
                trop_de_resultats = len(trouvees) > RECHERCHE_ORDONNANCE_MAX
                resultats = trouvees[:RECHERCHE_ORDONNANCE_MAX]
                if not resultats:
                    messages.error(
                        request,
                        "Aucune ordonnance ne correspond à cette recherche.",
                    )
                elif trop_de_resultats:
                    messages.warning(
                        request,
                        f"Plus de {RECHERCHE_ORDONNANCE_MAX} ordonnances correspondent. "
                        "Précisez le nom du patient.",
                    )

    return render(
        request,
        "scanner_ordonnance.html",
        {
            "ordonnance": ordonnance,
            "integrite": ordonnance.verifier_integrite() if ordonnance else None,
            "resultats": resultats,
            "recherche": recherche,
            "trop_de_resultats": trop_de_resultats,
        },
    )


@role_required(User.Role.PHARMACIEN)
@require_POST
def valider_delivrance(request, pk):
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")
    code_qr = request.POST.get("code_qr", "").strip().upper()
    if not code_qr:
        raise Http404("Code QR manquant.")

    with transaction.atomic():
        try:
            ordonnance = Ordonnance.objects.select_for_update().get(pk=pk, code_qr=code_qr)
        except Ordonnance.DoesNotExist:
            raise Http404("Aucune ordonnance ne correspond à ce code.")

        if ordonnance.est_annulee:
            messages.error(
                request,
                f"Ordonnance annulée par le prescripteur ({ordonnance.motif_annulation})."
            )
        elif hasattr(ordonnance, "delivrance") or ordonnance.statut == Ordonnance.Statut.DELIVRE:
            messages.error(request, "Cette ordonnance a déjà été délivrée.")
        elif ordonnance.est_expiree:
            messages.error(
                request,
                "Cette ordonnance a dépassé sa durée de validité et ne peut plus être délivrée."
            )
        elif ordonnance.verifier_integrite() == Ordonnance.Integrite.ALTEREE:
            # Contenu modifie apres la prescription : on ne delivre pas, et
            # on laisse une trace pour l'administrateur.
            journaliser(
                request, JournalActivite.Action.INTEGRITE,
                f"Ordonnance {ordonnance.code_qr}",
                details="Délivrance refusée : sceau d'intégrité invalide.",
            )
            messages.error(
                request,
                "Délivrance refusée : le contenu de cette ordonnance a été modifié "
                "après sa prescription (sceau d'intégrité invalide). "
                "Contactez le médecin prescripteur."
            )
        else:
            montant_str = request.POST.get("montant_total", "").strip().replace(",", ".")
            try:
                montant_total = Decimal(montant_str) if montant_str else Decimal("0.00")
                if montant_total < Decimal("0.00"):
                    montant_total = Decimal("0.00")
            except (ValueError, ArithmeticError):
                montant_total = Decimal("0.00")

            patient = ordonnance.consultation.patient
            taux = patient.taux_couverture or Decimal("0.00")

            delivrance = Delivrance(
                ordonnance=ordonnance,
                pharmacien=pharmacien,
                montant_total=montant_total,
                taux_couverture=taux,
            )
            delivrance.calculer_partages()
            delivrance.save()

            ordonnance.statut = Ordonnance.Statut.DELIVRE
            ordonnance.save(update_fields=["statut"])
            from ..services.notifications import notifier_delivrance_effectuee
            notifier_delivrance_effectuee(delivrance)

            lignes_servies = request.POST.getlist("lignes_servies")
            total_lignes = ordonnance.lignes.count()
            est_partiel = (total_lignes > 0 and len(lignes_servies) < total_lignes)

            if montant_total > Decimal("0.00"):
                detail_partage = (
                    f"Total : {delivrance.montant_total:,.0f} FCFA "
                    f"(Prise en charge IPM : {delivrance.montant_part_assurance:,.0f} FCFA | "
                    f"Ticket modérateur : {delivrance.montant_part_patient:,.0f} FCFA)."
                )
                if est_partiel:
                    messages.success(
                        request,
                        f"Délivrance partielle validée ({len(lignes_servies)}/{total_lignes} médicaments servis). {detail_partage}",
                        extra_tags="succes-critique",
                    )
                else:
                    messages.success(
                        request,
                        f"Délivrance complète validée. {detail_partage}",
                        extra_tags="succes-critique",
                    )
            else:
                messages.success(request, "Délivrance validée.", extra_tags="succes-critique")

    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("historique_delivrances")



@role_required(User.Role.PHARMACIEN)
def historique_delivrances(request):
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")

    delivrances = Delivrance.objects.filter(pharmacien=pharmacien).select_related(
        "ordonnance__consultation__patient", "ordonnance__consultation__medecin"
    ).order_by("-date_delivrance")

    # Le pharmacien revient sur une delivrance passee pour une raison : un
    # patient conteste, ou il faut retrouver le jour d'une remise. D'ou une
    # recherche (patient ou code) et un filtre par date, rien de plus.
    recherche = request.GET.get("q", "").strip()
    if recherche:
        delivrances = delivrances.filter(
            Q(ordonnance__consultation__patient__nom__icontains=recherche)
            | Q(ordonnance__consultation__patient__prenom__icontains=recherche)
            | Q(ordonnance__code_qr__icontains=recherche)
        )

    date_filtre = request.GET.get("date", "")
    if date_filtre:
        try:
            date_valide = datetime.date.fromisoformat(date_filtre)
        except ValueError:
            date_filtre = ""
        else:
            delivrances = delivrances.filter(date_delivrance__date=date_valide)

    return render(request, "historique_delivrances.html", {
        "delivrances": _paginer(request, delivrances),
        "recherche": recherche,
        "date_choisie": date_filtre,
    })
