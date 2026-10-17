"""
Service de Chatbot et Webhook WhatsApp pour SantéSN.

Permet aux assurés d'interagir directement via l'application WhatsApp pour :
1. Consulter leurs droits de couverture et leur plafond annuel restant
2. Rechercher un médecin ou une pharmacie conventionnée avec tri par proximité
3. Prendre un rendez-vous médical directement en envoyant un message WhatsApp
4. Obtenir les numéros d'urgence médicale au Sénégal
5. Lier instantanément un compte assuré via son numéro de carte ou son email
"""

import datetime
import logging
import re
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from Plateform_medicale.models import Medecin, Patient, Prestataire, RendezVous, User, distance_km
from Plateform_medicale.services.notifications import notifier_demande_rdv

logger = logging.getLogger("Plateform_medicale")

JOURS_SEMAINE = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}


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
    """
    Retrouve le dossier Patient associé au numéro WhatsApp de manière résiliente :
    - Tolérance aux indicatifs (+221, 221, 00221, 9 chiffres)
    - Tolérance aux espaces, tirets et ponctuations dans la base
    - Recherche dans Patient et User (rôle ASSURE)
    """
    tel_norm = normaliser_numero_telephone(telephone)
    if not tel_norm:
        return None

    variantes = {tel_norm}
    if tel_norm.startswith("221") and len(tel_norm) == 12:
        variantes.add(tel_norm[3:])  # sans indicatif (ex: 761863108)
        variantes.add(f"+{tel_norm}")
        variantes.add(f"00{tel_norm}")

    # 1. Recherche directe dans la table Patient (icontains)
    for v in variantes:
        patient = Patient.objects.filter(telephone__icontains=v).first()
        if patient:
            return patient

    # 2. Recherche via le compte User (rôle ASSURE)
    for v in variantes:
        user = User.objects.filter(phone_number__icontains=v, role=User.Role.ASSURE).first()
        if user and hasattr(user, "patient"):
            return user.patient

    # 3. Parcours avec normalisation stricte pour gérer les espaces stockés en base (ex: '76 186 31 08')
    for p in Patient.objects.exclude(telephone="").only("id", "telephone", "prenom", "nom", "numero_carte", "adresse", "user"):
        if normaliser_numero_telephone(p.telephone) == tel_norm:
            return p

    for u in User.objects.filter(role=User.Role.ASSURE).exclude(phone_number="").only("id", "phone_number"):
        if normaliser_numero_telephone(u.phone_number) == tel_norm and hasattr(u, "patient"):
            return u.patient

    return None


def tenter_liaison_automatique(expediteur_telephone, texte):
    """
    Permet à un assuré d'associer instantanément son numéro WhatsApp à son dossier
    en envoyant simplement son numéro de carte (ex: SN-36D66F3046) ou son adresse email.
    """
    if not texte or not expediteur_telephone:
        return None, None

    tel_norm = normaliser_numero_telephone(expediteur_telephone)
    if not tel_norm:
        return None, None

    texte_propre = texte.strip()
    patient = None

    # 1. Recherche par numéro de carte (ex: SN-36D66F3046 ou 36D66F3046)
    match_carte = re.search(r"(?:sn[-_ ]?)?([a-z0-9]{8,14})", texte_propre, re.IGNORECASE)
    if match_carte:
        code_carte = match_carte.group(1).upper()
        patient = (
            Patient.objects.filter(numero_carte__iexact=f"SN-{code_carte}").first()
            or Patient.objects.filter(numero_carte__iexact=code_carte).first()
            or Patient.objects.filter(numero_carte__icontains=code_carte).first()
        )

    # 2. Recherche par adresse email (ex: lamaranitodiallo2908@gmail.com)
    if not patient:
        match_email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", texte_propre)
        if match_email:
            email_trouve = match_email.group(0).lower()
            patient = Patient.objects.filter(user__email__iexact=email_trouve).first()

    if not patient:
        return None, None

    # Enregistrement du numéro WhatsApp pour l'assuré
    patient.telephone = tel_norm
    patient.save(update_fields=["telephone"])

    if patient.user:
        patient.user.phone_number = tel_norm
        patient.user.save(update_fields=["phone_number"])

    nom_complet = f"{patient.prenom} {patient.nom}".strip()
    msg = (
        f"🎉 *Compte SantéSN associé avec succès !*\n\n"
        f"Bonjour *{nom_complet}*,\n"
        f"Votre numéro WhatsApp (+{tel_norm}) est désormais relié à votre carte assuré *{patient.numero_carte}*.\n\n"
        f"Vous pouvez dès à présent gérer vos consultations et vos droits directement sur WhatsApp :\n"
        f"• *1* : Voir vos droits et solde annuel restant\n"
        f"• *2* : Prendre un rendez-vous médical direct\n"
        f"• *3* : Établissements & pharmacies conventionnées\n"
        f"• *4* : Numéros d'urgence médicale\n\n"
        f"👉 *Envoyez 2 ou RDV pour choisir un médecin proche de chez vous !*"
    )
    return patient, msg


