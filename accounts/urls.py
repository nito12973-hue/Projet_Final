from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('redirection/', views.post_login_redirect, name='post_login_redirect'),
    path('installation/', views.setup_wizard, name='setup_wizard'),

    path('espace/assure/', views.dashboard_assure, name='dashboard_assure'),
    path('espace/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
    path('espace/pharmacien/', views.dashboard_pharmacien, name='dashboard_pharmacien'),
]
