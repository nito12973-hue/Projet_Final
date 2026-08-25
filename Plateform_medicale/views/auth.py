"""
Vues d'authentification et de gestion du compte utilisateur.

Contient : login, logout, redirection post-connexion, assistant d'installation,
mon compte, changement de mot de passe, déconnexion partout, paramètres,
comptes bloqués et déblocage.
"""

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sessions.models import Session
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from django.contrib import messages

from ..forms import (
    LoginForm,
    MonCompteForm,
    PreferenceNotificationForm,
    SetupWizardForm,
)
from ..models import (
    JournalActivite,
    PreferenceNotification,
    TentativeConnexion,
    User,
)
from .utils import admin_required, journaliser, role_required


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

def _admin_exists():
    return User.objects.filter(role=User.Role.ADMIN).exists()


def login_view(request):
    """Connexion par email et mot de passe. Le role est detecte en base."""
    if not _admin_exists():
        return redirect('setup_wizard')

    # 'next' est pose par @login_required quand une page protegee redirige
    # ici (session expiree, ou lien direct sans etre connecte). Valide avant
    # de s'en servir comme cible (empeche un lien ?next=https://... trafique
    # de rediriger hors du site) ; sa seule presence sert aussi a expliquer
    # explicitement la redirection sur l'ecran de connexion plutot que de
    # rester muet (le formulaire n'a pas d'action explicite, la query string
    # de la page suit donc telle quelle jusqu'au POST).
    next_url = request.GET.get('next', '')
    next_valide = bool(next_url) and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )
    destination = 'post_login_redirect'
    if next_valide:
        # Seul un ADMIN peut être renvoyé vers le tableau de bord ou les rapports d'administration
        admin_only_prefixes = ('/tableau-de-bord', '/rapports', '/parametres', '/utilisateurs', '/plans-couverture')
        if any(next_url.startswith(p) for p in admin_only_prefixes):
            if request.user.is_authenticated and request.user.role == User.Role.ADMIN:
                destination = next_url
        else:
            destination = next_url

    if request.user.is_authenticated:
        return redirect('post_login_redirect')

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.user)
        if next_valide:
            admin_only_prefixes = ('/tableau-de-bord', '/rapports', '/parametres', '/utilisateurs', '/plans-couverture')
            if any(next_url.startswith(p) for p in admin_only_prefixes) and form.user.role != User.Role.ADMIN:
                return redirect('post_login_redirect')
            return redirect(next_url)
        return redirect('post_login_redirect')

    return render(request, 'login.html', {'form': form, 'session_expiree': next_valide})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté.')
    return redirect('login')


@login_required
def post_login_redirect(request):
    """Redirection automatique vers le dashboard correspondant au role."""
    role = request.user.role
    if role == User.Role.ADMIN:
        return redirect('dashboard')
    if role == User.Role.ASSURE:
        return redirect('dashboard_assure')
    if role == User.Role.MEDECIN:
        return redirect('dashboard_medecin')
    if role == User.Role.PHARMACIEN:
        return redirect('dashboard_pharmacien')

    logout(request)
    messages.error(request, "Rôle inconnu. Contactez l'administration.")
    return redirect('login')


def setup_wizard(request):
    """
    Assistant de premiere installation.

    Accessible uniquement si aucun administrateur n'existe. Une fois le premier
    administrateur cree, l'assistant redirige toujours vers la connexion.
    """
    if _admin_exists():
        return redirect('login')

    form = SetupWizardForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            'Bienvenue ! Votre compte Super Administrateur a été créé.',
        )
        return redirect('post_login_redirect')

    return render(request, 'setup_wizard.html', {'form': form})


# ---------------------------------------------------------------------------
# Mon compte & sécurité
# ---------------------------------------------------------------------------

@login_required
def mon_compte(request):
    """Modification par l'utilisateur de ses propres informations.

    Ne permet pas de changer son role (regle metier : le role est stocke en
    base, jamais choisi par l'utilisateur). Changer l'email exige le mot de
    passe actuel, cf. MonCompteForm.
    """
    form = MonCompteForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        ancien_email = request.user.email
        form.save()
        if form.cleaned_data["email"].lower() != ancien_email.lower():
            messages.success(
                request,
                "Informations enregistrées. Votre adresse de connexion est "
                f"désormais {form.cleaned_data['email']}.",
            )
        else:
            messages.success(request, "Informations enregistrées.")
        return redirect("mon_compte")

    return render(request, "mon_compte.html", {"form": form})


