"""
Service d'émission centralisé des événements métier, notifications et emails réactifs.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from ..models import Notification, PreferenceNotification, User

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
    Crée une notification en base et tente un envoi d'email HTML sécurisé.
    En cas d'échec d'envoi d'email, la notification et l'action métier RESTENT VALIDES.
    """
    notification = Notification.objects.create(
        destinataire=destinataire,
        titre=titre,
        message=message,
        type_evenement=type_evenement,
        url_action=url_action,
    )

    if envoyer_email and destinataire.email and _doit_envoyer_email(destinataire, type_evenement):
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
                html_content = render_to_string(template_email, ctx)
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
            logger.warning("Échec d'envoi d'email pour la notification %s: %s", notification.pk, exc)
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

    # Notification Médecin (seulement si un compte utilisateur est rattaché)
    if medecin_user is None:
        logger.info(
            "Pas de notification médecin pour le RDV %s : le médecin %s n'a pas de compte utilisateur.",
            rendez_vous.pk, rendez_vous.medecin,
        )
    else:
        emettre_notification(
            destinataire=medecin_user,
            titre="Nouvelle demande de rendez-vous",
            message=f"Demande de rendez-vous de {patient} pour le {date_str}.",
            type_evenement=Notification.TypeEvenement.RDV_DEMANDE,
            url_action=reverse("agenda_medecin"),
            template_email="emails/rdv_demande_medecin.html",
            contexte_email={"rendez_vous": rendez_vous},
        )

    # Accusé de réception Assuré (si compte rattaché)
    if patient.user:
        emettre_notification(
            destinataire=patient.user,
            titre="Demande de rendez-vous enregistrée",
            message=f"Votre demande de rendez-vous avec le Dr {rendez_vous.medecin} pour le {date_str} a bien été enregistrée et est en attente de confirmation.",
            type_evenement=Notification.TypeEvenement.RDV_DEMANDE,
            url_action=reverse("mes_rendez_vous_assure"),
            template_email="emails/rdv_demande_assure.html",
            contexte_email={"rendez_vous": rendez_vous},
        )


def notifier_confirmation_rdv(rendez_vous):
    """Déclenché quand le médecin confirme un RDV."""
    patient = rendez_vous.patient
    if not patient.user:
        return

    date_str = rendez_vous.date_heure.strftime("%d/%m/%Y à %H:%M")
    emettre_notification(
        destinataire=patient.user,
        titre="Rendez-vous confirmé",
        message=f"Votre rendez-vous avec le Dr {rendez_vous.medecin} pour le {date_str} est confirmé.",
        type_evenement=Notification.TypeEvenement.RDV_CONFIRME,
        url_action=reverse("mes_rendez_vous_assure"),
        template_email="emails/rdv_confirme.html",
        contexte_email={"rendez_vous": rendez_vous},
    )


def notifier_refus_rdv(rendez_vous):
    """Déclenché quand le médecin refuse un RDV."""
    patient = rendez_vous.patient
    if not patient.user:
        return

    date_str = rendez_vous.date_heure.strftime("%d/%m/%Y")
    emettre_notification(
        destinataire=patient.user,
        titre="Rendez-vous non disponible",
        message=f"Votre demande de rendez-vous avec le Dr {rendez_vous.medecin} pour le {date_str} n'a pas pu être retenue.",
        type_evenement=Notification.TypeEvenement.RDV_REFUSE,
        url_action=reverse("mes_rendez_vous_assure"),
        template_email="emails/rdv_refuse.html",
        contexte_email={"rendez_vous": rendez_vous},
    )


def notifier_demande_prise_en_charge(prise_en_charge):
    """Déclenché lorsqu'un assuré demande une prise en charge."""
    admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
    patient = prise_en_charge.patient
    url = reverse("liste_prises_en_charge")

    for admin in admins:
        emettre_notification(
            destinataire=admin,
            titre="Nouvelle demande de prise en charge",
            message=f"Nouvelle demande de prise en charge soumise par {patient} (Motif : {prise_en_charge.motif}).",
            type_evenement=Notification.TypeEvenement.PEC_DEMANDE,
            url_action=url,
            template_email="emails/pec_demande_admin.html",
            contexte_email={"prise_en_charge": prise_en_charge},
        )


def notifier_validation_prise_en_charge(prise_en_charge):
    """Déclenché quand un admin valide une prise en charge."""
    patient = prise_en_charge.patient
    if not patient.user:
        return

    emettre_notification(
        destinataire=patient.user,
        titre="Prise en charge accordée",
        message=f"Votre demande de prise en charge pour '{prise_en_charge.motif}' a été validée.",
        type_evenement=Notification.TypeEvenement.PEC_VALIDEE,
        url_action=reverse("mes_prises_en_charge_assure"),
        template_email="emails/pec_validee.html",
        contexte_email={"prise_en_charge": prise_en_charge},
    )


def notifier_refus_prise_en_charge(prise_en_charge):
    """Déclenché quand un admin refuse une prise en charge."""
    patient = prise_en_charge.patient
    if not patient.user:
        return

    emettre_notification(
        destinataire=patient.user,
        titre="Prise en charge non accordée",
        message=f"Votre demande de prise en charge pour '{prise_en_charge.motif}' n'a pas été accordée.",
        type_evenement=Notification.TypeEvenement.PEC_REFUSEE,
        url_action=reverse("mes_prises_en_charge_assure"),
        template_email="emails/pec_refusee.html",
        contexte_email={"prise_en_charge": prise_en_charge},
    )


def notifier_ordonnance_creee(ordonnance):
    """Déclenché lorsqu'un médecin crée une ordonnance pour une consultation."""
    patient = ordonnance.consultation.patient
    if not patient.user:
        return

    url = reverse("voir_ordonnance_assure", args=[ordonnance.pk])
    emettre_notification(
        destinataire=patient.user,
        titre="Nouvelle ordonnance disponible",
        message=f"Une nouvelle ordonnance médicale rédigée par le Dr {ordonnance.consultation.medecin} est disponible dans votre espace.",
        type_evenement=Notification.TypeEvenement.ORDONNANCE_CREEE,
        url_action=url,
        template_email="emails/ordonnance_creee.html",
        contexte_email={"ordonnance": ordonnance},
    )


def notifier_delivrance_effectuee(delivrance):
    """Déclenché lorsqu'un pharmacien valide la délivrance d'une ordonnance."""
    patient = delivrance.ordonnance.consultation.patient
    if not patient.user:
        return

    emettre_notification(
        destinataire=patient.user,
        titre="Ordonnance délivrée",
        message=f"Votre ordonnance a été délivrée à la pharmacie {delivrance.pharmacien.prestataire or delivrance.pharmacien}.",
        type_evenement=Notification.TypeEvenement.DELIVRANCE_EFFECTUEE,
        url_action=reverse("mon_historique_assure"),
        template_email="emails/delivrance_effectuee.html",
        contexte_email={"delivrance": delivrance},
    )
