"""Liste des ordonnances (vue administrateur)."""

from django.db.models import Q
from django.shortcuts import render

from ..models import Ordonnance
from .utils import _paginer, _trier, admin_required


@admin_required
def liste_ordonnances(request):
    ordonnances = Ordonnance.objects.select_related(
        "consultation__patient", "consultation__medecin", "delivrance"
    )

    recherche = request.GET.get("q", "").strip()
    if recherche:
        ordonnances = ordonnances.filter(
            Q(consultation__patient__nom__icontains=recherche)
            | Q(consultation__patient__prenom__icontains=recherche)
            | Q(code_qr__icontains=recherche)
        )

    delivree = request.GET.get("delivrance", "") or request.GET.get("delivree", "")
    if delivree == "oui":
        ordonnances = ordonnances.filter(delivrance__isnull=False)
    elif delivree == "non":
        ordonnances = ordonnances.filter(delivrance__isnull=True)

    ordonnances = _trier(
        request, ordonnances,
        ["consultation__patient__nom", "date_creation"],
        "-date_creation",
    )
    return render(request, "liste_ordonnances.html", {
        "ordonnances": _paginer(request, ordonnances),
        "recherche": recherche,
        "delivree_choisie": delivree,
    })
