"""
Service d'envoi WhatsApp officiel (Meta Cloud API / passerelle SMS/WhatsApp agréée).
Conçu pour une résilience absolue : ne bloque jamais la création de compte.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger("Plateform_medicale")


def envoyer_message_whatsapp(numero_telephone, texte_message, template_nom=None, template_params=None):
    """
    Envoie un message via l'API officielle WhatsApp Cloud.
    Supporte les messages directs (texte) et les modèles officiels (template).

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
    elif not numero_nettoye.startswith("221") and len(numero_nettoye) == 9:
        numero_nettoye = f"221{numero_nettoye}"

    if len(numero_nettoye) < 8:
        return {
            "succes": False,
            "statut": "NUMERO_INVALIDE",
            "message": f"Numéro de téléphone invalide : {numero_telephone}",
        }

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    if template_nom:
        components = []
        if template_params:
            parameters = [{"type": "text", "text": str(p)} for p in template_params]
            components.append({"type": "body", "parameters": parameters})
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_nettoye,
            "type": "template",
            "template": {
                "name": template_nom,
                "language": {"code": "fr"},
                "components": components,
            },
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_nettoye,
            "type": "text",
            "text": {"preview_url": False, "body": texte_message},
        }

    try:
        donnees = json.dumps(payload).encode("utf-8")
        requete = urllib.request.Request(
            url,
            data=donnees,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(requete, timeout=5) as reponse:
            corps = json.loads(reponse.read().decode("utf-8"))
            msg_id = corps.get("messages", [{}])[0].get("id", "")
            logger.info("Message WhatsApp envoyé avec succès au %s (ID: %s)", numero_nettoye, msg_id)
            return {
                "succes": True,
                "statut": "ENVOYE",
                "message": "Envoyé avec succès via WhatsApp Cloud API",
            }
    except urllib.error.HTTPError as err:
        erreur_msg = f"Erreur API WhatsApp ({err.code})"
        try:
            details = json.loads(err.read().decode("utf-8"))
            detail_txt = details.get("error", {}).get("message", "")
            if detail_txt:
                erreur_msg += f" : {detail_txt}"
        except Exception:
            pass
        logger.warning("Échec d'envoi WhatsApp au %s : %s", numero_nettoye, erreur_msg)
        return {
            "succes": False,
            "statut": "ECHEC",
            "message": erreur_msg,
        }
    except Exception as exc:
        logger.warning("Échec de connexion API WhatsApp au %s : %s", numero_nettoye, exc)
        return {
            "succes": False,
            "statut": "ECHEC",
            "message": f"Échec de connexion API WhatsApp : {exc}",
        }
