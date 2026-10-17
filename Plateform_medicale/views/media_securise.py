"""
Contrôleur sécurisé de distribution des fichiers médias sensibles (SantéSN).
Empêche tout accès direct ou non autorisé aux ordonnances, feuilles de soins,
actes d'état-civil et justificatifs de remboursement.
Supporte :
1. Nginx X-Accel-Redirect (haute performance en production Docker)
2. Django FileResponse (streaming protégé en développement local)
3. Repli base de données FichierMedia (persistance serverless Vercel sans perte)
"""

import mimetypes
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404

from ..models import DemandeRemboursement, FichierMedia, Patient, User


def _finaliser_reponse_fichier(reponse, nom_fichier):
    """Sécurise les headers de téléchargement : nosniff et assainissement du nom de fichier."""
    nom_propre = os.path.basename(nom_fichier).replace('"', '').replace('\n', '').replace('\r', '')
    reponse["Content-Disposition"] = f'inline; filename="{nom_propre}"'
    reponse["X-Content-Type-Options"] = "nosniff"
    return reponse


@login_required
def telecharger_justificatif_remboursement(request, pk):
    """
    Téléchargement sécurisé d'un justificatif de remboursement hors réseau.
    Matrice des droits :
    - Assuré propriétaire du dossier : AUTORISÉ (200)
    - Gestionnaire de l'organisme assureur du dossier : AUTORISÉ (200)
    - Autre assuré (même IPM ou IPM tierce) : REFUSÉ (404)
    - Gestionnaire d'un autre organisme : REFUSÉ (404)
    - Administrateur IT (infrastructure) : REFUSÉ (403 Secret médical)
    """
    if request.user.role == User.Role.ADMIN:
        raise PermissionDenied("L'administrateur technique n'a pas accès aux pièces médicales confidentielles.")

    remboursement = get_object_or_404(
        DemandeRemboursement.objects.select_related("patient", "patient__user", "organisme"),
        pk=pk,
    )

    est_proprietaire = (
        request.user.role == User.Role.ASSURE
        and remboursement.patient.user_id == request.user.pk
    )
    est_gestionnaire_organisme = (
        request.user.role == User.Role.GESTIONNAIRE
        and request.user.organisme_id == remboursement.organisme_id
    )

    if not (est_proprietaire or est_gestionnaire_organisme):
        raise Http404("Document introuvable ou accès non autorisé.")

    if not remboursement.justificatif:
        raise Http404("Aucun fichier justificatif n'est associé à cette demande.")

    nom_fichier = os.path.basename(remboursement.justificatif.name)
    type_mime, _ = mimetypes.guess_type(nom_fichier)
    type_mime = type_mime or "application/octet-stream"

    # 1. Mode Production Nginx (X-Accel-Redirect)
    if getattr(settings, "USE_X_ACCEL_REDIRECT", False):
        reponse = HttpResponse(content_type=type_mime)
        reponse["X-Accel-Redirect"] = f"/protected_media/{remboursement.justificatif.name}"
        return _finaliser_reponse_fichier(reponse, nom_fichier)

    # 2. Mode standard avec fichier présent sur le système de fichiers
    try:
        fichier_disque = remboursement.justificatif.open("rb")
        reponse = FileResponse(fichier_disque, content_type=type_mime)
        return _finaliser_reponse_fichier(reponse, nom_fichier)
    except (FileNotFoundError, OSError):
        pass

    # 3. Repli base de données FichierMedia (Architecture serverless Vercel)
    chemin_media = remboursement.justificatif.name
    fichier_db = FichierMedia.objects.filter(chemin__icontains=nom_fichier).first()
    if fichier_db and fichier_db.contenu:
        reponse = HttpResponse(fichier_db.contenu, content_type=fichier_db.type_mime or type_mime)
        return _finaliser_reponse_fichier(reponse, nom_fichier)

    raise Http404("Le fichier physique est introuvable sur le stockage.")


