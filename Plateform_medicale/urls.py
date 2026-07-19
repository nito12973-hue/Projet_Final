from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('tableau-de-bord/', views.dashboard, name='dashboard'),
    path('rapports/', views.rapports, name='rapports'),
    path('rapports/exporter/excel/', views.exporter_rapports_excel, name='exporter_rapports_excel'),
    path('rapports/exporter/pdf/', views.exporter_rapports_pdf, name='exporter_rapports_pdf'),

    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('redirection/', views.post_login_redirect, name='post_login_redirect'),
    path('installation/', views.setup_wizard, name='setup_wizard'),
    path('mon-compte/mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),

    path('espace/assure/', views.dashboard_assure, name='dashboard_assure'),
    path('espace/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
    path('espace/pharmacien/', views.dashboard_pharmacien, name='dashboard_pharmacien'),

    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/exporter/', views.exporter_utilisateurs_excel, name='exporter_utilisateurs_excel'),
    path('utilisateurs/ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    path('utilisateurs/<int:pk>/modifier/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/<int:pk>/activer-desactiver/', views.activer_desactiver_utilisateur, name='activer_desactiver_utilisateur'),
    path('utilisateurs/<int:pk>/reinitialiser-mot-de-passe/', views.reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),
    path('utilisateurs/<int:pk>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'),

    path('patients/', views.liste_patients, name='liste_patients'),
    path('patients/ajouter/', views.ajouter_patient, name='ajouter_patient'),
    path('patients/<int:pk>/modifier/', views.modifier_patient, name='modifier_patient'),
    path('patients/<int:pk>/supprimer/', views.supprimer_patient, name='supprimer_patient'),

    path('medecins/', views.liste_medecins, name='liste_medecins'),
    path('medecins/ajouter/', views.ajouter_medecin, name='ajouter_medecin'),
    path('medecins/<int:pk>/modifier/', views.modifier_medecin, name='modifier_medecin'),
    path('medecins/<int:pk>/supprimer/', views.supprimer_medecin, name='supprimer_medecin'),

    path('pharmaciens/', views.liste_pharmaciens, name='liste_pharmaciens'),
    path('pharmaciens/<int:pk>/modifier/', views.modifier_pharmacien, name='modifier_pharmacien'),

    path('services/', views.liste_services, name='liste_services'),
    path('services/ajouter/', views.ajouter_service, name='ajouter_service'),
    path('services/<int:pk>/modifier/', views.modifier_service, name='modifier_service'),
    path('services/<int:pk>/supprimer/', views.supprimer_service, name='supprimer_service'),

    path('prises-en-charge/', views.liste_prises_en_charge, name='liste_prises_en_charge'),
    path('prises-en-charge/ajouter/', views.ajouter_prise_en_charge, name='ajouter_prise_en_charge'),
    path('prises-en-charge/<int:pk>/modifier/', views.modifier_prise_en_charge, name='modifier_prise_en_charge'),
    path('prises-en-charge/<int:pk>/supprimer/', views.supprimer_prise_en_charge, name='supprimer_prise_en_charge'),

    path('paiements/', views.liste_paiements, name='liste_paiements'),
    path('paiements/<int:pk>/regler/', views.marquer_paiement_regle, name='marquer_paiement_regle'),

    path('prestataires/', views.liste_prestataires, name='liste_prestataires'),
    path('prestataires/ajouter/', views.ajouter_prestataire, name='ajouter_prestataire'),
    path('prestataires/<int:pk>/modifier/', views.modifier_prestataire, name='modifier_prestataire'),
    path('prestataires/<int:pk>/supprimer/', views.supprimer_prestataire, name='supprimer_prestataire'),

    path('plans-de-couverture/', views.liste_plans_couverture, name='liste_plans_couverture'),
    path('plans-de-couverture/ajouter/', views.ajouter_plan_couverture, name='ajouter_plan_couverture'),
    path('plans-de-couverture/<int:pk>/modifier/', views.modifier_plan_couverture, name='modifier_plan_couverture'),
    path('plans-de-couverture/<int:pk>/supprimer/', views.supprimer_plan_couverture, name='supprimer_plan_couverture'),

    path('medecin/agenda/', views.agenda_medecin, name='agenda_medecin'),
    path('medecin/rendez-vous/ajouter/', views.ajouter_rendez_vous, name='ajouter_rendez_vous'),
    path('medecin/rendez-vous/<int:pk>/statut/', views.changer_statut_rendez_vous, name='changer_statut_rendez_vous'),
    path('medecin/patients/', views.mes_patients, name='mes_patients'),
    path('medecin/consultations/', views.historique_consultations, name='historique_consultations'),
    path('medecin/consultations/ajouter/', views.ajouter_consultation_medecin, name='ajouter_consultation_medecin'),
    path('medecin/consultations/<int:consultation_pk>/ordonnance/ajouter/', views.ajouter_ordonnance_medecin, name='ajouter_ordonnance_medecin'),
    path('medecin/ordonnances/<int:pk>/', views.voir_ordonnance_medecin, name='voir_ordonnance_medecin'),
    path('medecin/profil/', views.modifier_profil_medecin, name='modifier_profil_medecin'),

    path('pharmacien/scanner/', views.scanner_ordonnance, name='scanner_ordonnance'),
    path('pharmacien/ordonnances/<int:pk>/delivrer/', views.valider_delivrance, name='valider_delivrance'),
    path('pharmacien/historique/', views.historique_delivrances, name='historique_delivrances'),

    path('assure/profil/', views.mon_profil_assure, name='mon_profil_assure'),
    path('assure/ayants-droit/', views.liste_ayants_droit, name='liste_ayants_droit'),
    path('assure/ayants-droit/ajouter/', views.ajouter_ayant_droit, name='ajouter_ayant_droit'),
    path('assure/ayants-droit/<int:pk>/modifier/', views.modifier_ayant_droit, name='modifier_ayant_droit'),
    path('assure/ayants-droit/<int:pk>/supprimer/', views.supprimer_ayant_droit, name='supprimer_ayant_droit'),
    path('assure/rendez-vous/', views.mes_rendez_vous_assure, name='mes_rendez_vous_assure'),
    path('assure/rendez-vous/ajouter/', views.ajouter_rendez_vous_assure, name='ajouter_rendez_vous_assure'),
    path('assure/rendez-vous/<int:pk>/annuler/', views.annuler_rendez_vous_assure, name='annuler_rendez_vous_assure'),
    path('assure/ordonnances/', views.mes_ordonnances_assure, name='mes_ordonnances_assure'),
    path('assure/ordonnances/<int:pk>/', views.voir_ordonnance_assure, name='voir_ordonnance_assure'),
    path('assure/historique/', views.mon_historique_assure, name='mon_historique_assure'),

    path('notifications/envoyer/', views.envoyer_notification, name='envoyer_notification'),
    path('notifications/envoyees/', views.liste_notifications_envoyees, name='liste_notifications_envoyees'),
    path('notifications/', views.mes_notifications, name='mes_notifications'),
    path('notifications/<int:pk>/lue/', views.marquer_notification_lue, name='marquer_notification_lue'),
]
