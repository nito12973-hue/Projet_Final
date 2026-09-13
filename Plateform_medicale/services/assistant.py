"""
Service métier de l'Assistant SantéSN.

Moteur d'intentions déterministe, sécurisé et rapide pour les assurés.
Interroge exclusivement les données du patient authentifié et respecte
strictement les limites déontologiques et médicales.
"""

import re
from django.urls import reverse
from django.utils import timezone
from ..models import Patient, RendezVous, Ordonnance, PriseEnCharge, User, DemandeSupport, MessageSupport, Notification


# Mots-clés de demande médicale, symptômes ou urgences cliniques
MOTS_CLES_MEDICAL = [
    "urgence", "urgences", "douleur", "malade",
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
        "type": "medical_warning" | "donnees" | "aide" | "support" | "defaut",
        "actions": [ {"libelle": str, "url": str, "style": "primary" | "secondary"} ],
        "suggestions": [str]
    }
    """
    texte_brut = (message_texte or "").strip()
    texte_lower = texte_brut.lower()

    # 2. DÉTECTION DEMANDE MÉDICALE CLINIQUE (Pas de diagnostic automatisé)
    for mot in MOTS_CLES_MEDICAL:
        if re.search(r'\b' + re.escape(mot) + r'\b', texte_lower):
            return {
                "type": "medical_warning",
                "texte": (
                    "**Rappel déontologique médical :**\n\n"
                    "En tant qu'Assistant SantéSN, **je ne suis pas habilité à poser de diagnostic ni à prescrire un traitement.** "
                    "Seul un médecin qualifié peut vous examiner et déterminer la prise en charge adaptée à votre état de santé.\n\n"
                    "Vous pouvez prendre rendez-vous en ligne avec l'un de nos médecins partenaires ou consulter les établissements conventionnés."
                ),
                "actions": [
                    {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "primary"},
                    {"libelle": "Centres et prestataires partenaires", "url": reverse("prestataires_proches"), "style": "secondary"}
                ],
                "suggestions": [
                    "Prendre un rendez-vous",
                    "Mes ordonnances en cours",
                    "Contacter l'administration"
                ]
            }

    patient = getattr(user, "patient", None)

    # 3. INTENTION : GESTION DIRECTE DU SUPPORT & DES RÉCLAMATIONS PAR L'ASSISTANT
    # 3.1. Dépôt direct d'une réclamation / problème / signalement
    match_prefix = re.match(
        r'^(?:réclamation|reclamation|plainte|signalement|ticket|problème|probleme|anomalie)\s*[:\-]?\s*(.*)$',
        texte_brut,
        re.IGNORECASE
    )
    intention_reclamation = any(k in texte_lower for k in [
        "déposer une réclamation", "deposer une reclamation",
        "faire une réclamation", "faire une reclamation",
        "je dépose une réclamation", "je depose une reclamation",
        "je souhaite déposer une réclamation", "je souhaite deposer une reclamation",
        "je souhaite faire une réclamation", "je souhaite faire une reclamation"
    ])

    est_depot_reclamation = False
    detail_msg = ""
    if match_prefix:
        contenu_apres = match_prefix.group(1).strip()
        if len(contenu_apres) >= 3:
            est_depot_reclamation = True
            detail_msg = contenu_apres
    elif intention_reclamation and len(texte_brut) > 35:
        est_depot_reclamation = True
        detail_msg = texte_brut

    if est_depot_reclamation:
        # Détection de la catégorie
        detail_lower = detail_msg.lower()
        if any(w in detail_lower for w in ["remboursement", "pec", "prise en charge", "taux", "plafond"]):
            categorie = DemandeSupport.Categorie.PRISE_EN_CHARGE
        elif any(w in detail_lower for w in ["rendez-vous", "rdv", "consultation", "médecin", "medecin"]):
            categorie = DemandeSupport.Categorie.RENDEZ_VOUS
        elif any(w in detail_lower for w in ["ordonnance", "médicament", "medicament", "pharmacie"]):
            categorie = DemandeSupport.Categorie.ORDONNANCE
        elif any(w in detail_lower for w in ["carte", "matricule", "compte"]):
            categorie = DemandeSupport.Categorie.COMPTE
        elif any(w in detail_lower for w in ["ayant droit", "famille", "enfant", "conjoint"]):
            categorie = DemandeSupport.Categorie.AYANT_DROIT
        else:
            categorie = DemandeSupport.Categorie.AUTRE

        priorite = DemandeSupport.Priorite.URGENTE if "urgent" in detail_lower else DemandeSupport.Priorite.NORMALE
        objet = detail_msg[:80] if len(detail_msg) > 5 else "Réclamation transmise via l'Assistant SantéSN"

        demande = DemandeSupport.objects.create(
            auteur=user,
            patient=patient,
            objet=objet,
            categorie=categorie,
            priorite=priorite,
            statut=DemandeSupport.Statut.EN_ATTENTE
        )
        MessageSupport.objects.create(
            demande=demande,
            auteur=user,
            message=texte_brut
        )

        # Notification en direct des administrateurs SantéSN
        admins = list(User.objects.filter(role=User.Role.ADMIN, is_active=True))
        if admins:
            nom_patient = user.get_full_name() or user.email
            Notification.objects.bulk_create([
                Notification(
                    destinataire=admin,
                    titre="Nouvelle réclamation via l'Assistant",
                    message=f"L'assuré {nom_patient} a transmis la réclamation #{demande.numero_dossier} : {demande.objet}.",
                    type_evenement=Notification.TypeEvenement.SUPPORT_DEMANDE,
                    url_action=reverse("admin_detail_demande_support", args=[demande.pk]),
                )
                for admin in admins
            ])

        texte = (
            "**Votre réclamation a été directement enregistrée et transmise à l'administration.**\n\n"
            f"- **Numéro de dossier** : `#{demande.numero_dossier}`\n"
            f"- **Catégorie** : {demande.get_categorie_display()}\n"
            f"- **Statut** : En attente de traitement administratif\n"
            f"- **Objet enregistré** : {demande.objet}\n\n"
            "Nos gestionnaires administratifs SantéSN ont été notifiés et examinent votre dossier. "
            "Vous pourrez consulter l'avancement ou les réponses à tout moment en me demandant simplement : *« Où en est ma réclamation ? »*."
        )

        return {
            "type": "support",
            "texte": texte,
            "actions": [],
            "suggestions": [
                "Suivi de mes réclamations",
                "Mon taux de couverture",
                "Prendre un rendez-vous"
            ]
        }

    # 3.2. Suivi des réclamations et demandes en cours
    mots_cles_suivi = [
        "suivi", "mes demandes", "ma demande", "mes réclamations", "mes reclamations",
        "ma réclamation", "ma reclamation", "où en est", "ou en est", "consulter ma réclamation",
        "consulter mes réclamations", "état de ma demande", "etat de ma demande",
        "état de mes réclamations", "etat de mes reclamations", "statut réclamation",
        "statut reclamation", "statut de ma réclamation", "statut de ma reclamation",
        "statut de mon ticket", "mon ticket", "mes tickets", "mes dossiers", "mon dossier"
    ]
    if any(k in texte_lower for k in mots_cles_suivi):
        demandes = DemandeSupport.objects.filter(auteur=user).select_related("patient").prefetch_related("messages").order_by("-date_creation")[:5]
        if demandes.exists():
            lignes = []
            for d in demandes:
                date_str = d.date_creation.strftime("%d/%m/%Y")
                statut_label = d.get_statut_display()
                lignes.append(f"- **#{d.numero_dossier}** : *{d.objet}* · Statut : **{statut_label}** (ouvert le {date_str})")
                
                # S'il y a un message de l'administration, afficher le dernier message
                messages_fil = list(d.messages.all())
                for m in reversed(messages_fil):
                    if m.auteur != user:
                        extrait = (m.message[:110] + '...') if len(m.message) > 110 else m.message
                        lignes.append(f"  ↳ *Réponse de l'administration :* « {extrait} »")
                        break
            
            texte = (
                "**Vos dossiers de réclamation et d'assistance :**\n\n"
                + "\n".join(lignes)
                + "\n\nPour soumettre une nouvelle réclamation, décrivez simplement votre situation directement ici."
            )
        else:
            texte = (
                "**Vous n'avez aucun dossier de réclamation ou demande d'assistance en cours.**\n\n"
                "Si vous constatez une anomalie sur vos remboursements, vos ordonnances ou vos droits, "
                "décrivez-la directement ici en commençant votre message par exemple par *« Réclamation : ... »*."
            )
        return {
            "type": "support",
            "texte": texte,
            "actions": [],
            "suggestions": [
                "Déposer une réclamation",
                "Mon taux de couverture",
                "Consulter mes ordonnances"
            ]
        }

    # 3.3. Guide de dépôt / contact support & réclamations
    mots_cles_guide_reclamation = [
        "déposer une réclamation", "deposer une reclamation",
        "faire une réclamation", "faire une reclamation",
        "je souhaite déposer une réclamation", "je souhaite deposer une reclamation",
        "comment faire une réclamation", "comment faire une reclamation",
        "comment déposer une réclamation", "comment deposer une reclamation",
        "contacter le support", "contacter l'administration", "contacter administration",
        "service client", "support administratif", "aide réclamation", "aide reclamation",
        "réclamation", "reclamation", "plainte"
    ]
    if any(k in texte_lower for k in mots_cles_guide_reclamation):
        return {
            "type": "support",
            "texte": (
                "**Service d'Assistance & Réclamations SantéSN :**\n\n"
                "Je prends directement en charge vos réclamations et signalements auprès de l'administration SantéSN, "
                "sans que vous ayez besoin de naviguer dans des formulaires externes.\n\n"
                "Pour ouvrir immédiatement un dossier, écrivez simplement votre message ici en commençant par exemple par :\n\n"
                "- *« Réclamation : erreur constatée sur mon taux de prise en charge »*\n"
                "- *« Problème : mon ordonnance n'apparaît pas en pharmacie »*\n\n"
                "Je créerai immédiatement votre ticket officiel et le transmettrai à nos équipes administratives."
            ),
            "actions": [],
            "suggestions": [
                "Suivi de mes réclamations",
                "Réclamation : anomalie sur prise en charge",
                "Réclamation : problème de carte"
            ]
        }

    # 4. INTENTION : RENDEZ-VOUS
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
                "**Vos prochains rendez-vous programmés :**\n\n"
                + "\n".join(lignes)
                + "\n\nVous pouvez consulter l'historique complet de vos consultations ou programmer un nouveau créneau ci-dessous."
            )
        else:
            texte = (
                "**Aucun rendez-vous à venir n'est planifié pour le moment.**\n\n"
                "Souhaitez-vous programmer une nouvelle consultation avec un praticien conventionné ?"
            )

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "primary"},
                {"libelle": "Consulter mes rendez-vous", "url": reverse("mes_rendez_vous_assure"), "style": "secondary"}
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
                "**Vos dernières prescriptions médicales :**\n\n"
                + "\n".join(lignes)
                + "\n\nPrésentez simplement le QR Code de votre ordonnance dans l'une des pharmacies partenaires conventionnées."
            )
        else:
            texte = (
                "**Aucune prescription médicale n'est enregistrée sur votre compte pour l'instant.**\n\n"
                "Vos ordonnances seront automatiquement disponibles ici dès qu'un praticien vous en délivrera une."
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
            "**Votre couverture santé SantéSN :**\n\n"
            f"- **Formule active** : {plan_nom}\n"
            f"- **Taux de prise en charge garanti** : **{taux}%** sur les actes et soins conventionnés.\n"
        )
        if plafond:
            restant = patient.plafond_annuel_restant()
            texte += f"- **Plafond annuel restant** : {restant} FCFA (sur {plafond} FCFA).\n"
        
        texte += "\nVos démarches et hospitalisations sont traitées en direct avec le tiers payant."

        return {
            "type": "donnees",
            "texte": texte,
            "actions": [
                {"libelle": "Mes prises en charge", "url": reverse("mes_prises_en_charge_assure"), "style": "primary"},
                {"libelle": "Ma carte d'assuré", "url": reverse("carte_assure"), "style": "secondary"}
            ],
            "suggestions": [
                "Mes ayants droit",
                "Prendre un rendez-vous",
                "Contacter l'administration"
            ]
        }

    # 6. INTENTION : CARTE D'ASSURÉ & IDENTIFIANT
    if any(k in texte_lower for k in ["carte", "matricule", "numéro de carte", "numero de carte", "mon qr"]):
        if not patient:
            return _reponse_sans_profil_patient()

        texte = (
            "**Votre carte de santé dématérialisée :**\n\n"
            f"- **Numéro de carte** : `{patient.numero_carte}`\n"
            f"- **Titulaire** : {patient.prenom} {patient.nom}\n"
            f"- **Bénéficiaires couverts** : Vous et vos ayants droit rattachés.\n\n"
            "Votre carte dispose d'un QR Code sécurisé à présenter lors de chaque visite médicale ou pharmacie."
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
                f"**Vos ayants droit rattachés ({len(ayants_droit)}) :**\n\n"
                + "\n".join(noms)
                + "\n\nIls bénéficient automatiquement du même niveau de prise en charge que votre compte principal."
            )
        else:
            texte = (
                "**Aucun ayant droit n'est rattaché à votre dossier pour le moment.**\n\n"
                "Vous pouvez déclarer votre conjoint(e) ou vos enfants pour qu'ils bénéficient de votre couverture santé."
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

    # 9. INTENTION : ÉTABLISSEMENTS & PRESTATAIRES PROCHES
    if any(k in texte_lower for k in ["hôpital", "hopital", "clinique", "prestataire", "proche", "où aller", "ou aller", "adresse"]):
        return {
            "type": "aide",
            "texte": (
                "**Réseau d'établissements et prestataires conventionnés :**\n\n"
                "SantéSN collabore avec un réseau hospitalier, de cliniques et de pharmacies agréées au Sénégal. "
                "Vous pouvez localiser les établissements à proximité de votre position et consulter leurs coordonnées."
            ),
            "actions": [
                {"libelle": "Centres et prestataires partenaires", "url": reverse("prestataires_proches"), "style": "primary"},
                {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "secondary"}
            ],
            "suggestions": [
                "Prendre un rendez-vous",
                "Mes ordonnances",
                "Déposer une réclamation"
            ]
        }

    # 10. RÉPONSE D'ACCUEIL / ORIENTATION GÉNÉRALE
    return {
        "type": "defaut",
        "texte": (
            "**Bonjour. Je suis l'Assistant SantéSN.**\n\n"
            "Je suis à votre disposition pour vous orienter et répondre à vos questions sur vos prestations de santé :\n\n"
            "- **Rendez-vous médicaux** : Vos consultations à venir ou réservation en ligne.\n"
            "- **Prescriptions & Pharmacie** : Suivi de vos ordonnances et délivrances.\n"
            "- **Prise en charge & Plafonds** : Consultation de vos droits et garanties.\n"
            "- **Couverture familiale** : Gestion de vos ayants droit rattachés.\n"
            "- **Assistance & Réclamations** : Dépôt et suivi direct de vos réclamations.\n\n"
            "Que souhaitez-vous consulter aujourd'hui ?"
        ),
        "actions": [
            {"libelle": "Prendre un rendez-vous", "url": reverse("ajouter_rendez_vous_assure"), "style": "primary"}
        ],
        "suggestions": [
            "Quels sont mes prochains rendez-vous ?",
            "Quel est mon taux de prise en charge ?",
            "Consulter mes ordonnances",
            "Déposer une réclamation",
            "Suivi de mes réclamations"
        ]
    }


def _reponse_sans_profil_patient():
    return {
        "type": "aide",
        "texte": (
            "Votre compte utilisateur n'est pas encore associé à un dossier d'assuré actif. "
            "Veuillez compléter vos informations de profil afin d'accéder à l'ensemble des services."
        ),
        "actions": [
            {"libelle": "Compléter mon profil", "url": reverse("mon_profil_assure"), "style": "primary"}
        ],
        "suggestions": [
            "Déposer une réclamation"
        ]
    }
