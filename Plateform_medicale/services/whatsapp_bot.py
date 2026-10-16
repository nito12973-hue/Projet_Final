"""
Service de Chatbot et Webhook WhatsApp pour SantéSN.

Permet aux assurés d'interagir directement via l'application WhatsApp pour :
1. Consulter leurs droits de couverture et leur plafond annuel restant
2. Rechercher un médecin ou une pharmacie conventionnée
3. Prendre un rendez-vous médical directement en envoyant un message WhatsApp
4. Obtenir les numéros d'urgence médicale au Sénégal
"""

import datetime
import logging
import re
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from Plateform_medicale.models import Medecin, Patient, Prestataire, RendezVous, User
from Plateform_medicale.services.notifications import notifier_demande_rdv

logger = logging.getLogger("Plateform_medicale")


def normaliser_numero_telephone(telephone):
    """Normalise un numéro de téléphone au format sénégalais épuré."""
    if not telephone:
        return ""
    chiffres = "".join(filter(str.isdigit, str(telephone)))
    if chiffres.startswith("00"):
        chiffres = chiffres[2:]
    if chiffres.startswith("0") and len(chiffres) == 10:
        chiffres = chiffres[1:]
    if not chiffres.startswith("221") and len(chiffres) == 9:
        chiffres = f"221{chiffres}"
    return chiffres


def trouver_patient_par_telephone(telephone):
    """Retrouve le dossier Patient associé au numéro WhatsApp."""
    tel_norm = normaliser_numero_telephone(telephone)
    if not tel_norm:
        return None

    variantes = {tel_norm}
    if tel_norm.startswith("221") and len(tel_norm) == 12:
        variantes.add(tel_norm[3:])  # sans indicatif (ex: 771234567)
        variantes.add(f"+{tel_norm}")

    # 1. Recherche directe dans la table Patient
    for v in variantes:
        patient = Patient.objects.filter(telephone__icontains=v).first()
        if patient:
            return patient

    # 2. Recherche via le compte User (rôle ASSURE)
    for v in variantes:
        user = User.objects.filter(phone_number__icontains=v, role=User.Role.ASSURE).first()
        if user and hasattr(user, "patient"):
            return user.patient

    return None


def lister_medecins_disponibles(limite=6):
    """Retourne la liste ordonnée des médecins partenaires pour le bot."""
    return list(Medecin.objects.select_related("prestataire").all()[:limite])


def formater_reponse_menu(patient=None):
    """Génère le menu d'accueil du bot SantéSN."""
    nom_affiche = f" {patient.prenom}" if patient else ""
    return (
        f"👋 *Bonjour{nom_affiche} ! Bienvenue sur l'assistant WhatsApp SantéSN.*\n"
        f"Votre plateforme d'assurance santé & prévoyance au Sénégal.\n\n"
        f"Comment pouvons-nous vous aider aujourd'hui ?\n"
        f"1️⃣ *Consulter mes droits et mon plafond restant*\n"
        f"2️⃣ *Prendre un rendez-vous médical direct*\n"
        f"3️⃣ *Trouver un médecin ou une pharmacie partenaire*\n"
        f"4️⃣ *Numéros d'urgence médicale (SAMU, Pompiers)*\n\n"
        f"👉 *Répondez simplement avec le chiffre de votre choix (ex: 2).*"
    )


def formater_reponse_droits(patient):
    """Présente l'état des droits et le solde annuel du foyer de l'assuré."""
    if not patient:
        return (
            "⚠️ *Numéro non reconnu*\n\n"
            "Votre numéro WhatsApp n'est pas encore associé à un dossier assuré SantéSN.\n"
            "Veuillez vous connecter sur votre espace patient ou contacter votre IPM "
            "pour enregistrer votre numéro de téléphone."
        )

    organisme_nom = str(patient.organisme) if patient.organisme else "IPM SantéSN"
    taux = patient.taux_couverture
    taux_str = f"{taux}%" if taux is not None else "Non défini"

    plan = getattr(patient.titulaire, "plan_couverture", None)
    plafond_annuel = getattr(plan, "plafond_annuel", Decimal("500000")) if plan else Decimal("500000")
    consommation = patient.consommation_annuelle_assurance()
    solde_restant = max(Decimal("0"), plafond_annuel - consommation)

    statut_str = "Actif (Validé)" if patient.est_valide else "En attente de validation"

    return (
        f"💳 *Vos Droits d'Assurance SantéSN*\n\n"
        f"👤 *Bénéficiaire :* {patient.nom_complet}\n"
        f"🏛️ *Organisme :* {organisme_nom}\n"
        f"📊 *Taux de prise en charge :* {taux_str}\n"
        f"💰 *Plafond annuel restant :* {int(solde_restant):,} FCFA\n"
        f"📋 *Statut couverture :* {statut_str}\n\n"
        f"Pour revenir au menu principal, envoyez *MENU*."
    )


