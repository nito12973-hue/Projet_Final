"""
Service d'onboarding sécurisé et d'activation de compte SantéSN.
Remplace la transmission de mots de passe en clair par un jeton d'activation
unique à validité limitée (24 heures).
"""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .whatsapp import envoyer_message_whatsapp

logger = logging.getLogger("Plateform_medicale")


def generer_lien_activation(utilisateur, request=None):
    """
    Génère une URL d'activation sécurisée et temporaire (24h) pour l'utilisateur.
    N'inclut AUCUN mot de passe.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(utilisateur.pk))
    token = default_token_generator.make_token(utilisateur)
    chemin = reverse("activer_compte", kwargs={"uidb64": uidb64, "token": token})

    if request:
        try:
            return request.build_absolute_uri(chemin)
        except Exception:
            pass

    site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
    return f"{site_url}{chemin}"

def construire_bilan_onboarding(statut, utilisateur, action="creation"):
    """
    Construit un bilan clair et concis pour la stratégie Mono-Canal :
    - Canal Principal : WhatsApp
    - Canal de Secours : Email
    """
    email = utilisateur.email
    email_envoye = statut.get("email_envoye", False)
    ws = statut.get("whatsapp_statut", "NON_CONFIGURE")
    whatsapp_envoye = statut.get("whatsapp_envoye", False)

    prefixe_creation = "Compte créé avec succès." if action == "creation" else ""

    # CAS 1 : WhatsApp configuré + numéro valide -> WhatsApp uniquement
    if whatsapp_envoye:
        if action == "creation":
            texte_flash = "Compte créé avec succès. Le lien d'activation a été envoyé par WhatsApp."
        else:
            texte_flash = "Le lien d'activation a été envoyé par WhatsApp."
        titre = "Activation envoyée par WhatsApp"
        note = "Le lien d'activation a été transmis sur le numéro WhatsApp de l'utilisateur."
        niveau = "success"
        canal = "WhatsApp"

    # CAS 2 : WhatsApp non configuré -> Email de secours
    elif ws == "NON_CONFIGURE" and email_envoye:
        if action == "creation":
            texte_flash = "Compte créé avec succès. WhatsApp n'est pas configuré. Le lien d'activation a été envoyé par email."
        else:
            texte_flash = "WhatsApp n'est pas configuré. Le lien d'activation a été envoyé par email."
        titre = "Activation envoyée par Email"
        note = "WhatsApp n'est pas configuré sur cette plateforme. L'activation a été transmise par email."
        niveau = "success"
        canal = "Email"

    # CAS 3 : Numéro WhatsApp invalide ou absent -> Email de secours
    elif ws in ("SANS_TELEPHONE", "NUMERO_INVALIDE") and email_envoye:
        if action == "creation":
            texte_flash = "Compte créé avec succès. Le numéro WhatsApp n'est pas disponible. Le lien d'activation a été envoyé par email."
        else:
            texte_flash = "Le numéro WhatsApp n'est pas disponible. Le lien d'activation a été envoyé par email."
        titre = "Activation envoyée par Email"
        note = "Le numéro WhatsApp n'est pas disponible. Le lien d'activation a été envoyé par email."
        niveau = "success"
        canal = "Email"

    # CAS 4 : WhatsApp configuré mais API en panne -> Email de secours
    elif ws == "ECHEC" and email_envoye:
        if action == "creation":
            texte_flash = "Compte créé avec succès. Échec de l'envoi WhatsApp. Le lien d'activation a été envoyé par email en secours."
        else:
            texte_flash = "Échec de l'envoi WhatsApp. Le lien d'activation a été envoyé par email en secours."
        titre = "Activation envoyée par Email (Secours)"
        note = "Une erreur est survenue lors de l'envoi WhatsApp. Le lien a été envoyé par email en secours."
        niveau = "warning"
        canal = "Email (Secours)"

    # CAS 5 : Aucun canal disponible (WhatsApp échoué/absent ET Email échoué)
    else:
        if action == "creation":
            texte_flash = (
                "Compte créé, mais aucun canal d'activation n'est disponible. "
                "Veuillez configurer un moyen de contact ou renvoyer l'activation ultérieurement."
            )
        else:
            texte_flash = (
                "Échec de l'envoi : aucun canal d'activation n'est disponible. "
                "Veuillez configurer un moyen de contact ou réessayer ultérieurement."
            )
        titre = "Aucun canal d'activation disponible"
        note = "Veuillez vérifier les coordonnées de l'utilisateur ou copier directement le lien sécurisé ci-dessous."
        niveau = "error"
        canal = "Aucun"

    return {
        "titre": titre,
        "note": note,
        "niveau": niveau,
        "texte_flash": texte_flash,
        "canal": canal,
        "email_statut_label": "Envoyé" if email_envoye else ("Non envoyé (WhatsApp utilisé)" if whatsapp_envoye else "Échec"),
        "email_statut_classe": "succes" if email_envoye else ("neutre" if whatsapp_envoye else "danger"),
        "whatsapp_statut_label": (
            "Envoyé" if ws == "ENVOYE" else
            "Non configuré" if ws == "NON_CONFIGURE" else
            "Sans téléphone" if ws == "SANS_TELEPHONE" else
            "Numéro invalide" if ws == "NUMERO_INVALIDE" else
            "Échec"
        ),
        "whatsapp_statut_classe": (
            "succes" if ws == "ENVOYE" else
            "neutre" if ws in ("NON_CONFIGURE", "SANS_TELEPHONE") else
            "danger"
        ),
    }


def envoyer_activation_utilisateur(utilisateur, request=None):
    """
    Génère le lien d'activation et applique la stratégie mono-canal :
    1. WhatsApp en canal principal : si disponible et envoyé, aucun email n'est envoyé.
    2. Email en canal de secours : activé si WhatsApp n'est pas configuré,
       si le numéro est absent/invalide ou en cas d'échec de l'API WhatsApp.
    """
    lien_activation = generer_lien_activation(utilisateur, request=request)
    prenom = utilisateur.first_name or "Bonjour"
    email = utilisateur.email
    telephone = getattr(utilisateur, "phone_number", "") or ""

    # 1. Tentative WhatsApp en premier (Canal Principal)
    whatsapp_texte = (
        f"Bonjour {prenom},\n\n"
        f"Votre compte SantéSN a été créé.\n\n"
        f"Activez votre compte et définissez votre mot de passe :\n"
        f"{lien_activation}\n\n"
        f"Ce lien est valable 24 heures.\n\n"
        f"SantéSN"
    )
    whatsapp_res = envoyer_message_whatsapp(telephone, whatsapp_texte)

    email_envoye = False
    email_erreur = None

    if whatsapp_res["succes"]:
        # WhatsApp a fonctionné : NE JAMAIS envoyer par Email
        logger.info("Activation envoyée par WhatsApp uniquement pour %s (%s)", email, telephone)
    else:
        # 2. WhatsApp indisponible ou échec : Bascule sur l'Email de secours (Fallback)
        logger.info("WhatsApp indisponible (%s), bascule sur Email de secours pour %s", whatsapp_res["statut"], email)
        if email:
            try:
                sujet = "Activation de votre compte SantéSN"
                ctx = {
                    "user": utilisateur,
                    "prenom": prenom,
                    "email": email,
                    "lien_activation": lien_activation,
                    "duree_heures": 24,
                }
                corps_texte = (
                    f"Bonjour {prenom},\n\n"
                    f"Votre compte SantéSN a été créé.\n\n"
                    f"Pour commencer à utiliser la plateforme, veuillez activer votre compte et définir votre mot de passe :\n\n"
                    f"{lien_activation}\n\n"
                    f"Ce lien est valable 24 heures.\n\n"
                    f"Si vous n'êtes pas à l'origine de cette création de compte, veuillez contacter l'administration.\n\n"
                    f"SantéSN"
                )
                try:
                    corps_html = render_to_string("emails/activation_compte.html", ctx)
                except Exception:
                    corps_html = None

                msg = EmailMultiAlternatives(
                    subject=sujet,
                    body=corps_texte,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@santesn.sn"),
                    to=[email],
                )
                if corps_html:
                    msg.attach_alternative(corps_html, "text/html")
                msg.send(fail_silently=False)
                email_envoye = True
                logger.info("Email d'activation de secours envoyé à %s", email)
            except Exception as exc:
                email_erreur = str(exc)
                logger.warning("Échec d'envoi d'email de secours pour %s : %s", email, exc)

    statut = {
        "lien_activation": lien_activation,
        "email_envoye": email_envoye,
        "email_statut": "ENVOYE" if email_envoye else ("NON_ENVOYE" if whatsapp_res["succes"] else "ECHEC"),
        "email_erreur": email_erreur,
        "whatsapp_envoye": whatsapp_res["succes"],
        "whatsapp_statut": whatsapp_res["statut"],
        "whatsapp_message": whatsapp_res["message"],
        "whatsapp_erreur": whatsapp_res["message"] if not whatsapp_res["succes"] else None,
        "canal_utilise": "WHATSAPP" if whatsapp_res["succes"] else ("EMAIL" if email_envoye else "AUCUN"),
    }
    statut["bilan"] = construire_bilan_onboarding(statut, utilisateur)
    return statut
