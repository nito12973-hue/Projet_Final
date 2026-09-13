"""
Service métier de l'Assistant SantéSN.

Moteur d'intentions déterministe, sécurisé et rapide pour les assurés.
Interroge exclusivement les données du patient authentifié et respecte
strictement les limites déontologiques et médicales.
"""

import re
from django.urls import reverse
from django.utils import timezone
from ..models import Patient, RendezVous, Ordonnance, PriseEnCharge


# Mots-clés de détresse / urgence vitale
MOTS_CLES_URGENCE = [
    "urgence", "urgences", "samu", "1515", "pompiers", "18",
    "douleur thoracique", "infarctus", "avc", "étouffement", "etouffement",
    "inconscient", "perte de connaissance", "coma", "hémorragie", "hemorragie",
    "détresse respiratoire", "detresse respiratoire", "convulsion"
]

# Mots-clés de demande de diagnostic ou de prescription
MOTS_CLES_MEDICAL = [
    "diagnostic", "diagnostique", "quel médicament", "quel medicament",
    "que prendre", "posologie", "automédication", "automedication",
    "fièvre", "fievre", "maux de tête", "maux de tete", "mal de ventre",
    "douleur au ventre", "vomissement", "diarrhée", "diarrhee", "toux",
    "grippe", "paludisme", "palu", "tension"
]