@login_required
def changer_mot_de_passe(request):
    """
    Changement du mot de passe par l'utilisateur connecte (tous roles).

    Distinct de la reinitialisation par l'admin (Gestion des utilisateurs) :
    ici, l'utilisateur doit connaitre son mot de passe actuel.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Mot de passe modifié avec succès.')
            return redirect('post_login_redirect')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'changer_mot_de_passe.html', {'form': form})


@login_required
@require_POST
def deconnecter_partout(request):
    """Ferme toutes les sessions de l'utilisateur, y compris la courante.

    Django n'offre pas de primitive pour cela sans changer le mot de passe :
    on parcourt les sessions NON EXPIREES et on supprime celles dont
    _auth_user_id correspond. Suppose le backend de sessions en base (celui par
    defaut ; ce projet n'en change pas). Le filtre sur expire_date evite de
    decoder des sessions deja mortes.

    Le message est pose APRES logout() : logout() vide la session courante, un
    message ajoute avant serait perdu.
    """
    identifiant = str(request.user.pk)
    fermees = 0
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        if session.get_decoded().get("_auth_user_id") == identifiant:
            session.delete()
            fermees += 1

    logout(request)
    messages.success(
        request,
        f"{fermees} session(s) fermée(s). Reconnectez-vous pour continuer.",
    )
    return redirect("login")


# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------

# Sections de la page Parametres : (slug, libelle, icone, role requis).
# Une seule table pilote a la fois le menu de gauche ET le controle d'acces,
# pour qu'ils ne puissent pas diverger.
# (slug, libelle, icone, role_requis). role_requis=None : ouverte a tous.
#
# La section "Données" a ete SUPPRIMEE : ses six entrees (2 imports, 3 exports)
# etaient toutes des actions metier deja presentes sur leur propre page. Un
# import d'utilisateurs se fait depuis Utilisateurs, un import de reglements
# depuis Paiements -- c'est la que l'administrateur les cherche. Pire, les
# exports proposes ici ignoraient les filtres alors que le sous-titre affirmait
# le contraire. Videe de ses doublons, la section n'avait plus de contenu.
#
# La section "Avancé" a ete FUSIONNEE dans "Général" : depuis que la carte
# "Mon compte" a rejoint le menu du compte, General ne portait plus qu'un seul
# panneau de trois valeurs et laissait un grand vide sous lui, tandis
# qu'"Avancé" ne portait qu'un panneau lui aussi. Les deux disent la meme
# chose -- ce que la plateforme est et ce dont elle depend, en lecture seule.
# Une section de plus pour un seul panneau n'ajoutait qu'un clic.
#
# L'icone de "Général" n'est plus user-circle : cette section ne porte plus le
# compte de l'utilisateur.
SECTIONS_PARAMETRES = [
    ("general", "Général", "settings", None),
    ("apparence", "Apparence", "eye", None),
    ("securite", "Sécurité", "lock", None),
    ("notifications", "Notifications", "bell", None),
]


@login_required
def parametres(request, section="general"):
    """Page Parametres, decoupee en sections qui ont chacune leur URL.

    Un clic dans le menu de gauche ouvre reellement la page correspondante
    (et non un simple defilement) : l'adresse est partageable, le bouton
    Retour du navigateur fonctionne, et chaque ecran reste court.

    Regle de contenu inchangee : la page n'affiche QUE des reglages adosses a
    du code reel. La section "general" montre la configuration de la
    plateforme en LECTURE SEULE (langue, fuseau, format de date) : ce sont de
    vraies valeurs, lues dans settings.py, qui repondent a une question
    legitime -- les presenter comme modifiables serait un mensonge, les
    cacher priverait l'administrateur d'une information utile.
    """
    from Plateform_medicale import views
    sections_reg = getattr(views, "SECTIONS_PARAMETRES", SECTIONS_PARAMETRES)
    autorisees = [s for s in sections_reg
                  if s[3] is None or request.user.role == s[3]]
    slugs = {s[0] for s in autorisees}
    if section not in slugs:
        raise Http404("Section de paramètres inconnue.")

    contexte = {
        "sections": [
            {"slug": slug, "libelle": libelle, "icone": icone}
            for slug, libelle, icone, _ in autorisees
        ],
        "section": section,
        "section_libelle": next(s[1] for s in autorisees if s[0] == section),
    }

    if section == "general":
        contexte.update({
            "langue_plateforme": "Français",
            "fuseau_horaire": settings.TIME_ZONE,
        })
    elif section == "apparence":
        pass
    elif section == "notifications":
        prefs, _ = PreferenceNotification.objects.get_or_create(user=request.user)
        if request.method == "POST":
            pref_form = PreferenceNotificationForm(request.POST, instance=prefs)
            if pref_form.is_valid():
                pref_form.save()
                messages.success(request, "Préférences de notifications mises à jour.", extra_tags="succes-critique")
                return redirect("parametres_section", section="notifications")
            else:
                contexte["pref_form"] = pref_form
        else:
            contexte["pref_form"] = PreferenceNotificationForm(instance=prefs)
    elif section == "securite":
        contexte["duree_session_heures"] = settings.SESSION_COOKIE_AGE // 3600
        if request.user.role == User.Role.ADMIN:
            contexte["total_journal"] = JournalActivite.objects.count()
            comptes, role_choisi, recherche = _comptes_bloques(request)
            contexte.update({
                "comptes_bloques": comptes,
                "role_choisi": role_choisi,
                "recherche_bloques": recherche,
                "roles_disponibles": User.Role.choices,
                "minutes_blocage": int(TentativeConnexion.DUREE_BLOCAGE.total_seconds() // 60),
                "max_tentatives": TentativeConnexion.MAX_TENTATIVES,
            })

    return render(request, "parametres.html", contexte)


def _comptes_bloques(request):
    """Comptes reellement bloques, filtres par role et par recherche.

    Renvoie (liste, role_choisi, recherche). Chaque element est un dict pret
    a afficher : on ne passe au gabarit que ce qui est necessaire a l'ecran
    (identite, role, echecs, temps restant) -- rien d'authentification.
    """
    role_choisi = request.GET.get("role", "")
    recherche = request.GET.get("q", "").strip()
    maintenant = timezone.now()

    comptes = []
    for utilisateur, ligne in TentativeConnexion.comptes_bloques():
        if role_choisi and utilisateur.role != role_choisi:
            continue
        if recherche:
            cible = f"{utilisateur.first_name} {utilisateur.last_name} {utilisateur.email}".lower()
            if recherche.lower() not in cible:
                continue
        restant = ligne.secondes_restantes(maintenant)
        comptes.append({
            "utilisateur": utilisateur,
            "tentatives": ligne.tentatives,
            "minutes_restantes": max(1, -(-restant // 60)),  # arrondi au superieur
        })
    comptes.sort(key=lambda c: c["minutes_restantes"], reverse=True)
    return comptes, role_choisi, recherche


@admin_required
@require_POST
def debloquer_compte(request, pk):
    """Deblocage manuel par un administrateur.

    Supprime la ligne de comptage, ce qui est exactement ce que fait une
    connexion reussie : le compte peut se reconnecter immediatement. Le
    deblocage automatique par expiration continue de fonctionner en parallele
    -- il ne depend que de dernier_echec.

    Deblocage INDIVIDUEL uniquement : pas de "tout debloquer". Un blocage
    massif est souvent le signe d'une attaque en cours ; tout relacher d'un
    clic annulerait la protection au pire moment.
    """
    utilisateur = get_object_or_404(User, pk=pk)
    supprimees = TentativeConnexion.objects.filter(email=utilisateur.email.lower()).delete()[0]
    if supprimees:
        journaliser(request, JournalActivite.Action.DEBLOCAGE, f"Utilisateur {utilisateur.email}")
        messages.success(
            request,
            f"Le compte de {utilisateur} peut de nouveau se connecter.",
            extra_tags="succes-critique",
        )
    else:
        # Expiration survenue entre l'affichage et le clic : ce n'est pas une
        # erreur, le resultat voulu est deja atteint.
        messages.info(request, f"Le compte de {utilisateur} n'était plus bloqué.")
    return redirect(f"{reverse('parametres_section', args=['securite'])}#comptes-bloques")


def activer_compte(request, uidb64, token):
    """
    Activation de compte par jeton sécurisé à usage unique (Onboarding).
    Permet à l'utilisateur de choisir son propre mot de passe.
    """
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from ..forms import ActivationCompteForm

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        utilisateur = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        utilisateur = None

    if utilisateur is None or not default_token_generator.check_token(utilisateur, token):
        return render(request, "activer_compte_invalide.html")

    if request.method == "POST":
        form = ActivationCompteForm(utilisateur, request.POST)
        if form.is_valid():
            utilisateur = form.sauvegarder()
            journaliser(
                request,
                JournalActivite.Action.ACTIVATION,
                f"Utilisateur {utilisateur.email}",
                "Activation initiale via lien sécurisé",
            )
            # Déconnecter toute session précédente (ex: admin en cours de test)
            logout(request)
            # Connecter automatiquement le nouvel utilisateur activé
            login(request, utilisateur)
            messages.success(
                request,
                f"Bienvenue {utilisateur.first_name or ''} ! Votre compte est activé avec succès.",
            )
            return redirect("post_login_redirect")
    else:
        form = ActivationCompteForm(utilisateur)

    return render(
        request,
        "activer_compte.html",
        {"form": form, "utilisateur": utilisateur},
    )
