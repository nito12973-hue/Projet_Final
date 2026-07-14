from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm, SetupWizardForm
from .models import User


def _admin_exists():
    return User.objects.filter(role=User.Role.ADMIN).exists()


def login_view(request):
    """Connexion : email + mot de passe. Le rôle est détecté automatiquement."""
    if not _admin_exists():
        return redirect('accounts:setup_wizard')

    if request.user.is_authenticated:
        return redirect('accounts:post_login_redirect')

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.user)
        return redirect('accounts:post_login_redirect')

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté.')
    return redirect('accounts:login')


@login_required
def post_login_redirect(request):
    """Redirection automatique vers le dashboard correspondant au rôle."""
    role = request.user.role
    if role == User.Role.ADMIN:
        return redirect('dashboard')
    if role == User.Role.ASSURE:
        return redirect('accounts:dashboard_assure')
    if role == User.Role.MEDECIN:
        return redirect('accounts:dashboard_medecin')
    if role == User.Role.PHARMACIEN:
        return redirect('accounts:dashboard_pharmacien')
    # Rôle inconnu : sécurité avant tout, on déconnecte.
    logout(request)
    messages.error(request, "Rôle inconnu. Contactez l'administration.")
    return redirect('accounts:login')


def setup_wizard(request):
    """
    Assistant de première installation.

    Accessible uniquement si aucun administrateur n'existe.
    Crée le premier Super Administrateur puis se désactive définitivement.
    """
    if _admin_exists():
        return redirect('accounts:login')

    form = SetupWizardForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            'Bienvenue ! Votre compte Super Administrateur a été créé.',
        )
        return redirect('accounts:post_login_redirect')

    return render(request, 'accounts/setup_wizard.html', {'form': form})


# Dashboards temporaires (placeholders) — remplacés dans les phases 3 à 5.

@role_required(User.Role.ASSURE)
def dashboard_assure(request):
    return render(request, 'accounts/dashboard_placeholder.html', {
        'dashboard_title': 'Espace Assuré',
        'dashboard_message': 'Votre espace personnel sera disponible prochainement.',
    })


@role_required(User.Role.MEDECIN)
def dashboard_medecin(request):
    return render(request, 'accounts/dashboard_placeholder.html', {
        'dashboard_title': 'Espace Médecin',
        'dashboard_message': 'Votre espace de consultation sera disponible prochainement.',
    })


@role_required(User.Role.PHARMACIEN)
def dashboard_pharmacien(request):
    return render(request, 'accounts/dashboard_placeholder.html', {
        'dashboard_title': 'Espace Pharmacien',
        'dashboard_message': 'Votre espace de validation sera disponible prochainement.',
    })