def traiter_message_assistant(user, message_texte):
    """
    Analyse le message d'un assuré et retourne une réponse structurée :
    {
        "texte": str,
        "type": "urgence" | "medical_warning" | "donnees" | "aide" | "support" | "defaut",
        "actions": [ {"libelle": str, "url": str, "style": "primary" | "secondary"} ],
        "suggestions": [str]
    }
    """
    texte_brut = (message_texte or "").strip()
    texte_lower = texte_brut.lower()

    # 1. DÉTECTION URGENCE VITALE (Priorité absolue)
    for mot in MOTS_CLES_URGENCE:
        if re.search(r'\b' + re.escape(mot) + r'\b', texte_lower):
            return {
                "type": "urgence",
                "texte": (
                    "🚨 **SITUATION D'URGENCE MÉDICALE DÉTECTÉE**\n\n"
                    "L'Assistant SantéSN ne peut pas traiter les urgences vitales. "
                    "Si vous-même ou un proche êtes en détresse, **contactez immédiatement les secours au Sénégal :**\n\n"
                    "- 📞 **SAMU National : 15 15** (numéro d'urgence médicale gratuit)\n"
                    "- 🚒 **Sapeurs-Pompiers : 18**\n"
                    "- 🏥 Ou présentez-vous sans délai au service d'accueil des urgences le plus proche."
                ),
                "actions": [
                    {"libelle": "Trouver un hôpital proche", "url": reverse("prestataires_proches"), "style": "primary"},
                ],
                "suggestions": [
                    "Quels sont mes prochains rendez-vous ?",
                    "Où trouver un médecin ?",
                    "Contacter l'administration"
                ]
            }

    # 2. DÉTECTION DEMANDE MÉDICALE CLINIQUE (Pas de diagnostic automatisé)
    for mot in MOTS_CLES_MEDICAL:
        if re.search(r'\b' + re.escape(mot) + r'\b', texte_lower):
            return {
                "type": "medical_warning",
                "texte": (
                    "ℹ️ **Rappel déontologique médical :**\n\n"
                    "En tant qu'Assistant SantéSN, **je ne suis pas habilité à poser de diagnostic ni à prescrire un traitement.** "
                    "Seul un médecin qualifié peut vous examiner et prescrire les soins adaptés à votre état de santé.\n\n"
                    "👉 Vous pouvez prendre rendez-vous en ligne avec l'un de nos praticiens conventionnés ou consulter la liste des prestataires proches."
                ),
                "actions": [
                    {"libelle": "Prendre un rendez-vous médical", "url": reverse("ajouter_rendez_vous_assure"), "style": "primary"},
                    {"libelle": "Trouver un centre de santé", "url": reverse("prestataires_proches"), "style": "secondary"}
                ],
                "suggestions": [
                    "Comment prendre un rendez-vous ?",
                    "Mes ordonnances en cours",
                    "Contacter l'administration"
                ]
            }

    patient = getattr(user, "patient", None)

    # 3. INTENTION : RENDEZ-VOUS
    if any(k in texte_lower for k in ["rendez-vous", "rdv", "consultation", "mon médecin", "prochain rdv"]):
        if not patient:
            return _reponse_sans_profil_patient()
        
        maintenant = timezone.now()
        prochains_rdv = RendezVous.objects.filter(
            patient__in=[patient.pk] + list(patient.ayants_droit.values_list("pk", flat=True)),
            date_heure__gte=maintenant
        ).select_related("medecin", "prestataire", "patient").order_by("date_heure")[:3]

        if prochains_rdv:
            lignes = []
            for r in prochains_rdv:
                statut_lbl = r.get_statut_display()
                date_str = r.date_heure.strftime("%d/%m/%Y à %H:%M")
                med_nom = str(r.medecin) if r.medecin else "Praticien du centre"
                prest_nom = r.prestataire.nom if r.prestataire else "Cabinet"
                lignes.append(f"- **{date_str}** : Dr. {med_nom} ({prest_nom}) · Statut : *{statut_lbl}* ({r.patient.prenom})")
            
            texte = (
                f"📅 **Vos prochains rendez-vous programmés :**\n\n"
                + "\n".join(lignes)
                + "\n\nVous pouvez consulter l'historique complet ou demander un nouveau créneau ci-dessous."
            )
        else:
            texte = (
                "📅 **Vous n'avez aucun rendez-vous à venir pour le moment.**\n\n"
                "Souhaitez-vous programmer une nouvelle consultation avec un médecin conventionné ?"
            )

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "primary"},
                {"libelle": "Voir tous mes rendez-vous", "url": reverse("mes_rendez_vous_assure"), "style": "secondary"}
            ],
            "suggestions": [
                "Quel est mon taux de prise en charge ?",
                "Mes ordonnances",
                "Ma carte d'assuré"
            ]
        }

    # 4. INTENTION : ORDONNANCES & PHARMACIE
    if any(k in texte_lower for k in ["ordonnance", "médicament", "medicament", "pharmacie", "délivrance", "delivrance"]):
        if not patient:
            return _reponse_sans_profil_patient()

        dernieres_ord = Ordonnance.objects.filter(
            consultation__patient__in=[patient.pk] + list(patient.ayants_droit.values_list("pk", flat=True))
        ).select_related("consultation__medecin", "consultation__patient").order_by("-date_emission")[:3]

        if dernieres_ord:
            lignes = []
            for o in dernieres_ord:
                statut_badge = o.get_statut_display()
                date_str = o.date_emission.strftime("%d/%m/%Y")
                med_nom = str(o.consultation.medecin) if o.consultation and o.consultation.medecin else "Médecin"
                lignes.append(f"- **Réf. {o.code_qr}** du {date_str} (Dr. {med_nom}) · Statut : *{statut_badge}*")
            
            texte = (
                "💊 **Vos dernières prescriptions médicales :**\n\n"
                + "\n".join(lignes)
                + "\n\nPrésentez simplement le QR Code de votre ordonnance dans l'une de nos pharmacies partenaires."
            )
        else:
            texte = (
                "💊 **Aucune ordonnance n'est enregistrée sur votre compte pour l'instant.**\n\n"
                "Vos ordonnances s'affichent automatiquement ici dès qu'un médecin conventionné vous en prescrit une."
            )

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Consulter mes ordonnances", "url": reverse("mes_ordonnances_assure"), "style": "primary"}
            ],
            "suggestions": [
                "Prendre un rendez-vous",
                "Mon taux de couverture",
                "Contacter l'administration"
            ]
        }

    # 5. INTENTION : PRISE EN CHARGE & COUVERTURE SANTÉ
    if any(k in texte_lower for k in ["prise en charge", "pec", "taux", "couverture", "remboursement", "mutuelle", "plafond"]):
        if not patient:
            return _reponse_sans_profil_patient()

        taux = patient.taux_couverture or 0
        plan_nom = patient.titulaire.plan_couverture.nom if (patient.titulaire and patient.titulaire.plan_couverture) else "Standard"
        plafond = patient.titulaire.plan_couverture.plafond_annuel if (patient.titulaire and patient.titulaire.plan_couverture) else None
        
        texte = (
            f"🛡️ **Votre couverture SantéSN :**\n\n"
            f"- **Formule active** : {plan_nom}\n"
            f"- **Taux de prise en charge garanti** : **{taux}%** sur les actes et soins conventionnés.\n"
        )
        if plafond:
            restant = patient.plafond_annuel_restant()
            texte += f"- **Plafond annuel restant** : {restant} FCFA (sur {plafond} FCFA).\n"
        
        texte += "\nVos démarches et hospitalisations prises en charge sont suivies en temps réel dans votre espace."

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Mes prises en charge", "url": reverse("mes_prises_en_charge_assure"), "style": "primary"},
                {"libelle": "Ma carte d'assuré", "url": reverse("carte_assure"), "style": "secondary"}
            ],
            "suggestions": [
                "Qui sont mes ayants droit ?",
                "Prendre un rendez-vous",
                "Contacter l'administration"
            ]
        }

    # 6. INTENTION : CARTE D'ASSURÉ & IDENTIFIANT
    if any(k in texte_lower for k in ["carte", "matricule", "numéro de carte", "numero de carte", "mon qr"]):
        if not patient:
            return _reponse_sans_profil_patient()

        texte = (
            f"🪪 **Votre carte dématérialisée SantéSN :**\n\n"
            f"- **Numéro de carte** : `{patient.numero_carte}`\n"
            f"- **Titulaire** : {patient.prenom} {patient.nom}\n"
            f"- **Bénéficiaires couverts** : Vous et vos ayants droit rattachés.\n\n"
            "Votre carte dispose d'un QR Code officiel que vous pouvez présenter aux cliniques, hôpitaux et pharmacies."
        )

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Afficher ma carte & QR Code", "url": reverse("carte_assure"), "style": "primary"}
            ],
            "suggestions": [
                "Mes ayants droit",
                "Mon taux de couverture",
                "Prendre un rendez-vous"
            ]
        }

    # 7. INTENTION : AYANTS DROIT & FAMILLE
    if any(k in texte_lower for k in ["ayant droit", "ayants droit", "famille", "enfant", "conjoint", "bénéficiaire"]):
        if not patient:
            return _reponse_sans_profil_patient()

        ayants_droit = list(patient.ayants_droit.all())
        if ayants_droit:
            noms = [f"- **{ad.prenom} {ad.nom}** ({ad.get_lien_parente_display() or 'Bénéficiaire'}) · Carte : `{ad.numero_carte}`" for ad in ayants_droit]
            texte = (
                f"👨‍👩‍👧‍👦 **Vos ayants droit rattachés ({len(ayants_droit)}) :**\n\n"
                + "\n".join(noms)
                + "\n\nIls bénéficient automatiquement du même plan de couverture santé que vous."
            )
        else:
            texte = (
                "👨‍👩‍👧‍👦 **Vous n'avez pas encore rattaché d'ayant droit.**\n\n"
                "Vous pouvez ajouter votre conjoint(e) ou vos enfants pour qu'ils bénéficient de votre prise en charge santé."
            )

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Gérer mes ayants droit", "url": reverse("liste_ayants_droit"), "style": "primary"},
                {"libelle": "Ajouter un ayant droit", "url": reverse("ajouter_ayant_droit"), "style": "secondary"}
            ],
            "suggestions": [
                "Ma carte d'assuré",
                "Prendre un rendez-vous",
                "Mon taux de couverture"
            ]
        }

    # 8. INTENTION : CONTACTER L'ADMINISTRATION / RÉCLAMATION / SUPPORT
    if any(k in texte_lower for k in [
        "contacter", "administration", "administrateur", "réclamation", "reclamation",
        "litige", "problème", "probleme", "erreur", "plainte", "bloqué", "bloque", "support", "humain"
    ]):
        return {
            "type": "support",
            "texte": (
                "🤝 **Contacter l'Administration SantéSN :**\n\n"
                "Un problème sur votre dossier, une question administrative ou une réclamation ? "
                "Notre équipe administrative est à votre disposition pour vous répondre directement dans votre espace.\n\n"
                "Cliquez sur le bouton ci-dessous pour ouvrir une demande officielle."
            ),
            "actions": [
                {"libelle": "Ouvrir une demande d'assistance", "url": reverse("creer_demande_support"), "style": "primary"},
                {"libelle": "Voir mes demandes existantes", "url": reverse("mes_demandes_support"), "style": "secondary"}
            ],
            "suggestions": [
                "Comment prendre un rendez-vous ?",
                "Mes prises en charge",
                "Mon taux de couverture"
            ]
        }

    # 9. INTENTION : ÉTABLISSEMENTS & PRESTATAIRES PROCHES
    if any(k in texte_lower for k in ["hôpital", "hopital", "clinique", "prestataire", "proche", "où aller", "ou aller", "adresse"]):
        return {
            "type": "aide",
            "texte": (
                "📍 **Établissements & Prestataires partenaires :**\n\n"
                "SantéSN référence un réseau d'hôpitaux, cliniques et pharmacies conventionnés partout au Sénégal. "
                "Vous pouvez activer la géolocalisation pour découvrir les centres les plus proches de votre position avec itinéraires GPS."
            ),
            "actions": [
                {"libelle": "Voir les prestataires proches", "url": reverse("prestataires_proches"), "style": "primary"},
                {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "secondary"}
            ],
            "suggestions": [
                "Prendre un rendez-vous",
                "Mon ordonnance est-elle valable ?",
                "Contacter l'administration"
            ]
        }

    # 10. RÉPONSE D'ACCUEIL / ORIENTATION GÉNÉRALE
    return {
        "type": "defaut",
        "texte": (
            "👋 **Bonjour ! Je suis l'Assistant SantéSN.**\n\n"
            "Je suis là pour vous accompagner dans vos démarches de santé dématérialisées. Voici quelques exemples de ce que je peux faire pour vous :\n\n"
            "- 📅 **Rendez-vous** : Consulter vos prochains créneaux ou réserver une consultation.\n"
            "- 💊 **Ordonnances** : Vérifier vos prescriptions et leur validité en pharmacie.\n"
            "- 🛡️ **Couverture** : Connaître votre taux de prise en charge et votre plafond restant.\n"
            "- 👨‍👩‍👧‍👦 **Famille** : Suivre vos ayants droit et accéder à vos cartes de santé.\n"
            "- 🤝 **Support** : Contacter directement l'administration en cas de besoin.\n\n"
            "*Posez-moi votre question simplement ou utilisez les suggestions ci-dessous !*"
        ),
        "actions": [
            {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "primary"},
            {"libelle": "Contacter l'administration", "url": reverse("creer_demande_support"), "style": "secondary"}
        ],
        "suggestions": [
            "Quels sont mes prochains rendez-vous ?",
            "Quel est mon taux de prise en charge ?",
            "Où trouver mon ordonnance ?",
            "Qui sont mes ayants droit ?",
            "Je veux contacter l'administration"
        ]
    }


def _reponse_sans_profil_patient():
    return {
        "type": "aide",
        "texte": (
            "⚠️ Votre compte utilisateur n'est pas encore associé à un dossier patient actif. "
            "Veuillez compléter votre profil pour accéder à vos démarches."
        ),
        "actions": [
            {"libelle": "Compléter mon profil", "url": reverse("mon_profil_assure"), "style": "primary"}
        ],
        "suggestions": [
            "Contacter l'administration"
        ]
    }
