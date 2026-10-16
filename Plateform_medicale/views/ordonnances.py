"""Liste des ordonnances (vue administrateur)."""

from django.db.models import Q
from django.shortcuts import render

from ..models import Ordonnance, User
from .utils import _paginer, _trier, filtrer_par_organisme, role_required


@role_required(User.Role.GESTIONNAIRE)
def liste_ordonnances(request):
    ordonnances = Ordonnance.objects.select_related(
        "consultation__patient", "consultation__patient__organisme", "consultation__medecin", "delivrance"
    )
    if request.user.role == User.Role.GESTIONNAIRE:
        ordonnances = filtrer_par_organisme(
            request, ordonnances, champ="consultation__patient__organisme"
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
