"""Liste des rendez-vous (vue administrateur)."""

from django.db.models import Q
from django.shortcuts import render

from ..models import RendezVous
from .utils import _paginer, _trier, admin_required


@admin_required
def liste_rendez_vous(request):
    rendez_vous = RendezVous.objects.select_related("patient", "medecin", "prestataire")

    recherche = request.GET.get("q", "").strip() or request.GET.get("recherche", "").strip()
    if recherche:
        rendez_vous = rendez_vous.filter(
            Q(patient__nom__icontains=recherche)
            | Q(patient__prenom__icontains=recherche)
            | Q(medecin__nom__icontains=recherche)
            | Q(medecin__prenom__icontains=recherche)
        )

    statut = request.GET.get("statut", "")
    if statut and statut in RendezVous.Statut.values:
        rendez_vous = rendez_vous.filter(statut=statut)

    rendez_vous = _trier(request, rendez_vous,
                         ["patient__nom", "medecin__nom", "date_heure", "statut"], "-date_heure")
    return render(request, "liste_rendez_vous.html", {
        "rendez_vous": _paginer(request, rendez_vous),
        "statut_choisi": statut if statut in RendezVous.Statut.values else "",
        "statuts": RendezVous.Statut.choices,
        "recherche": recherche,
    })


import datetime
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ..models import User


@login_required
def telecharger_ics_rendez_vous(request, pk):
    """Génère un fichier iCalendar (.ics) pour ajouter le rendez-vous dans Google / Apple Calendar."""
    rdv = get_object_or_404(
        RendezVous.objects.select_related("patient", "medecin", "prestataire"),
        pk=pk,
    )

    est_admin = request.user.role == User.Role.ADMIN
    est_medecin = (
        request.user.role == User.Role.MEDECIN
        and hasattr(request.user, "medecin")
        and rdv.medecin == request.user.medecin
    )
    est_assure = False
    if request.user.role == User.Role.ASSURE and hasattr(request.user, "patient"):
        patient = request.user.patient
        membres = [patient.pk] + list(patient.ayants_droit.values_list("pk", flat=True))
        if rdv.patient_id in membres:
            est_assure = True

    if not (est_admin or est_medecin or est_assure):
        raise PermissionDenied("Vous n'avez pas accès à ce rendez-vous.")

    dt_start = rdv.date_heure.strftime("%Y%m%dT%H%M%SZ")
    dt_end = (rdv.date_heure + datetime.timedelta(minutes=45)).strftime("%Y%m%dT%H%M%SZ")
    dt_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = f"santesn-rdv-{rdv.pk}@{request.get_host()}"

    lieu = rdv.prestataire.nom if rdv.prestataire else "Cabinet médical"
    if rdv.prestataire and rdv.prestataire.ville:
        lieu += f", {rdv.prestataire.ville}"

    description = f"Rendez-vous médical SantéSN avec Dr {rdv.medecin} ({rdv.medecin.specialite or 'Médecine générale'}). Patient : {rdv.patient.prenom} {rdv.patient.nom}."

    lignes_ics = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SantéSN//Plateforme Médicale//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dt_stamp}",
        f"DTSTART:{dt_start}",
        f"DTEND:{dt_end}",
        f"SUMMARY:RDV Médical - Dr {rdv.medecin}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{lieu}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    ics_contenu = "\r\n".join(lignes_ics) + "\r\n"
    response = HttpResponse(ics_contenu, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="rdv_santesn_{rdv.pk}.ics"'
    return response