def formater_reponse_medecins():
    """Présente la liste des praticiens et le guide de prise de rendez-vous."""
    medecins = lister_medecins_disponibles()
    if not medecins:
        return (
            "🩺 *Prise de Rendez-vous Médical*\n\n"
            "Aucun praticien n'est enregistré pour le moment. "
            "Veuillez vous rapprocher de votre centre de santé conventionné."
        )

    lignes = ["📅 *Prendre un Rendez-vous Médical*\n", "Voici la liste des médecins partenaires :"]
    for idx, med in enumerate(medecins, start=1):
        etab = f" ({med.prestataire.nom})" if med.prestataire else ""
        lignes.append(f"{idx}. *Dr. {med.prenom} {med.nom}* - {med.specialite}{etab}")

    lignes.append("\n👉 *Pour réserver, envoyez :*")
    lignes.append("*RDV [N° Médecin] [Date JJ/MM/AAAA] [Heure HH:MM] [Motif]*")
    lignes.append("\n*Exemple :* `RDV 1 25/10/2026 10:30 Consultation de routine`")
    lignes.append("\nPour voir le menu, envoyez *MENU*.")

    return "\n".join(lignes)


def formater_reponse_partenaires():
    """Liste les établissements de soins et pharmacies partenaires."""
    prestataires = list(Prestataire.objects.filter(partenaire=True)[:6])
    if not prestataires:
        return "🏥 Aucun prestataire partenaire n'est actuellement répertorié."

    lignes = ["🏥 *Établissements & Réseau Conventionné :*\n"]
    for p in prestataires:
        tel = f" - 📞 {p.telephone}" if p.telephone else ""
        lignes.append(f"• *{p.nom}* ({p.get_type_prestataire_display()}) - {p.ville}{tel}")

    lignes.append("\nPour réserver avec un médecin, envoyez *2*.")
    return "\n".join(lignes)


def formater_reponse_urgences():
    """Affiche les numéros d'urgence utiles au Sénégal."""
    return (
        "🚨 *Numéros d'Urgence Médicale au Sénégal*\n\n"
        "🚑 *SAMU National :* 1515\n"
        "🚒 *Sapeurs-Pompiers :* 18\n"
        "👮 *Police Secours :* 17\n"
        "🏥 *SOS Médecins Dakar :* +221 33 889 15 15\n"
        "🏥 *Hôpital Principal de Dakar :* +221 33 839 50 50\n"
        "📞 *Assistance Plateforme SantéSN :* +221 78 957 61 45\n\n"
        "Envoyez *MENU* pour revenir au sommaire."
    )


def reserver_rendez_vous_whatsapp(patient, medecin, date_heure, motif=""):
    """Crée le rendez-vous dans la base de données et émet les notifications."""
    # Vérification que le créneau n'est pas déjà occupé pour ce médecin
    conflit = RendezVous.objects.filter(
        medecin=medecin,
        date_heure=date_heure,
    ).exclude(
        statut__in=[RendezVous.Statut.ANNULE, RendezVous.Statut.REFUSE, RendezVous.Statut.ABSENT]
    ).exists()

    if conflit:
        return False, (
            f"⚠️ *Créneau indisponible*\n\n"
            f"Le Dr. {medecin.prenom} {medecin.nom} est déjà occupé le "
            f"{date_heure.strftime('%d/%m/%Y à %H:%M')}.\n"
            f"Veuillez choisir un autre jour ou une heure différente."
        )

    # Création effective du rendez-vous
    rdv = RendezVous.objects.create(
        patient=patient,
        medecin=medecin,
        prestataire=medecin.prestataire,
        date_heure=date_heure,
        motif=motif.strip() or "Demande de consultation via WhatsApp",
        statut=RendezVous.Statut.DEMANDE,
    )

    # Déclenchement de la notification (Email, tableau de bord, WhatsApp)
    try:
        notifier_demande_rdv(rdv)
    except Exception as exc:
        logger.warning("Échec notification pour RDV WhatsApp %s: %s", rdv.pk, exc)

    prestataire_str = f"🏥 *Lieu :* {rdv.prestataire.nom}\n" if rdv.prestataire else ""
    return True, (
        f"✅ *Votre rendez-vous a été enregistré !*\n\n"
        f"🩺 *Médecin :* Dr. {medecin.prenom} {medecin.nom} ({medecin.specialite})\n"
        f"📅 *Date & Heure :* {date_heure.strftime('%d/%m/%Y à %H:%M')}\n"
        f"{prestataire_str}"
        f"📋 *Motif :* {rdv.motif}\n"
        f"⏳ *Statut :* Demande transmise au praticien (en attente de confirmation).\n\n"
        f"Vous recevrez une alerte de confirmation dès que le praticien aura validé le créneau.\n"
        f"Retrouvez votre rendez-vous à tout moment sur votre espace SantéSN."
    )