def lister_medecins_disponibles(patient=None, ville=None, coords_gps=None, limite=6):
    """
    Retourne la liste des médecins partenaires en privilégiant la proximité géographique :
    1. Si coordonnées GPS fournies (partage de position WhatsApp) : tri par distance (km)
    2. Si une ville est précisée (ex: "RDV Thiès", "RDV Dakar") : filtre par cette ville
    3. Si patient identifié : privilégie sa ville/région d'adresse
    """
    qs = Medecin.objects.select_related("prestataire")
    qs = qs.filter(Q(user__is_active=True) | Q(user__isnull=True))

    # 1. Si coordonnées GPS transmises sur WhatsApp
    if coords_gps and len(coords_gps) == 2:
        lat_u, lng_u = coords_gps
        avec_dist = []
        sans_dist = []
        for m in qs:
            if m.prestataire and m.prestataire.latitude is not None and m.prestataire.longitude is not None:
                d = round(distance_km(lat_u, lng_u, float(m.prestataire.latitude), float(m.prestataire.longitude)), 1)
                avec_dist.append((m, d))
            else:
                sans_dist.append((m, None))
        avec_dist.sort(key=lambda x: x[1])
        tous = [m for m, d in avec_dist] + [m for m, d in sans_dist]
        d_map = dict(avec_dist)
        for m in tous:
            m._distance_km = d_map.get(m)
        return tous[:limite]

    # 2. Si une ville ou quartier spécifique est mentionné (ex: "Thiès", "Dakar", "Mbour", "Touba")
    if ville:
        qs_ville = qs.filter(
            Q(prestataire__ville__icontains=ville)
            | Q(prestataire__adresse__icontains=ville)
        )
        if qs_ville.exists():
            return list(qs_ville[:limite])

    # 3. Si patient identifié : privilégier les médecins proches de son adresse
    if patient:
        ville_patient = ""
        adresse_patient = getattr(patient, "adresse", "") or ""
        if adresse_patient:
            villes_senegal = [
                "Dakar", "Plateau", "Médina", "Fann", "Point E", "Mermoz", "Almadies",
                "Yoff", "Pikine", "Guédiawaye", "Rufisque", "Thiès", "Mbour", "Saly",
                "Saint-Louis", "Touba", "Kaolack", "Ziguinchor", "Diourbel", "Fatick", "Kolda"
            ]
            for v in villes_senegal:
                if v.lower() in adresse_patient.lower():
                    ville_patient = v
                    break

        if ville_patient:
            qs_proches = qs.filter(
                Q(prestataire__ville__icontains=ville_patient)
                | Q(prestataire__adresse__icontains=ville_patient)
            )
            if qs_proches.exists():
                proches = list(qs_proches[:limite])
                if len(proches) < limite:
                    autres = list(qs.exclude(pk__in=[m.pk for m in proches])[:limite - len(proches)])
                    return proches + autres
                return proches

    return list(qs[:limite])


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
        f"4️⃣ *Numéros d'urgence médicale (SAMU 1515, Pompiers 18)*\n\n"
        f"👉 *Répondez simplement avec le chiffre de votre choix (ex: 2).*"
    )


