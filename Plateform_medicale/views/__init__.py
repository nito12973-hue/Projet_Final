"""
Package views de SantéSN.

Ce package découpe le monolithe views.py original en modules thématiques.
Le présent __init__.py réexporte TOUT ce que urls.py référence, pour que
aucun fichier extérieur n'ait besoin d'être modifié.

Architecture des modules :
  utils.py          — constantes, pagination, tri, journalisation, permissions
  auth.py           — login, logout, setup_wizard, compte, paramètres
  public.py         — landing, robots_txt, sitemap_xml
  dashboard.py      — dashboard admin, rapports, exports Excel/PDF
  patients.py       — CRUD patients, carte_patient, carte_scan
  medecins.py       — CRUD médecins
  pharmaciens.py    — CRUD pharmaciens
  services.py       — CRUD services médicaux
  prises_en_charge.py — CRUD prises en charge
  paiements.py      — CRUD paiements, exports CSV, import règlements
  prestataires.py   — CRUD prestataires, Nominatim, plans couverture
  utilisateurs.py   — CRUD utilisateurs, import/export Excel/CSV
  rendez_vous.py    — liste rendez-vous (admin)
  consultations.py  — liste consultations (admin), journal activité
  ordonnances.py    — liste ordonnances (admin)
  medecin_espace.py — espace médecin (dashboard, agenda, consultations…)
  pharmacien_espace.py — espace pharmacien (scanner, délivrances…)
  assure_espace.py  — espace assuré (profil, RDV, ordonnances…)
  notifications.py  — envoi et lecture des notifications
"""
import urllib.request  # noqa: F401

# Utilitaires et décorateurs (nécessaires à tous les modules)
from .utils import (  # noqa: F401
    TAILLE_PAGE_LISTE,
    RECHERCHE_ORDONNANCE_MIN,
    RECHERCHE_ORDONNANCE_MAX,
    MOIS_ABREGES,
    _paginer,
    _trier,
    journaliser,
    _filtrer_rendez_vous,
    _avertissement_cascade,
    _cellule_csv,
    role_required,
    admin_required,
    compteurs_files_attente,
    user_role,
)

# Authentification et compte
from .auth import (  # noqa: F401
    _admin_exists,
    login_view,
    logout_view,
    post_login_redirect,
    setup_wizard,
    mon_compte,
    changer_mot_de_passe,
    deconnecter_partout,
    SECTIONS_PARAMETRES,
    parametres,
    _comptes_bloques,
    debloquer_compte,
    activer_compte,
)

# Pages publiques
from .public import (  # noqa: F401
    landing,
    robots_txt,
    sitemap_xml,
)

# Dashboard et rapports administrateur
from .dashboard import (  # noqa: F401
    _consultations_par_mois,
    _consultations_par_jour,
    _montants_regles_par_jour,
    _consultations_par_annee,
    _donnees_rapports,
    dashboard,
    rapports,
    exporter_rapports_excel,
    exporter_rapports_pdf,
)

# Patients
from .patients import (  # noqa: F401
    liste_patients,
    ajouter_patient,
    modifier_patient,
    supprimer_patient,
    carte_patient,
    carte_scan,
)

# Médecins
from .medecins import (  # noqa: F401
    liste_medecins,
    ajouter_medecin,
    modifier_medecin,
    supprimer_medecin,
)

# Pharmaciens
from .pharmaciens import (  # noqa: F401
    liste_pharmaciens,
    modifier_pharmacien,
)

# Services médicaux
from .services import (  # noqa: F401
    liste_services,
    ajouter_service,
    modifier_service,
    supprimer_service,
)

# Prises en charge
from .prises_en_charge import (  # noqa: F401
    liste_prises_en_charge,
    ajouter_prise_en_charge,
    modifier_prise_en_charge,
    supprimer_prise_en_charge,
)

# Paiements
from .paiements import (  # noqa: F401
    _filtrer_paiements,
    liste_paiements,
    exporter_paiements_csv,
    marquer_paiement_regle,
    recu_paiement,
)


# Prestataires et plans de couverture
from .prestataires import (  # noqa: F401
    liste_prestataires,
    ajouter_prestataire,
    modifier_prestataire,
    supprimer_prestataire,
    _appeler_nominatim,
    _resultat_osm,
    recherche_lieu_prestataire,
    liste_plans_couverture,
    ajouter_plan_couverture,
    modifier_plan_couverture,
    supprimer_plan_couverture,
)

# Gestion des utilisateurs
from .utilisateurs import (  # noqa: F401
    _filtrer_utilisateurs,
    liste_utilisateurs,
    exporter_utilisateurs_excel,
    exporter_utilisateurs_csv,
    COLONNES_IMPORT_UTILISATEURS,
    _normaliser_texte_import,
    _ROLES_PAR_LIBELLE_IMPORT,
    _analyser_ligne_import_utilisateurs,
    _creer_comptes_import_utilisateurs,
    importer_utilisateurs_excel,
    telecharger_modele_import_utilisateurs,
    ajouter_utilisateur,
    modifier_utilisateur,
    activer_desactiver_utilisateur,
    reinitialiser_mot_de_passe,
    renvoyer_activation,
    supprimer_utilisateur,
)

# Listes administrateur et rendez-vous
from .rendez_vous import (  # noqa: F401
    liste_rendez_vous,
    telecharger_ics_rendez_vous,
)


from .consultations import (  # noqa: F401
    liste_consultations,
    journal_activite,
)

from .ordonnances import (  # noqa: F401
    liste_ordonnances,
)

# Espace médecin
from .medecin_espace import (  # noqa: F401
    _medecin_courant,
    _patients_du_medecin,
    dashboard_medecin,
    agenda_medecin,
    changer_statut_rendez_vous,
    mes_patients,
    rechercher_patients_medecin,
    fiche_patient_medecin,
    historique_consultations,
    ajouter_consultation_medecin,
    ajouter_ordonnance_medecin,
    _contexte_ordonnance,
    voir_ordonnance_medecin,
    annuler_ordonnance_medecin,
    modifier_profil_medecin,
)

# Espace pharmacien
from .pharmacien_espace import (  # noqa: F401
    _pharmacien_courant,
    dashboard_pharmacien,
    scanner_ordonnance,
    valider_delivrance,
    historique_delivrances,
)

# Espace assuré
from .assure_espace import (  # noqa: F401
    _patient_principal,
    _beneficiaires,
    prestataires_proches,
    fiche_prestataire_assure,
    fiche_medecin_assure,
    dashboard_assure,
    mon_profil_assure,
    liste_ayants_droit,
    ajouter_ayant_droit,
    modifier_ayant_droit,
    supprimer_ayant_droit,
    mes_rendez_vous_assure,
    ajouter_rendez_vous_assure,
    annuler_rendez_vous_assure,
    mes_ordonnances_assure,
    voir_ordonnance_assure,
    mes_prises_en_charge_assure,
    mon_historique_assure,
    carte_assure,
)

# Notifications
from .notifications import (  # noqa: F401
    envoyer_notification,
    liste_notifications_envoyees,
    mes_notifications,
    marquer_notification_lue,
    marquer_toutes_notifications_lues,
    api_dernieres_notifications,
)