def parser_demande_rdv(texte, patient):
    """
    Tente de parser une instruction de réservation directe du type :
    - 'RDV 1 25/10/2026 10:30 Consultation'
    - '1 25/10/2026 10h30'
    - 'RDV 2 2026-10-25 15:00 Maux de tete'
    """
    if not patient:
        return (
            "⚠️ *Compte assuré introuvable*\n\n"
            "Pour prendre rendez-vous automatiquement par WhatsApp, votre numéro doit être "
            "rattaché à un dossier assuré SantéSN.\n"
            "Rapprochez-vous de votre gestionnaire d'IPM ou de mutuelle."
        )

    medecins = lister_medecins_disponibles()
    if not medecins:
        return "⚠️ Aucun médecin n'est disponible pour la prise de rendez-vous pour le moment."

    # Motif regex pour capturer: index medecin, date, heure, motif
    regex = re.compile(
        r"^(?:rdv\s+)?(\d+)\s+([0-9]{1,4}[\/\.-][0-9]{1,2}[\/\.-][0-9]{1,4})\s+(?:à\s*|a\s*)?([0-9]{1,2}(?:h|:)[0-9]{0,2})(?:\s+(.*))?$",
        re.IGNORECASE,
    )

    match = regex.match(texte.strip())
    if not match:
        return None

    idx_str, date_str, heure_str, motif = match.groups()
    motif = motif or ""

    try:
        idx = int(idx_str)
        if idx < 1 or idx > len(medecins):
            return f"⚠️ Numéro de praticien invalide ({idx}). Choisissez un chiffre entre 1 et {len(medecins)}."
        medecin = medecins[idx - 1]
    except Exception:
        return "⚠️ Choix du praticien invalide."

    # Normalisation de l'heure
    heure_str = heure_str.lower().replace("h", ":")
    if ":" not in heure_str:
        heure_str = f"{heure_str}:00"
    elif heure_str.endswith(":"):
        heure_str = f"{heure_str}00"

    parties_h = heure_str.split(":")
    heure_val = int(parties_h[0])
    minute_val = int(parties_h[1]) if len(parties_h) > 1 and parties_h[1] else 0

    # Normalisation de la date
    date_obj = None
    for separateur in ["/", "-", "."]:
        if separateur in date_str:
            elements = date_str.split(separateur)
            if len(elements) == 3:
                try:
                    if len(elements[0]) == 4:  # YYYY-MM-DD
                        date_obj = datetime.date(int(elements[0]), int(elements[1]), int(elements[2]))
                    else:  # DD-MM-YYYY
                        date_obj = datetime.date(int(elements[2]), int(elements[1]), int(elements[0]))
                    break
                except ValueError:
                    continue

    if not date_obj:
        return "⚠️ Format de date invalide. Utilisez le format JJ/MM/AAAA (ex: 25/10/2026)."

    try:
        heure_obj = datetime.time(heure_val, minute_val)
    except ValueError:
        return "⚠️ Heure invalide. Utilisez un format comme 10:30 ou 15h00."

    tz = timezone.get_current_timezone()
    rdv_datetime = timezone.make_aware(datetime.datetime.combine(date_obj, heure_obj), tz)

    if rdv_datetime < timezone.now():
        return (
            "⚠️ *Date déjà dépassée*\n\n"
            "Vous avez sélectionné une date ou une heure passée. "
            "Veuillez choisir un créneau futur pour votre consultation."
        )

    succes, message = reserver_rendez_vous_whatsapp(patient, medecin, rdv_datetime, motif)
    return message


def traiter_message_entrant_whatsapp(expediteur_telephone, texte_message):
    """
    Point d'entrée du moteur conversationnel WhatsApp.
    Analyse le message reçu et renvoie la réponse texte appropriée.
    """
    texte = (texte_message or "").strip()
    patient = trouver_patient_par_telephone(expediteur_telephone)

    if not texte:
        return formater_reponse_menu(patient)

    texte_lower = texte.lower().strip()

    # 1. Tentative de parsing d'une réservation directe (ex: 'RDV 1 25/10/2026 10h00')
    reponse_rdv = parser_demande_rdv(texte, patient)
    if reponse_rdv:
        return reponse_rdv

    # 2. Commandes de menu / salutations
    if texte_lower in ("bonjour", "salut", "bonsoir", "hello", "hi", "menu", "aide", "help", "start"):
        return formater_reponse_menu(patient)

    # 3. Choix 1 : Droits & Solde
    if texte_lower in ("1", "solde", "droit", "droits", "couverture", "plafond", "mon solde"):
        return formater_reponse_droits(patient)

    # 4. Choix 2 : Demande de rendez-vous / Liste des praticiens
    if texte_lower in ("2", "rdv", "rendez-vous", "rendez vous", "prendre rdv", "prendre un rdv", "docteur", "medecin"):
        return formater_reponse_medecins()

    # 5. Choix 3 : Partenaires & Réseau conventionné
    if texte_lower in ("3", "partenaire", "partenaires", "pharmacie", "pharmacies", "clinique", "prestataire"):
        return formater_reponse_partenaires()

    # 6. Choix 4 : Urgences
    if texte_lower in ("4", "urgence", "urgences", "samu", "pompier", "pompiers", "secours"):
        return formater_reponse_urgences()

    # 7. Si le texte contient explicitement "rdv" ou "rendez" sans respecter la syntaxe complète
    if "rdv" in texte_lower or "rendez" in texte_lower:
        return formater_reponse_medecins()

    # Réponse par défaut : guidage bienveillant
    return (
        "🤖 Je n'ai pas bien compris votre demande.\n\n"
        + formater_reponse_menu(patient)
    )
