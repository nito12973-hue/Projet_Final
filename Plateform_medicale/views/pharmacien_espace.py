"""
Espace Pharmacien : dashboard, scanner d'ordonnance, validation de délivrance,
historique des délivrances.
"""

import datetime

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import Delivrance, Ordonnance, Pharmacien, User
from .utils import _paginer, RECHERCHE_ORDONNANCE_MAX, RECHERCHE_ORDONNANCE_MIN, role_required


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

    contexte = {
        "pharmacien": pharmacien,
        "delivrances_du_jour": delivrances_du_jour,
        "total_delivrances_jour": delivrances_du_jour.count(),
        "total_delivrances_global": delivrances.count(),
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
    ordonnance = get_object_or_404(Ordonnance, pk=pk, code_qr=code_qr)
    if ordonnance.est_annulee:
        messages.error(
            request,
            f"Ordonnance annulée par le prescripteur ({ordonnance.motif_annulation})."
        )
    elif hasattr(ordonnance, "delivrance"):
        messages.error(request, "Cette ordonnance a déjà été délivrée.")
    else:
        delivrance = Delivrance.objects.create(ordonnance=ordonnance, pharmacien=pharmacien)
        ordonnance.statut = Ordonnance.Statut.DELIVRE
        ordonnance.save(update_fields=["statut"])
        from ..services.notifications import notifier_delivrance_effectuee
        notifier_delivrance_effectuee(delivrance)
        messages.success(request, "Délivrance validée.", extra_tags="succes-critique")
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
