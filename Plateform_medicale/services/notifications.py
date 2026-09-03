# -*- coding: utf-8 -*-
"""
Service d'émission centralisé des événements métier, notifications et emails réactifs.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from ..models import Notification, PreferenceNotification, User
from .whatsapp import envoyer_message_whatsapp

logger = logging.getLogger(__name__)


def _doit_envoyer_email(user, type_evenement):
    """Vérifie les préférences d'email de l'utilisateur."""
    pref, _ = PreferenceNotification.objects.get_or_create(user=user)
    if type_evenement in (
        Notification.TypeEvenement.RDV_DEMANDE,
        Notification.TypeEvenement.RDV_CONFIRME,
        Notification.TypeEvenement.RDV_REFUSE,
        Notification.TypeEvenement.RDV_ANNULE,
    ):
        return pref.email_rdv
    elif type_evenement in (
        Notification.TypeEvenement.PEC_DEMANDE,
        Notification.TypeEvenement.PEC_VALIDEE,
        Notification.TypeEvenement.PEC_REFUSEE,
    ):
        return pref.email_prise_en_charge
    elif type_evenement == Notification.TypeEvenement.ORDONNANCE_CREEE:
        return pref.email_ordonnance
    elif type_evenement == Notification.TypeEvenement.DELIVRANCE_EFFECTUEE:
        return pref.email_delivrance
    return True


def _obtenir_utilisateur_assure(patient):
    """Retourne le compte User associé à l'assuré (directement ou via l'assuré principal)."""
    if patient is None:
        return None
    if getattr(patient, "user", None):
        return patient.user
    if getattr(patient, "assure_principal", None) and getattr(patient.assure_principal, "user", None):
        return _obtenir_utilisateur_assure(patient)
    return None


def emettre_notification(
    destinataire,
    titre,
    message,
    type_evenement=Notification.TypeEvenement.SYSTEME,
    url_action="",
    envoyer_email=True,
    sujet_email=None,
    template_email=None,
    contexte_email=None,
):
    """
    Crée une notification in-app et applique la stratégie multicanale :
    1. WhatsApp en canal principal (si activé et numéro de téléphone renseigné).
    2. Email HTML en canal de secours (si WhatsApp désactivé, numéro absent ou échec d'envoi API).
    """
    notification = Notification.objects.create(
        destinataire=destinataire,
        titre=titre,
        message=message,
        type_evenement=type_evenement,
        url_action=url_action,
    )
    notification.whatsapp_envoye = False

    if not _doit_envoyer_email(destinataire, type_evenement):
        return notification

    telephone = getattr(destinataire, "phone_number", "") or ""
    whatsapp_succes = False

    # 1. Tentative WhatsApp prioritaire
    if telephone and getattr(settings, "WHATSAPP_ENABLED", False):
        try:
            texte_wa = f"[{titre}]\n\n{message}"
            if url_action:
                site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
                lien_complet = url_action if url_action.startswith("http") else f"{site_url.rstrip('/')}{url_action}"
                texte_wa += f"\n\nConsulter : {lien_complet}"

            res_wa = envoyer_message_whatsapp(telephone, texte_wa)
            if res_wa.get("succes"):
                whatsapp_succes = True
                notification.whatsapp_envoye = True
                # WhatsApp reussi in-memory
                logger.info("Notification %s envoyée via WhatsApp à %s", notification.pk, destinataire.email)
        except Exception as exc:
            logger.warning("Échec tentative WhatsApp pour la notification %s : %s", notification.pk, exc)

    # 2. Secours Email (si WhatsApp non envoyé)
    if not whatsapp_succes and envoyer_email and destinataire.email:
        try:
            sujet = sujet_email or f"[SantéSN] {titre}"
            ctx = contexte_email or {}
            ctx.update({
                "user": destinataire,
                "titre": titre,
                "message": message,
                "url_action": url_action,
            })

            site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
            texte_brut = f"{titre}\n\n{message}\n\nAccéder à SantéSN : {url_action or site_url}"

            if template_email:
                try:
                    html_content = render_to_string(template_email, ctx)
                except Exception:
                    html_content = render_to_string("emails/notification_standard.html", ctx)
            else:
                html_content = render_to_string("emails/notification_standard.html", ctx)

            email_msg = EmailMultiAlternatives(
                subject=sujet,
                body=texte_brut,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@santesn.sn"),
                to=[destinataire.email],
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)

            notification.email_envoye = True
            notification.save(update_fields=["email_envoye"])
        except Exception as exc:
            logger.warning("Échec d'envoi d'email de secours pour la notification %s: %s", notification.pk, exc)
            notification.email_erreur = str(exc)
            notification.save(update_fields=["email_erreur"])

    return notification


# ---------------------------------------------------------------------------
# Événements métier spécifiques
# ---------------------------------------------------------------------------

def notifier_demande_rdv(rendez_vous):
    """Déclenché lorsqu'un assuré réserve un rendez-vous."""
    medecin_user = rendez_vous.medecin.user
    patient = rendez_vous.patient
    date_str = rendez_vous.date_heure.strftime("%d/%m/%Y à %H:%M")

    if medecin_user:
        emettre_notification(
            destinataire=medecin_user,
            titre="Nouvelle demande de rendez-vous",
            message=f"Le patient {patient} a demandé un rendez-vous le {date_str}.",
            type_evenement=Notification.TypeEvenement.RDV_DEMANDE,
            url_action=reverse("agenda_medecin"),
            template_email="emails/rdv_demande_admin.html",
            contexte_email={"rendez_vous": rendez_vous, "patient": patient, "date_str": date_str},
        )
    else:
        logger.info("Pas de notification médecin pour le RDV %s : le médecin %s n'a pas de compte utilisateur.", rendez_vous.pk, rendez_vous.medecin)

    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        assure_user = _obtenir_utilisateur_assure(patient)
        emettre_notification(
            destinataire=assure_user,
            titre="Demande de rendez-vous enregistrée",
            message=f"Votre demande de rendez-vous avec le Dr {rendez_vous.medecin} pour le {date_str} a bien été enregistrée.",
            type_evenement=Notification.TypeEvenement.RDV_DEMANDE,
            url_action=reverse("mes_rendez_vous_assure"),
            template_email="emails/rdv_demande_assure.html",
            contexte_email={"rendez_vous": rendez_vous, "patient": patient, "date_str": date_str},
        )


def notifier_confirmation_rdv(rendez_vous):
    """Déclenché lorsqu'un médecin confirme un rendez-vous."""
    patient = rendez_vous.patient
    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        date_str = rendez_vous.date_heure.strftime("%d/%m/%Y à %H:%M")
        emettre_notification(
            destinataire=assure_user,
            titre="Rendez-vous confirmé",
            message=f"Votre rendez-vous avec le Dr {rendez_vous.medecin} du {date_str} a été confirmé.",
            type_evenement=Notification.TypeEvenement.RDV_CONFIRME,
            url_action=reverse("mes_rendez_vous_assure"),
            template_email="emails/rdv_confirme.html",
            contexte_email={"rendez_vous": rendez_vous, "patient": patient, "date_str": date_str},
        )


def notifier_refus_rdv(rendez_vous):
    """Déclenché lorsqu'un médecin refuse un rendez-vous."""
    patient = rendez_vous.patient
    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        date_str = rendez_vous.date_heure.strftime("%d/%m/%Y à %H:%M")
        emettre_notification(
            destinataire=assure_user,
            titre="Rendez-vous non disponible",
            message=f"Votre demande de rendez-vous avec le Dr {rendez_vous.medecin} pour le {date_str} n'a pas pu être retenue.",
            type_evenement=Notification.TypeEvenement.RDV_REFUSE,
            url_action=reverse("mes_rendez_vous_assure"),
            template_email="emails/rdv_refuse.html",
            contexte_email={"rendez_vous": rendez_vous, "patient": patient, "date_str": date_str},
        )


def notifier_annulation_rdv_par_medecin(rendez_vous):
    """Déclenché lorsqu'un médecin annule un rendez-vous déjà confirmé."""
    patient = rendez_vous.patient
    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        date_str = rendez_vous.date_heure.strftime("%d/%m/%Y à %H:%M")
        emettre_notification(
            destinataire=assure_user,
            titre="Rendez-vous annulé par le médecin",
            message=f"Le Dr {rendez_vous.medecin} a dû annuler le rendez-vous prévu le {date_str} (annulé par le praticien).",
            type_evenement=Notification.TypeEvenement.RDV_ANNULE,
            url_action=reverse("mes_rendez_vous_assure"),
            template_email="emails/rdv_annule.html",
            contexte_email={"rendez_vous": rendez_vous, "patient": patient, "date_str": date_str, "annule_par": "le médecin"},
        )


def notifier_annulation_rdv_par_assure(rendez_vous):
    """Déclenché lorsqu'un assuré annule un rendez-vous."""
    medecin_user = rendez_vous.medecin.user
    date_str = rendez_vous.date_heure.strftime("%d/%m/%Y à %H:%M")

    if medecin_user:
        emettre_notification(
            destinataire=medecin_user,
            titre="Rendez-vous annulé par le patient",
            message=f"Le patient {rendez_vous.patient} a annulé son rendez-vous du {date_str} (annulé par le patient).",
            type_evenement=Notification.TypeEvenement.RDV_ANNULE,
            url_action=reverse("agenda_medecin"),
            template_email="emails/rdv_annule.html",
            contexte_email={"rendez_vous": rendez_vous, "patient": rendez_vous.patient, "date_str": date_str, "annule_par": "le patient"},
        )


def notifier_ordonnance_creee(ordonnance):
    """Déclenché lorsqu'un médecin prescrit une ordonnance."""
    patient = ordonnance.consultation.patient
    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        emettre_notification(
            destinataire=assure_user,
            titre="Nouvelle ordonnance disponible",
            message=f"Une nouvelle ordonnance a été rédigée par le Dr {ordonnance.consultation.medecin}.",
            type_evenement=Notification.TypeEvenement.ORDONNANCE_CREEE,
            url_action=reverse("voir_ordonnance_assure", args=[ordonnance.pk]),
            template_email="emails/ordonnance_creee.html",
            contexte_email={"ordonnance": ordonnance, "patient": patient},
        )


def notifier_delivrance_effectuee(delivrance):
    """Déclenché lorsqu'une pharmacie valide la délivrance d'une ordonnance."""
    ordonnance = delivrance.ordonnance
    patient = ordonnance.consultation.patient

    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        nom_ph = delivrance.pharmacien.prestataire.nom if delivrance.pharmacien.prestataire else 'partenaire'
        emettre_notification(
            destinataire=assure_user,
            titre="Médicaments délivrés",
            message=f"Vos médicaments de l'ordonnance #{ordonnance.pk} ont été délivrés par la pharmacie {nom_ph}.",
            type_evenement=Notification.TypeEvenement.DELIVRANCE_EFFECTUEE,
            url_action=reverse("voir_ordonnance_assure", args=[ordonnance.pk]),
            template_email="emails/delivrance_effectuee.html",
            contexte_email={"delivrance": delivrance, "ordonnance": ordonnance, "patient": patient},
        )


def notifier_demande_prise_en_charge(prise_en_charge):
    """Déclenché lorsqu'une demande de prise en charge est soumise."""
    admins = User.objects.filter(role=User.Role.ADMIN)
    for admin in admins:
        emettre_notification(
            destinataire=admin,
            titre="Nouvelle demande de prise en charge",
            message=f"Une demande de PEC de  pour {prise_en_charge.patient} est en attente de validation.",
            type_evenement=Notification.TypeEvenement.PEC_DEMANDE,
            url_action=reverse("liste_prises_en_charge"),
            template_email="emails/pec_demande_admin.html",
            contexte_email={"prise_en_charge": prise_en_charge, "patient": prise_en_charge.patient},
        )


def notifier_validation_prise_en_charge(prise_en_charge):
    """Déclenché lorsqu'une prise en charge est validée par l'admin."""
    patient = prise_en_charge.patient
    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        emettre_notification(
            destinataire=assure_user,
            titre="Prise en charge accordée",
            message=f"Votre prise en charge de  a été accordée par l'IPM.",
            type_evenement=Notification.TypeEvenement.PEC_VALIDEE,
            url_action=reverse("mes_prises_en_charge_assure"),
            template_email="emails/pec_validee.html",
            contexte_email={"prise_en_charge": prise_en_charge, "patient": patient},
        )


def notifier_refus_prise_en_charge(prise_en_charge):
    """Déclenché lorsqu'une prise en charge est refusée par l'admin."""
    patient = prise_en_charge.patient
    assure_user = _obtenir_utilisateur_assure(patient)
    if assure_user:
        motif = prise_en_charge.motif_refus or 'Non spécifié'
        emettre_notification(
            destinataire=assure_user,
            titre="Prise en charge refusée",
            message=f"Votre demande de prise en charge n'a pas pu être accordée. Motif : {motif}.",
            type_evenement=Notification.TypeEvenement.PEC_REFUSEE,
            url_action=reverse("mes_prises_en_charge_assure"),
            template_email="emails/pec_refusee.html",
            contexte_email={"prise_en_charge": prise_en_charge, "patient": patient},
        )
