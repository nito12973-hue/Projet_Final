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
from django.utils.safestring import mark_safe

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

    site_url = getattr(settings, "SITE_URL", "https://projet-final-bice.vercel.app").rstrip("/")
    return f"{site_url}{chemin}"

def construire_bilan_onboarding(statut, utilisateur, action="creation"):
    """
    Construit un bilan clair et direct pour l'envoi automatique (WhatsApp / Email) :
    1. Si WhatsApp envoyé : confirmation immédiate avec le numéro.
    2. Si Email envoyé : confirmation immédiate avec l'adresse email et mention de vérifier les spams.
    3. Si échec : notification claire.
    """
    email = getattr(utilisateur, "email", "") or ""
    telephone = getattr(utilisateur, "phone_number", "") or ""
    email_envoye = statut.get("email_envoye", False)
    ws = statut.get("whatsapp_statut", "NON_CONFIGURE")
    whatsapp_envoye = statut.get("whatsapp_envoye", False)

    prefixe_creation = "Compte créé avec succès. " if action == "creation" else ""

    # CAS 1 : WhatsApp envoyé avec succès
    if whatsapp_envoye:
        texte_dest = f" au {telephone}" if telephone else ""
        texte_flash = mark_safe(f"{prefixe_creation}Le lien d'activation a été envoyé automatiquement par WhatsApp{texte_dest}.")
        titre = "Activation envoyée par WhatsApp"
        note = "Le lien d'activation a été transmis sur le numéro WhatsApp de l'utilisateur."
        niveau = "success"
        canal = "WhatsApp"

    # CAS 2 : Numéro WhatsApp absent ou incorrect -> Bascule Email automatique
    elif ws in ("SANS_TELEPHONE", "NUMERO_INVALIDE") and email_envoye:
        texte_dest = f" à {email}" if email else ""
        texte_flash = mark_safe(
            f"{prefixe_creation}Numéro de téléphone non renseigné ou incorrect. Le lien d'activation a été envoyé automatiquement par email{texte_dest} (pensez à vérifier la boîte principale et le dossier Spam / Courrier indésirable)."
        )
        titre = "Activation envoyée par Email"
        note = "Numéro WhatsApp incorrect. Le lien a été envoyé par email."
        niveau = "success"
        canal = "Email"

    # CAS 3 : Bascule Email automatique (100% sans bouton)
    elif email_envoye:
        texte_dest = f" à {email}" if email else ""
        texte_flash = mark_safe(
            f"{prefixe_creation}Le lien d'activation a été envoyé automatiquement par email{texte_dest} (pensez à vérifier la boîte principale et le dossier Spam / Courrier indésirable)."
        )
        titre = "Activation envoyée par Email"
        note = "Le lien d'activation a été transmis par email à l'adresse de l'utilisateur."
        niveau = "success"
        canal = "Email"

    # CAS 4 : Aucun canal n'a pu délivrer le message
    else:
        texte_flash = mark_safe(
            f"{prefixe_creation}Échec de l'envoi automatique : aucun message n'a pu être délivré par WhatsApp ni par Email. "
            "Veuillez vérifier les coordonnées de l'utilisateur."
        )
        titre = "Échec de l'envoi automatique"
        note = "Veuillez vérifier les coordonnées de l'utilisateur."
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
    if not telephone:
        if hasattr(utilisateur, "medecin") and getattr(utilisateur.medecin, "telephone", ""):
            telephone = utilisateur.medecin.telephone
        elif hasattr(utilisateur, "patient") and getattr(utilisateur.patient, "telephone", ""):
            telephone = utilisateur.patient.telephone
        elif hasattr(utilisateur, "pharmacien") and getattr(utilisateur.pharmacien, "telephone", ""):
            telephone = utilisateur.pharmacien.telephone

    # 1. Tentative WhatsApp en premier (Format SMS simple)
    whatsapp_texte = (
        f"SantéSN : Bonjour {prenom}, activez votre compte et définissez votre mot de passe via ce lien sécurisé (valable 24h) :\n"
        f"{lien_activation}"
    )
    template_nom = getattr(settings, "WHATSAPP_TEMPLATE_NAME", None)
    template_params = [prenom, lien_activation] if template_nom else None
    whatsapp_res = envoyer_message_whatsapp(
        telephone, whatsapp_texte, template_nom=template_nom, template_params=template_params
    )
    if not whatsapp_res["succes"] and template_nom:
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

                from_addr = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None) or "noreply@santesn.sn"
                from_header = f"SantéSN <{from_addr}>" if ("<" not in from_addr and "@" in from_addr) else from_addr

                msg = EmailMultiAlternatives(
                    subject=sujet,
                    body=corps_texte,
                    from_email=from_header,
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

    import urllib.parse
    numero_nettoye = "".join(filter(str.isdigit, str(telephone)))
    if numero_nettoye.startswith("00"):
        numero_nettoye = numero_nettoye[2:]
    elif not numero_nettoye.startswith("221") and len(numero_nettoye) == 9:
        numero_nettoye = f"221{numero_nettoye}"

    whatsapp_direct_url = ""
    if len(numero_nettoye) >= 8:
        whatsapp_direct_url = f"https://api.whatsapp.com/send?phone={numero_nettoye}&text={urllib.parse.quote(whatsapp_texte)}"

    statut = {
        "lien_activation": lien_activation,
        "whatsapp_direct_url": whatsapp_direct_url,
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
