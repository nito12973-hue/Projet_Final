import datetime
from django.db.models import Q
from django.shortcuts import render

from ..models import Consultation, JournalActivite, Ordonnance, PriseEnCharge
from .utils import _paginer, _trier, admin_required


@admin_required
def liste_consultations(request):
    consultations = Consultation.objects.select_related(
        "patient", "medecin", "service", "prise_en_charge"
    )

    recherche = request.GET.get("q", "").strip() or request.GET.get("recherche", "").strip()
    if recherche:
        consultations = consultations.filter(
            Q(patient__nom__icontains=recherche)
            | Q(patient__prenom__icontains=recherche)
            | Q(medecin__nom__icontains=recherche)
            | Q(medecin__user__first_name__icontains=recherche)
            | Q(medecin__user__last_name__icontains=recherche)
        )

    couverture = request.GET.get("couverture", "")
    if couverture == "oui":
        consultations = consultations.filter(prise_en_charge__statut="validee")
    elif couverture == "non":
        consultations = consultations.filter(
            Q(prise_en_charge__isnull=True) | ~Q(prise_en_charge__statut="validee")
        )

    date_str = request.GET.get("date", "")
    if date_str:
        try:
            date_val = datetime.date.fromisoformat(date_str)
            consultations = consultations.filter(date_consultation__date=date_val)
        except (ValueError, TypeError):
            pass

    consultations = _trier(
        request, consultations,
        ["patient__nom", "medecin__nom", "date_consultation", "service__nom"],
        "-date_consultation",
    )
    return render(request, "liste_consultations.html", {
        "consultations": _paginer(request, consultations),
        "recherche": recherche,
        "couverture_choisie": couverture,
    })


@admin_required
def journal_activite(request):
    entrees = JournalActivite.objects.select_related("auteur").order_by("-date")

    recherche = request.GET.get("q", "").strip() or request.GET.get("recherche", "").strip()
    if recherche:
        entrees = entrees.filter(
            Q(auteur_libelle__icontains=recherche)
            | Q(action__icontains=recherche)
            | Q(objet__icontains=recherche)
        )

    action = request.GET.get("action", "")
    if action in JournalActivite.Action.values:
        entrees = entrees.filter(action=action)

    date_str = request.GET.get("date", "")
    if date_str:
        try:
            date_val = datetime.date.fromisoformat(date_str)
            entrees = entrees.filter(date__date=date_val)
        except (ValueError, TypeError):
            pass

    return render(request, "journal_activite.html", {
        "entrees": _paginer(request, entrees),
        "recherche": recherche,
        "action_choisie": action,
        "actions": JournalActivite.Action.choices,
    })