@login_required
def telecharger_piece_identite_patient(request, pk):
    """Téléchargement sécurisé des pièces d'état civil d'un patient / ayant droit."""
    if request.user.role == User.Role.ADMIN:
        raise PermissionDenied("L'administrateur technique n'a pas accès aux pièces d'état civil des assurés.")

    patient = get_object_or_404(
        Patient.objects.select_related("user", "assure_principal", "organisme"),
        pk=pk,
    )

    est_proprietaire = (
        request.user.role == User.Role.ASSURE
        and (patient.user_id == request.user.pk or (patient.assure_principal and patient.assure_principal.user_id == request.user.pk))
    )
    est_gestionnaire_organisme = (
        request.user.role == User.Role.GESTIONNAIRE
        and request.user.organisme_id == patient.organisme_id
    )

    if not (est_proprietaire or est_gestionnaire_organisme):
        raise Http404("Document introuvable ou accès non autorisé.")

    if not patient.document_justificatif:
        raise Http404("Aucun document justificatif n'est associé à ce dossier.")

    nom_fichier = os.path.basename(patient.document_justificatif.name)
    type_mime, _ = mimetypes.guess_type(nom_fichier)
    type_mime = type_mime or "application/octet-stream"

    if getattr(settings, "USE_X_ACCEL_REDIRECT", False):
        reponse = HttpResponse(content_type=type_mime)
        reponse["X-Accel-Redirect"] = f"/protected_media/{patient.document_justificatif.name}"
        return _finaliser_reponse_fichier(reponse, nom_fichier)

    try:
        fichier_disque = patient.document_justificatif.open("rb")
        reponse = FileResponse(fichier_disque, content_type=type_mime)
        return _finaliser_reponse_fichier(reponse, nom_fichier)
    except (FileNotFoundError, OSError):
        pass

    fichier_db = FichierMedia.objects.filter(chemin__icontains=nom_fichier).first()
    if fichier_db and fichier_db.contenu:
        reponse = HttpResponse(fichier_db.contenu, content_type=fichier_db.type_mime or type_mime)
        return _finaliser_reponse_fichier(reponse, nom_fichier)

    raise Http404("Le fichier physique est introuvable.")


@login_required
def telecharger_devis_prise_en_charge(request, pk):
    """
    Téléchargement sécurisé du devis médical d'une prise en charge (PEC).
    Matrice d'accès :
    - Assuré titulaire / ayant droit concerné : AUTORISÉ (200)
    - Gestionnaire de l'organisme de l'assuré : AUTORISÉ (200)
    - Médecin traitant de l'assuré : AUTORISÉ (200)
    - Gestionnaire d'un autre organisme : REFUSÉ (404)
    - Autre assuré : REFUSÉ (404)
    - Administrateur IT (Secret médical) : REFUSÉ (403)
    """
    if request.user.role == User.Role.ADMIN:
        raise PermissionDenied("L'administrateur technique n'a pas accès aux devis médicaux confidentiels.")

    from ..models import PriseEnCharge

    prise = get_object_or_404(
        PriseEnCharge.objects.select_related("patient", "patient__user", "patient__assure_principal", "patient__organisme"),
        pk=pk,
    )

    patient = prise.patient
    est_proprietaire = (
        request.user.role == User.Role.ASSURE
        and (patient.user_id == request.user.pk or (patient.assure_principal and patient.assure_principal.user_id == request.user.pk))
    )
    est_gestionnaire_organisme = (
        request.user.role == User.Role.GESTIONNAIRE
        and request.user.organisme_id == patient.organisme_id
    )
    est_medecin = request.user.role == User.Role.MEDECIN

    if not (est_proprietaire or est_gestionnaire_organisme or est_medecin):
        raise Http404("Document introuvable ou accès non autorisé.")

    if not prise.devis_fichier:
        raise Http404("Aucun devis n'est attaché à cette prise en charge.")

    nom_fichier = os.path.basename(prise.devis_fichier.name)
    type_mime, _ = mimetypes.guess_type(nom_fichier)
    type_mime = type_mime or "application/octet-stream"

    if getattr(settings, "USE_X_ACCEL_REDIRECT", False):
        reponse = HttpResponse(content_type=type_mime)
        reponse["X-Accel-Redirect"] = f"/protected_media/{prise.devis_fichier.name}"
        return _finaliser_reponse_fichier(reponse, nom_fichier)

    try:
        fichier_disque = prise.devis_fichier.open("rb")
        reponse = FileResponse(fichier_disque, content_type=type_mime)
        return _finaliser_reponse_fichier(reponse, nom_fichier)
    except (FileNotFoundError, OSError):
        pass

    fichier_db = FichierMedia.objects.filter(chemin__icontains=nom_fichier).first()
    if fichier_db and fichier_db.contenu:
        reponse = HttpResponse(fichier_db.contenu, content_type=fichier_db.type_mime or type_mime)
        return _finaliser_reponse_fichier(reponse, nom_fichier)

    raise Http404("Le fichier physique est introuvable sur le stockage.")
