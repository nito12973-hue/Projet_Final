"""
Service d'envoi WhatsApp officiel (Meta Cloud API / passerelle SMS/WhatsApp agréée).
Conçu pour une résilience absolue : ne bloque jamais la création de compte.

Templates approuvés sur le WABA production (1060664073517769) :
  - compte_santesn_notif : BODY {{1}}=nom + BUTTON URL {{1}}=chemin
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger("Plateform_medicale")

# Modèle principal approuvé sur le WABA de production
TEMPLATE_DEFAUT = "compte_santesn_notif"


def envoyer_message_whatsapp(
    numero_telephone,
    texte_message,
    template_nom=None,
    template_params=None,
    template_button_params=None,
):
    """
    Envoie un message via l'API officielle WhatsApp Cloud.
    Supporte les messages directs (texte), les modèles officiels (template)
    et les modèles avec bouton URL (template_button_params).

    Retourne un dictionnaire de résultat :
    {
        "succes": bool,
        "statut": "ENVOYE" | "NON_CONFIGURE" | "NUMERO_INVALIDE" | "ECHEC",
        "message": str,
    }
    """
    if not numero_telephone or not str(numero_telephone).strip():
        return {
            "succes": False,
            "statut": "SANS_TELEPHONE",
            "message": "Numéro de téléphone absent",
        }

    whatsapp_active = getattr(settings, "WHATSAPP_ENABLED", False)
    token = getattr(settings, "WHATSAPP_API_TOKEN", None)
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)

    if not whatsapp_active or not token or not phone_number_id:
        return {
            "succes": False,
            "statut": "NON_CONFIGURE",
            "message": "WhatsApp n'est pas configuré sur ce serveur",
        }

    # Normalisation du numéro de téléphone (international)
    numero_nettoye = "".join(filter(str.isdigit, str(numero_telephone)))
    if numero_nettoye.startswith("00"):
        numero_nettoye = numero_nettoye[2:]
    elif numero_nettoye.startswith("0") and len(numero_nettoye) == 10:
        numero_nettoye = numero_nettoye[1:]

    if not numero_nettoye.startswith("221") and len(numero_nettoye) == 9:
        numero_nettoye = f"221{numero_nettoye}"

    if len(numero_nettoye) < 8:
        return {
            "succes": False,
            "statut": "NUMERO_INVALIDE",
            "message": f"Numéro de téléphone invalide : {numero_telephone}",
        }

    # Meta interdit à un compte WhatsApp Business d'envoyer des messages vers son propre numéro
    sender_phone = str(getattr(settings, "WHATSAPP_SENDER_PHONE", "221789576145")).strip()
    sender_nettoye = "".join(filter(str.isdigit, sender_phone))
    numeros_expediteur = {sender_nettoye}
    if sender_nettoye.startswith("221"):
        numeros_expediteur.add(sender_nettoye[3:])
    else:
        numeros_expediteur.add(f"221{sender_nettoye}")

    if numero_nettoye in numeros_expediteur:
        logger.warning("Tentative d'envoi WhatsApp vers le numéro expéditeur officiel (%s). Non autorisé par Meta.", numero_nettoye)
        return {
            "succes": False,
            "statut": "ECHEC",
            "message": f"Le numéro destinataire est identique au numéro expéditeur officiel ({sender_phone}). Meta interdit l'envoi vers soi-même.",
        }

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"

    def _preparer_payload(nom_tpl=None, params_tpl=None, code_langue=None, btn_params=None):
        if nom_tpl:
            components = []
            if params_tpl:
                parameters = [{"type": "text", "text": str(p)} for p in params_tpl]
                components.append({"type": "body", "parameters": parameters})
            # Support du bouton URL dynamique (composant BUTTON)
            if btn_params:
                for idx, val in enumerate(btn_params):
                    components.append({
                        "type": "button",
                        "sub_type": "url",
                        "index": str(idx),
                        "parameters": [{"type": "text", "text": str(val)}],
                    })
            langue = code_langue or "fr"
            return {
                "messaging_product": "whatsapp",
                "to": numero_nettoye,
                "type": "template",
                "template": {
                    "name": nom_tpl,
                    "language": {"code": langue},
                    "components": components,
                },
            }
        return {
            "messaging_product": "whatsapp",
            "to": numero_nettoye,
            "type": "text",
            "text": {"preview_url": False, "body": texte_message},
        }

    def _executer_envoi(payload_dict):
        donnees = json.dumps(payload_dict).encode("utf-8")
        requete = urllib.request.Request(
            url,
            data=donnees,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(requete, timeout=12) as reponse:
            corps = json.loads(reponse.read().decode("utf-8"))
            msg_id = corps.get("messages", [{}])[0].get("id", "")
            return True, msg_id, "Envoyé avec succès via WhatsApp Cloud API"

    # Tentative 1 : envoi selon la demande initiale (template si spécifié, sinon texte libre)
    payload_initial = _preparer_payload(template_nom, template_params, btn_params=template_button_params)
    try:
        succes, msg_id, msg_retour = _executer_envoi(payload_initial)
        logger.info("Message WhatsApp envoyé avec succès au %s (ID: %s)", numero_nettoye, msg_id)
        return {
            "succes": True,
            "statut": "ENVOYE",
            "message": msg_retour,
            "message_id": msg_id,
        }
    except urllib.error.HTTPError as err:
        erreur_code = err.code
        erreur_msg = f"Erreur API WhatsApp ({erreur_code})"
        code_meta = None
        try:
            details = json.loads(err.read().decode("utf-8"))
            code_meta = details.get("error", {}).get("code")
            detail_txt = details.get("error", {}).get("message", "")
            if detail_txt:
                erreur_msg += f" : {detail_txt}"
        except Exception:
            pass

        logger.warning("Échec tentative initiale WhatsApp au %s (code %s): %s", numero_nettoye, code_meta, erreur_msg)

        # Si le message texte libre a échoué à cause de la restriction de fenêtre 24h ou nouveau contact,
        # on effectue un fallback automatique vers le modèle officiel approuvé pour garantir la délivrabilité
        if not template_nom and code_meta in (131047, 131026, 131030, 100, 132000, 132001, 131051, 131052):
            try:
                logger.info("Bascule automatique vers le modèle officiel '%s' pour le numéro %s", TEMPLATE_DEFAUT, numero_nettoye)
                payload_fb = _preparer_payload(
                    TEMPLATE_DEFAUT,
                    ["Assuré SantéSN"],  # {{1}} body = nom
                    "fr",
                    ["activation"],      # {{1}} button URL = chemin
                )
                succes_fb, msg_id_fb, _ = _executer_envoi(payload_fb)
                return {
                    "succes": True,
                    "statut": "ENVOYE",
                    "message": f"Délivré avec succès via le modèle officiel ({TEMPLATE_DEFAUT})",
                    "message_id": msg_id_fb,
                }
            except Exception as fb_exc:
                logger.warning("Échec du modèle fallback '%s' pour %s : %s", TEMPLATE_DEFAUT, numero_nettoye, fb_exc)

        return {
            "succes": False,
            "statut": "ECHEC",
            "message": erreur_msg,
        }
    except Exception as exc:
        logger.warning("Échec exceptionnel d'envoi WhatsApp au %s : %s", numero_nettoye, exc)
        return {
            "succes": False,
            "statut": "ECHEC",
            "message": f"Échec de connexion API WhatsApp : {exc}",
        }
