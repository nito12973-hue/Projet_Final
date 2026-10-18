"""
Contrôleur Webhook pour WhatsApp Cloud API (Meta) et Passerelles Partenaires.

Fournit :
1. La vérification du webhook Meta (requête GET avec hub.challenge et hub.verify_token)
2. La réception en temps réel des messages WhatsApp entrants (requête POST)
3. Le traitement conversationnel via le bot SantéSN et la réponse automatique
"""

import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt

from Plateform_medicale.services.whatsapp import envoyer_message_whatsapp
from Plateform_medicale.services.whatsapp_bot import traiter_message_entrant_whatsapp

logger = logging.getLogger("Plateform_medicale")


@csrf_exempt
def webhook_whatsapp(request):
    """
    Point d'entrée Webhook officiel WhatsApp.
    - GET : validation de l'URL par Meta (challenge).
    - POST : traitement des messages entrants des assurés et réponse automatique.
    """
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        verify_token_attendu = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")

        if (
            mode == "subscribe"
            and token
            and verify_token_attendu
            and constant_time_compare(token, verify_token_attendu)
        ):
            logger.info("Validation du Webhook WhatsApp Meta réussie.")
            return HttpResponse(challenge, content_type="text/plain", status=200)

        logger.warning("Échec de vérification du Webhook WhatsApp : token incorrect.")
        return HttpResponse("Vérification échouée", status=403)

    if request.method == "POST":
        # Contrôle cryptographique officiel Meta (X-Hub-Signature-256)
        app_secret = getattr(settings, "WHATSAPP_APP_SECRET", "")
        if app_secret:
            hub_sig = request.headers.get("X-Hub-Signature-256") or request.META.get("HTTP_X_HUB_SIGNATURE_256", "")
            if not hub_sig or not hub_sig.startswith("sha256="):
                logger.warning("Signature X-Hub-Signature-256 manquante ou malformée sur le Webhook WhatsApp.")
                return HttpResponse("Signature invalide", status=403)
            sig_attendue = hmac.new(
                app_secret.encode("utf-8"),
                request.body,
                hashlib.sha256,
            ).hexdigest()
            sig_fournie = hub_sig.split("sha256=")[-1]
            if not constant_time_compare(sig_fournie, sig_attendue):
                logger.warning("Signature cryptographique Meta WhatsApp non concordante.")
                return HttpResponse("Signature invalide", status=403)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception as exc:
            logger.warning("Corps de requête Webhook WhatsApp invalide : %s", exc)
            return JsonResponse({"erreur": "JSON invalide"}, status=400)

        expediteur = None
        texte_message = ""

        # 1. Format officiel Meta Cloud API
        try:
            entry = payload.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})
            messages = value.get("messages", [])

            if messages:
                premier_message = messages[0]
                expediteur = premier_message.get("from")
                if premier_message.get("type") == "text":
                    texte_message = premier_message.get("text", {}).get("body", "")
                elif premier_message.get("type") == "button":
                    texte_message = premier_message.get("button", {}).get("text", "")
                elif premier_message.get("type") == "location":
                    loc = premier_message.get("location", {})
                    lat = loc.get("latitude")
                    lng = loc.get("longitude")
                    texte_message = f"LOCATION {lat} {lng}"
                elif premier_message.get("type") == "interactive":
                    interactive = premier_message.get("interactive", {})
                    texte_message = (
                        interactive.get("button_reply", {}).get("title")
                        or interactive.get("list_reply", {}).get("title")
                        or ""
                    )
        except Exception:
            pass

        # 2. Format direct / simplifié pour tests et passerelles SMS/WhatsApp alternatives
        if not expediteur:
            expediteur = payload.get("from") or payload.get("telephone") or payload.get("expediteur")
            texte_message = payload.get("text") or payload.get("message") or payload.get("body") or ""

        if not expediteur:
            # Acquittement technique Meta même si l'événement n'est pas un message (ex: statuts delivery/read)
            return JsonResponse({"status": "ignored", "motif": "Pas de message entrant exploitable"})

        logger.info("Message WhatsApp reçu du %s : '%s'", expediteur, texte_message)

        try:
            # Traitement conversationnel
            reponse_bot = traiter_message_entrant_whatsapp(expediteur, texte_message)

            # Envoi de la réponse sur WhatsApp
            statut_envoi = envoyer_message_whatsapp(expediteur, reponse_bot)
            logger.info("Réponse WhatsApp transmise au %s : statut %s", expediteur, statut_envoi.get("statut"))

            return JsonResponse({
                "status": "ok",
                "reponse": reponse_bot,
                "statut_envoi": statut_envoi,
            })
        except Exception as exc:
            logger.error("Erreur inattendue dans le traitement du message WhatsApp : %s", exc, exc_info=True)
            return JsonResponse({
                "status": "error",
                "detail": "Erreur interne traitée gracieusement",
            }, status=200)

    return HttpResponse("Méthode non autorisée", status=405)
