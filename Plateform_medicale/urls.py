from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('patients/', views.liste_patients, name='liste_patients'),
    path('patients/ajouter/', views.ajouter_patient, name='ajouter_patient'),
    path('patients/<int:pk>/modifier/', views.modifier_patient, name='modifier_patient'),
    path('patients/<int:pk>/supprimer/', views.supprimer_patient, name='supprimer_patient'),

    path('medecins/', views.liste_medecins, name='liste_medecins'),
    path('medecins/ajouter/', views.ajouter_medecin, name='ajouter_medecin'),
    path('medecins/<int:pk>/modifier/', views.modifier_medecin, name='modifier_medecin'),
    path('medecins/<int:pk>/supprimer/', views.supprimer_medecin, name='supprimer_medecin'),
    
    path('services/', views.liste_services, name='liste_services'),
    path('services/ajouter/', views.ajouter_service, name='ajouter_service'),
    path('services/<int:pk>/modifier/', views.modifier_service, name='modifier_service'),
    path('services/<int:pk>/supprimer/', views.supprimer_service, name='supprimer_service'),

    path('prises-en-charge/', views.liste_prises_en_charge, name='liste_prises_en_charge'),
    path('prises-en-charge/ajouter/', views.ajouter_prise_en_charge, name='ajouter_prise_en_charge'),
    path('prises-en-charge/<int:pk>/modifier/', views.modifier_prise_en_charge, name='modifier_prise_en_charge'),
    path('prises-en-charge/<int:pk>/supprimer/', views.supprimer_prise_en_charge, name='supprimer_prise_en_charge'),

    path('consultations/', views.liste_consultations, name='liste_consultations'),
    path('consultations/ajouter/', views.ajouter_consultation, name='ajouter_consultation'),
    path('consultations/<int:pk>/modifier/', views.modifier_consultation, name='modifier_consultation'),
    path('consultations/<int:pk>/supprimer/', views.supprimer_consultation, name='supprimer_consultation'),
    
    path('ordonnances/', views.liste_ordonnances, name='liste_ordonnances'),
    path('ordonnances/ajouter/', views.ajouter_ordonnances, name='ajouter_ordonnances'),
    path('ordonnances/<int:pk>/modifier/', views.modifier_ordonnances, name='modifier_ordonnances'),
    path('ordonnances/<int:pk>/supprimer/', views.supprimer_ordonnances, name='supprimer_ordonnances'),
]