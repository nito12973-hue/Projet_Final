# -*- coding: utf-8 -*-
"""
Commande Django pour auditer, simuler et tester les stratégies WhatsApp (Pull & Push) de SantéSN.

Usage :
    python manage.py tester_whatsapp --diagnostic
    python manage.py tester_whatsapp --simuler-pull "1" --from "221771112233"
    python manage.py tester_whatsapp --simuler-pull "2" --from "221771112233"
    python manage.py tester_whatsapp --simuler-pull "4"
    python manage.py tester_whatsapp --guide-deploiement
    python manage.py tester_whatsapp --push-test "221771234567" --texte "Test push SantéSN"
"""

import sys
from django.conf import settings
from django.core.management.base import BaseCommand

from Plateform_medicale.services.whatsapp import envoyer_message_whatsapp
from Plateform_medicale.services.whatsapp_bot import (
    formater_reponse_menu,
    traiter_message_entrant_whatsapp,
    trouver_patient_par_telephone,
)


class Command(BaseCommand):
    help = "Vérifie et teste les flux WhatsApp de SantéSN (stratégies Pull conversationnel et Push notifications)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--diagnostic",
            action="store_true",
            help="Vérifie les variables d'environnement et la configuration WhatsApp Meta.",
        )
        parser.add_argument(
            "--simuler-pull",
            type=str,
            help="Simule un message entrant envoyé par un assuré/praticien au bot WhatsApp.",
        )
        parser.add_argument(
            "--from",
            dest="expediteur",
            type=str,
            default="221771112233",
            help="Numéro de téléphone émetteur pour la simulation Pull (par défaut : 221771112233).",
        )
        parser.add_argument(
            "--push-test",
            type=str,
            help="Envoie un message Push réel vers le numéro de téléphone spécifié.",
        )
        parser.add_argument(
            "--texte",
            type=str,
            default="Bonjour, ceci est un test de notification Push de SantéSN.",
            help="Contenu texte du message Push à envoyer.",
        )
        parser.add_argument(
            "--guide-deploiement",
            action="store_true",
            help="Affiche les paramètres exacts pour configurer le Webhook dans le Dashboard Meta for Developers.",
        )

    def _ecrire(self, texte, style_func=None):
        """Écrit du texte sur stdout en protégeant contre les erreurs d'encodage cp1252 sur Windows."""
        try:
            if style_func:
                self.stdout.write(style_func(texte))
            else:
                self.stdout.write(texte)
        except UnicodeEncodeError:
            texte_ascii = texte.encode("ascii", "replace").decode("ascii")
            if style_func:
                self.stdout.write(style_func(texte_ascii))
            else:
                self.stdout.write(texte_ascii)

    def handle(self, *args, **options):
        self._ecrire("=== AUDIT & STRATEGIES WHATSAPP SANTESN ===", self.style.MIGRATE_HEADING)

        if options.get("guide_deploiement"):
            self._afficher_guide_deploiement()
            return

        if options.get("simuler_pull"):
            self._simuler_pull(options["expediteur"], options["simuler_pull"])
            return

        if options.get("push_test"):
            self._tester_push(options["push_test"], options["texte"])
            return

        # Par défaut : diagnostic complet + guide
        self._executer_diagnostic()
        self._afficher_guide_deploiement()

    def _executer_diagnostic(self):
        self._ecrire("\n[1/3] DIAGNOSTIC DE CONFIGURATION :", self.style.SUCCESS)

        active = getattr(settings, "WHATSAPP_ENABLED", False)
        token = getattr(settings, "WHATSAPP_API_TOKEN", "")
        phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
        verify_token = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "santesn_webhook_secret_2026")
        sender_phone = getattr(settings, "WHATSAPP_SENDER_PHONE", "221789576145")

        self._ecrire(f"  * WHATSAPP_ENABLED             : {'[OK] Active' if active else '[ATTENTION] Desactive (mode secours)'}")
        self._ecrire(f"  * WHATSAPP_PHONE_NUMBER_ID     : {'[OK] Renseigne (' + str(phone_id) + ')' if phone_id else '[NON CONFIGURE] Absent'}")
        self._ecrire(f"  * WHATSAPP_API_TOKEN           : {'[OK] Present (' + str(token[:10]) + '...)' if token else '[NON CONFIGURE] Absent'}")
        self._ecrire(f"  * WHATSAPP_WEBHOOK_VERIFY_TOKEN: [OK] '{verify_token}'")
        self._ecrire(f"  * WHATSAPP_SENDER_PHONE        : [OK] '{sender_phone}'")

    def _simuler_pull(self, expediteur, message_texte):
        self._ecrire(f"\n[SIMULATION PULL CONVERSATIONNEL]", self.style.SUCCESS)
        self._ecrire(f"  Emetteur : {expediteur}")
        self._ecrire(f"  Message entrant : '{message_texte}'")

        patient = trouver_patient_par_telephone(expediteur)
        if patient:
            self._ecrire(f"  Dossier Patient identifie : {patient.prenom} {patient.nom} (Carte: {patient.numero_carte})")
        else:
            self._ecrire(f"  Dossier Patient : Non reconnu (visiteur anonyme ou numero non encore rattache)")

        reponse = traiter_message_entrant_whatsapp(expediteur, message_texte)

        self._ecrire("\n--- REPONSE DU BOT SANTESN SUR WHATSAPP ---", self.style.MIGRATE_LABEL)
        self._ecrire(reponse)
        self._ecrire("-------------------------------------------\n", self.style.MIGRATE_LABEL)

    def _tester_push(self, destinataire, texte):
        self._ecrire(f"\n[TEST PUSH NOTIFICATION EN DIRECT]", self.style.SUCCESS)
        self._ecrire(f"  Destinataire : {destinataire}")
        self._ecrire(f"  Texte        : {texte}")

        resultat = envoyer_message_whatsapp(destinataire, texte)
        if resultat.get("succes"):
            self._ecrire(f"  [OK] Envoi Push REUSSI ! ID Meta : {resultat.get('message_id')}", self.style.SUCCESS)
        else:
            self._ecrire(f"  [ATTENTION] Statut : {resultat.get('statut')} - {resultat.get('message')}", self.style.WARNING)

    def _afficher_guide_deploiement(self):
        verify_token = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "santesn_webhook_secret_2026")
        self._ecrire("\n[2/3] PARAMETRES POUR LE REDEPLOIEMENT (META DEVELOPERS) :", self.style.SUCCESS)
        self._ecrire("  Pour activer le Webhook en production sur Meta for Developers :")
        self._ecrire("  1. Connectez-vous sur : https://developers.facebook.com/")
        self._ecrire("  2. Selectionnez votre application WhatsApp Cloud API.")
        self._ecrire("  3. Dans le menu de gauche : WhatsApp > Configuration (Configuration du Webhook).")
        self._ecrire("  4. Renseignez l'URL de rappel (Callback URL) :")
        self._ecrire("     -> https://<votre-domaine-ou-ip>/api/whatsapp/webhook/")
        self._ecrire(f"  5. Renseignez le Jeton de verification (Verify Token) :")
        self._ecrire(f"     -> {verify_token}")
        self._ecrire("  6. Cliquez sur 'Verifier et enregistrer'.")
        self._ecrire("  7. Dans 'Champs du webhook', abonnez-vous a l'evenement :")
        self._ecrire("     -> [x] messages (obligatoire pour recevoir les messages des assures)\n")

        self._ecrire("[3/3] SYNTHESE DES STRATEGIES IMPLEMENTEES :", self.style.SUCCESS)
        self._ecrire("  * STRATEGIE PULL (Assure/Praticien -> SanteSN) :")
        self._ecrire("    - Menu automatique d'accueil (Bonjour, Menu, Aide)")
        self._ecrire("    - Choix 1 : Consultation des droits et du solde annuel restant du foyer")
        self._ecrire("    - Choix 2 : Reservation directe de consultation (RDV [N Medecin] [Date] [Heure] [Motif])")
        self._ecrire("    - Choix 3 : Reseau des cliniques, hopitaux et pharmacies conventionnees")
        self._ecrire("    - Choix 4 : Numeros d'urgence nationale au Senegal (SAMU 1515, Pompiers 18)")
        self._ecrire("  * STRATEGIE PUSH (SanteSN -> Assure/Praticien) :")
        self._ecrire("    - Onboarding : Message de bienvenue et lien d'activation securise a la creation de compte")
        self._ecrire("    - Confirmation automatique lors de la prise de rendez-vous")
        self._ecrire("    - Alerte instantanee au medecin traitant lors d'une nouvelle demande")
        self._ecrire("    - Alerte ordonnance prete et delivree en pharmacie avec QR code securise")
        self._ecrire("    - Resilience Meta : bascule automatique vers le template officiel si hors fenetre 24h\n")
