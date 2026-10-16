"""
Contrôleur Webhook pour WhatsApp Cloud API (Meta) et Passerelles Partenaires.

Fournit :
1. La vérification du webhook Meta (requête GET avec hub.challenge et hub.verify_token)
2. La réception en temps réel des messages WhatsApp entrants (requête POST)
3. Le traitement conversationnel via le bot SantéSN et la réponse automatique
"""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
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

        verify_token_attendu = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "santesn_webhook_secret_2026")

        if mode == "subscribe" and token == verify_token_attendu:
            logger.info("Validation du Webhook WhatsApp Meta réussie.")
            return HttpResponse(challenge, content_type="text/plain", status=200)

        logger.warning("Échec de vérification du Webhook WhatsApp : token incorrect (%s).", token)
        return HttpResponse("Vérification échouée", status=403)

    if request.method == "POST":
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

    return HttpResponse("Méthode non autorisée", status=405)