def formater_reponse_droits(patient):
    """Présente l'état des droits et le solde annuel du foyer de l'assuré."""
    if not patient:
        return (
            "⚠️ *Numéro non reconnu*\n\n"
            "Votre numéro WhatsApp n'est pas encore associé à un dossier assuré SantéSN.\n"
            "👉 Pour l'associer en 5 secondes, envoyez votre *numéro de carte assuré* "
            "(ex: `SN-36D66F3046`) ou votre *adresse email*."
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


def formater_reponse_medecins(patient=None, ville=None, coords_gps=None):
    """Présente la liste des praticiens ordonnée par proximité et conventionnement."""
    medecins = lister_medecins_disponibles(patient=patient, ville=ville, coords_gps=coords_gps)
    if not medecins:
        if ville:
            return (
                f"🩺 *Recherche de Médecins à {ville.capitalize()}*\n\n"
                f"Aucun médecin partenaire n'a été trouvé à *{ville.capitalize()}* pour le moment.\n"
                f"Envoyez *2* pour voir tous les praticiens conventionnés disponibles."
            )
        return (
            "🩺 *Prise de Rendez-vous Médical*\n\n"
            "Aucun praticien n'est enregistré pour le moment. "
            "Veuillez vous rapprocher de votre centre de santé conventionné."
        )

    titre_section = "Voici la liste des médecins partenaires :"
    if coords_gps:
        titre_section = "📍 Médecins les plus proches de *votre position GPS* :"
    elif ville:
        titre_section = f"📍 Médecins partenaires disponibles à *{ville.capitalize()}* :"
    elif patient and getattr(patient, "adresse", ""):
        titre_section = "📍 Médecins partenaires recommandés proches de chez vous :"

    lignes = ["📅 *Prendre un Rendez-vous Médical*\n", titre_section]
    for idx, med in enumerate(medecins, start=1):
        etab_parts = []
        if med.prestataire:
            etab_parts.append(med.prestataire.nom)
            if med.prestataire.ville:
                etab_parts.append(med.prestataire.ville)
        etab = f" ({' - '.join(etab_parts)})" if etab_parts else ""
        dist = getattr(med, "_distance_km", None)
        dist_str = f" [à {dist} km]" if dist is not None else ""
        lignes.append(f"{idx}. *Dr. {med.prenom} {med.nom}* - {med.specialite}{etab}{dist_str}")

    lignes.append("\n👉 *Pour réserver en direct, écrivez :*")
    lignes.append("*RDV [N° Médecin] [Date JJ/MM/AAAA] [Heure HH:MM] [Motif]*")
    lignes.append("\n*Exemple :* `RDV 1 25/10/2026 10:30 Consultation de routine`")
    lignes.append("\n*Exemples rapides :*")
    lignes.append("• `RDV 1 demain à 10h30`")
    lignes.append("• `RDV 1 25/10 15:00`")
    lignes.append("• `RDV 1` (pour être guidé étape par étape)")
    lignes.append("\n💡 *Pour filtrer par ville :* envoyez `RDV [Ville]` (ex: *RDV Thiès* ou *RDV Dakar*).")
    lignes.append("Vous pouvez aussi envoyer votre *position GPS* sur WhatsApp !")

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

    rdv = RendezVous.objects.create(
        patient=patient,
        medecin=medecin,
        prestataire=medecin.prestataire,
        date_heure=date_heure,
        motif=motif.strip() or "Demande de consultation via WhatsApp",
        statut=RendezVous.Statut.DEMANDE,
    )

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


def extraire_date_naturelle(chaine, date_ref=None):
    """
    Extrait une date à partir d'expressions naturelles ou calendaires :
    - 'demain', 'après-demain', 'apres-demain'
    - 'lundi', 'mardi', 'mercredi', etc.
    - '25/10/2026', '25-10-2026', '25.10.2026'
    - '25/10/26'
    - '25/10' (déduit automatiquement l'année en cours)
    """
    if date_ref is None:
        date_ref = timezone.now().date()

    chaine_lower = chaine.lower().strip()

    # Relative : après-demain
    if "après-demain" in chaine_lower or "apres-demain" in chaine_lower or "apres demain" in chaine_lower:
        return date_ref + datetime.timedelta(days=2), "apres-demain"

    # Relative : demain
    if "demain" in chaine_lower:
        return date_ref + datetime.timedelta(days=1), "demain"

    # Jours de la semaine (ex: lundi, mardi)
    for nom_j, num_j in JOURS_SEMAINE.items():
        if re.search(rf"\b{nom_j}\b", chaine_lower):
            diff = (num_j - date_ref.weekday()) % 7
            if diff == 0:
                diff = 7  # Prochain [jour]
            return date_ref + datetime.timedelta(days=diff), nom_j

    # Date calendaire explicite
    m_date = re.search(r"(\b\d{1,2})[\/\.-](\d{1,2})(?:[\/\.-](\d{2,4}))?\b", chaine)
    if m_date:
        jour = int(m_date.group(1))
        mois = int(m_date.group(2))
        annee_str = m_date.group(3)
        if annee_str:
            annee = int(annee_str)
            if annee < 100:
                annee += 2000
        else:
            annee = date_ref.year

        try:
            d = datetime.date(annee, mois, jour)
            if not annee_str and d < date_ref:
                d = datetime.date(annee + 1, mois, jour)
            return d, m_date.group(0)
        except ValueError:
            pass

    return None, None


def extraire_heure_minute(chaine):
    """
    Extrait l'heure et la minute depuis des expressions variées :
    - '10h30', '10h', '10:30', '10:00', '14h00', 'à 10h', 'a 10h30'
    """
    m = re.search(r"(?:à\s*|a\s*)?(\b\d{1,2})(?:[h:]([0-5]?\d)?)?\b", chaine, re.IGNORECASE)
    if not m:
        return None, None
    h = int(m.group(1))
    minute_str = m.group(2)
    m_val = int(minute_str) if minute_str else 0
    if 0 <= h <= 23 and 0 <= m_val <= 59:
        return h, m_val
    return None, None


def parser_demande_rdv(texte, patient):
    """
    Moteur conversationnel flexible de prise de rendez-vous :
    Supporte :
    1. Réservation complète directe :
       - 'RDV 1 25/10/2026 10:30 Consultation'
       - 'RDV 1 25/10 10h30'
       - 'RDV 1 demain 10h'
       - 'RDV 1 demain à 14h30'
       - 'RDV 2 lundi 10h Consultation générale'
       - '1 25/10 10:00'
    2. Sélection de praticien seule (guidage interactif) :
       - 'RDV 1' ou '1'
    """
    if not texte:
        return None

    texte_propre = texte.strip()
    texte_lower = texte_propre.lower()

    # Détecte le numéro du médecin sélectionné
    # Motifs : "RDV 1 ...", "RDV Dr 1 ...", ou "1 [date/heure]..."
    match_med = re.match(r"^(?:rdv\s+|dr\s+|docteur\s+|medecin\s+|choix\s+)?(\d{1,2})(?:\s+(.*))?$", texte_propre, re.IGNORECASE)
    if not match_med:
        return None

    idx_str, reste_texte = match_med.groups()
    reste_texte = (reste_texte or "").strip()

    # Si pas de texte supplémentaire (date/heure), il faut impérativement un préfixe de commande (RDV, Dr, Choix)
    # pour ne jamais entrer en conflit avec les options numériques de menu ('1', '2', '3', '4')
    if not reste_texte and not re.match(r"^(?:rdv|dr|docteur|medecin|choix)\b", texte_propre, re.IGNORECASE):
        return None

    if not patient:
        return (
            "⚠️ *Compte assuré non identifié*\n\n"
            "Pour prendre rendez-vous automatiquement sur WhatsApp, votre numéro doit être "
            "associé à votre dossier assuré SantéSN.\n\n"
            "👉 *Envoyez simplement votre numéro de carte (ex: SN-36D66F3046) ou votre adresse email pour l'activer !*"
        )

    medecins = lister_medecins_disponibles(patient=patient)
    if not medecins:
        return "⚠️ Aucun médecin n'est disponible pour la prise de rendez-vous pour le moment."

    try:
        idx = int(idx_str)
        if idx < 1 or idx > len(medecins):
            return f"⚠️ Numéro de praticien invalide ({idx}). Choisissez un chiffre entre 1 et {len(medecins)}."
        medecin = medecins[idx - 1]
    except Exception:
        return "⚠️ Choix du praticien invalide."

    # Si l'utilisateur a envoyé UNIQUEMENT le numéro du médecin (ex: 'RDV 1')
    if not reste_texte:
        etab_nom = medecin.prestataire.nom if medecin.prestataire else "Cabinet conventionné"
        return (
            f"🩺 *Vous avez sélectionné le Dr. {medecin.prenom} {medecin.nom}*\n"
            f"• Spécialité : {medecin.specialite}\n"
            f"• Établissement : {etab_nom}\n\n"
            f"Pour quel jour et quelle heure souhaitez-vous votre rendez-vous ?\n\n"
            f"👉 *Répondez simplement par exemple :*\n"
            f"• `RDV {idx} demain à 10h30`\n"
            f"• `RDV {idx} 25/10 à 15h00`\n"
            f"• `RDV {idx} lundi à 11h Consultation`"
        )

    # Analyse de la date
    date_obj, date_token = extraire_date_naturelle(reste_texte)
    if not date_obj:
        return (
            f"⚠️ *Date de rendez-vous non reconnue*\n\n"
            f"Veuillez préciser la date voulue pour le Dr. {medecin.prenom} {medecin.nom}.\n"
            f"Exemples valides :\n"
            f"• `RDV {idx} demain à 10h`\n"
            f"• `RDV {idx} 25/10 à 15h00`\n"
            f"• `RDV {idx} 25/10/2026 10:30`"
        )

    # Suppression du token date pour extraire l'heure et le motif restant
    texte_sans_date = reste_texte
    if date_token:
        texte_sans_date = re.sub(re.escape(date_token), "", reste_texte, flags=re.IGNORECASE).strip()

    # Analyse de l'heure
    heure_val, minute_val = extraire_heure_minute(texte_sans_date)
    if heure_val is None:
        return (
            f"⚠️ *Heure de rendez-vous manquante*\n\n"
            f"Veuillez préciser l'heure souhaitée pour le {date_obj.strftime('%d/%m/%Y')}.\n"
            f"Exemple : `RDV {idx} {date_token} à 10h30` ou `RDV {idx} {date_token} 15:00`"
        )

    try:
        heure_obj = datetime.time(heure_val, minute_val)
    except ValueError:
        return "⚠️ Heure invalide. Utilisez un format comme 10:30 ou 15h00."

    # Motif restant (texte restant après extraction de date et heure)
    motif = re.sub(r"(?:à\s*|a\s*)?\b\d{1,2}(?:[h:]\d{0,2})?\b", "", texte_sans_date, flags=re.IGNORECASE).strip()

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
    Point d'entrée du moteur conversationnel WhatsApp SantéSN.
    Traite le message reçu, résout l'assuré ou lie son compte, et renvoie la réponse adaptée.
    """
    texte = (texte_message or "").strip()
    patient = trouver_patient_par_telephone(expediteur_telephone)

    # 0. Si le patient n'est pas encore lié : tentative de liaison automatique
    if not patient and texte:
        patient_lie, msg_liaison = tenter_liaison_automatique(expediteur_telephone, texte)
        if patient_lie:
            return msg_liaison

    if not texte:
        return formater_reponse_menu(patient)

    texte_lower = texte.lower().strip()

    # 1. Coordonnées GPS reçues (partage de position WhatsApp "LOCATION lat lng")
    if texte_lower.startswith("location "):
        morceaux_loc = texte.split()
        if len(morceaux_loc) >= 3:
            try:
                lat = float(morceaux_loc[1])
                lng = float(morceaux_loc[2])
                return formater_reponse_medecins(patient=patient, coords_gps=(lat, lng))
            except ValueError:
                pass

    # 2. Commandes de menu / salutations
    if texte_lower in ("bonjour", "salut", "bonsoir", "hello", "hi", "menu", "aide", "help", "start"):
        return formater_reponse_menu(patient)

    # 3. Choix 1 : Droits & Solde
    if texte_lower in ("1", "solde", "droit", "droits", "couverture", "plafond", "mon solde"):
        return formater_reponse_droits(patient)

    # 4. Choix 2 : Demande de rendez-vous / Liste des praticiens
    if texte_lower in ("2", "rdv", "rendez-vous", "rendez vous", "prendre rdv", "prendre un rdv", "docteur", "medecin"):
        return formater_reponse_medecins(patient=patient)

    # 5. Choix 3 : Partenaires & Réseau conventionné
    if texte_lower in ("3", "partenaire", "partenaires", "pharmacie", "pharmacies", "clinique", "prestataire"):
        return formater_reponse_partenaires()

    # 6. Choix 4 : Urgences
    if texte_lower in ("4", "urgence", "urgences", "samu", "pompier", "pompiers", "secours"):
        return formater_reponse_urgences()

    # 7. Recherche par ville : ex: "rdv dakar", "rdv thies", "rdv mbour", "rdv touba"
    match_rdv_ville = re.match(r"^rdv\s+([a-zA-Zà-ÿ\s-]+)$", texte.strip(), re.IGNORECASE)
    if match_rdv_ville:
        nom_ville = match_rdv_ville.group(1).strip()
        if nom_ville.lower() not in ("menu", "aide", "help", "docteur", "medecin", "partenaire"):
            # Si ce n'est pas un chiffre, on filtre par cette ville
            if not nom_ville.isdigit():
                return formater_reponse_medecins(patient=patient, ville=nom_ville)

    # 8. Tentative de parsing d'une réservation directe ou choix de médecin (ex: 'RDV 1 25/10 10h', 'RDV 1 demain 10h', 'RDV 1')
    reponse_rdv = parser_demande_rdv(texte, patient)
    if reponse_rdv:
        return reponse_rdv

    # 9. Si le texte contient explicitement "rdv" ou "rendez"
    if "rdv" in texte_lower or "rendez" in texte_lower:
        return formater_reponse_medecins(patient=patient)

    # 9. Réponse par défaut bienveillante
    if not patient:
        return (
            "👋 *Bienvenue sur l'assistant WhatsApp SantéSN !*\n\n"
            "Votre numéro WhatsApp n'est pas encore associé à votre dossier assuré.\n\n"
            "👉 *Pour activer votre compte en 5 secondes, écrivez simplement :*\n"
            "• Votre *numéro de carte assuré* (ex: `SN-36D66F3046`)\n"
            "• OU votre *adresse email* (ex: `lamaranitodiallo2908@gmail.com`)\n\n"
            "Dès réception, vous pourrez prendre vos rendez-vous et consulter vos droits directement ici !"
        )

    return (
        "🤖 Je n'ai pas bien compris votre message.\n\n"
        + formater_reponse_menu(patient)
    )
