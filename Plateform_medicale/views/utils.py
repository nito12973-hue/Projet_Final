"""
Utilitaires partagés entre toutes les vues de SantéSN.

Ce module regroupe les constantes de pagination, les fonctions de tri/pagination
sécurisées, le journaliseur d'activité et le filtre rendez-vous commun.
Aucune vue Django ici : ce module ne dépend que de Django ORM et des modèles.
"""

import datetime
import logging
import unicodedata
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger("Plateform_medicale")

from django.shortcuts import get_object_or_404

from ..models import (
    DemandeRemboursement,
    DemandeSupport,
    JournalActivite,
    Paiement,
    Patient,
    PriseEnCharge,
    RendezVous,
    User,
)

# ---------------------------------------------------------------------------
# Pagination des listes admin
# ---------------------------------------------------------------------------

TAILLE_PAGE_LISTE = 20

# Recherche de repli du pharmacien (scanner_ordonnance) : longueur minimale
# pour ne pas énumérer les patients, et plafond d'affichage au comptoir.
RECHERCHE_ORDONNANCE_MIN = 3
RECHERCHE_ORDONNANCE_MAX = 20

MOIS_ABREGES = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"]


def _paginer(request, queryset):
    """Pagine un queryset pour une liste admin (parametre GET 'page', taille
    fixe). get_page() plutot que page() : replie silencieusement sur la
    derniere/premiere page si le numero demande est hors limites, plutot que
    de lever une exception pour un lien de pagination perime ou trafique."""
    paginateur = Paginator(queryset, TAILLE_PAGE_LISTE)
    return paginateur.get_page(request.GET.get("page"))


def _trier(request, queryset, champs_autorises, defaut):
    """Trie un queryset de liste admin depuis le parametre GET 'tri' (ex.
    'nom' ou '-nom'), restreint a `champs_autorises` (sans le signe -) pour
    ne jamais passer un champ arbitraire a order_by(). Retombe sur `defaut`
    (nom de champ ou tuple/liste de noms) si absent ou hors liste."""
    tri = request.GET.get("tri", "")
    if tri.lstrip("-") in champs_autorises:
        return queryset.order_by(tri)
    if isinstance(defaut, (list, tuple)):
        return queryset.order_by(*defaut)
    return queryset.order_by(defaut)


def journaliser(request, action, objet, details="", organisme=None):
    """Enregistre une entree du journal d'activite.

    A appeler APRES que l'action a reussi, jamais avant : une entree qui
    decrit une action qui a echoue serait pire que pas d'entree du tout.

    L'auteur et l'organisme sont figes en texte en meme temps qu'ils sont
    references : supprimer le compte ou l'organisme ne doit pas effacer la
    trace de ce qui a ete fait (la cle passe a NULL, le libelle reste).
    """
    utilisateur = request.user if request.user.is_authenticated else None
    org = organisme
    if org is None and utilisateur is not None and getattr(utilisateur, "organisme_id", None):
        org = utilisateur.organisme
    JournalActivite.objects.create(
        auteur=utilisateur,
        auteur_libelle=(
            (utilisateur.get_full_name() or utilisateur.email)[:254]
            if utilisateur else "—"
        ),
        organisme=org,
        organisme_libelle=str(org)[:200] if org else "",
        action=action,
        objet=objet[:200],
        details=details[:300],
    )


def _filtrer_rendez_vous(request, rendez_vous):
    """Filtres 'statut' et 'periode', partages par l'agenda du medecin et les
    rendez-vous de l'assure : les deux ecrans posent la meme question.

    Le tri suit la periode. Un agenda melange passe et futur ; en tri unique
    "-date_heure", demander "a venir" affichait le rendez-vous le plus LOINTAIN
    en tete, alors que c'est le prochain qu'on vient consulter. Le statut est
    valide contre RendezVous.Statut.values (la VALEUR stockee, jamais le
    libelle) pour ne jamais passer une chaine arbitraire a filter().

    Renvoie (queryset, statut_retenu, periode_retenue) : une valeur hors liste
    est ramenee a "" pour que le formulaire ne reaffiche pas un choix ignore.
    """
    statut = request.GET.get("statut", "")
    if statut in RendezVous.Statut.values:
        rendez_vous = rendez_vous.filter(statut=statut)
    else:
        statut = ""

    periode = request.GET.get("periode", "")
    if periode == "a_venir":
        rendez_vous = rendez_vous.filter(date_heure__gte=timezone.now()).order_by("date_heure")
    elif periode == "passes":
        rendez_vous = rendez_vous.filter(date_heure__lt=timezone.now()).order_by("-date_heure")
    else:
        periode = ""
        rendez_vous = rendez_vous.order_by("-date_heure")

    return rendez_vous, statut, periode


def _avertissement_cascade(compteurs):
    """Construit un message d'avertissement a partir d'un dict {libelle: total}."""
    parties = [f"{total} {libelle}" for libelle, total in compteurs.items() if total]
    if not parties:
        return None
    return "Seront aussi supprimés : " + ", ".join(parties) + "."


def _cellule_csv(valeur):
    """Neutralise l'injection de formule CSV."""
    texte = "" if valeur is None else str(valeur)
    if texte and texte[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + texte
    return texte


def _normaliser_texte_import(valeur):
    """Normalise une valeur de cellule pour une comparaison insensible aux accents/majuscules."""
    texte = "" if valeur is None else str(valeur).strip()
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return texte.upper()


# ---------------------------------------------------------------------------
# Permissions par rôle & isolation par organisme
# ---------------------------------------------------------------------------

def role_required(*roles):
    """
    Restreint une vue aux rôles indiqués.

    Exemple :
        @role_required(User.Role.ADMIN, User.Role.MEDECIN)
        def ma_vue(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                logger.warning(
                    f"Alerte de sécurité: Accès refusé pour {request.user.email} (rôle: {request.user.role}) "
                    f"vers {view_func.__name__} sur {request.path}. Rôles autorisés: {roles}"
                )
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_required(view_func):
    """Restreint une vue au rôle ADMIN (Administrateur Général) uniquement."""
    return role_required(User.Role.ADMIN)(view_func)


def gestionnaire_required(view_func):
    """Restreint une vue au rôle GESTIONNAIRE rattaché à un organisme défini et actif."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.GESTIONNAIRE:
            logger.warning(
                f"Alerte de sécurité: Accès refusé pour {request.user.email} (rôle: {request.user.role}) "
                f"vers {view_func.__name__} sur {request.path}. Rôle autorisé: GESTIONNAIRE"
            )
            raise PermissionDenied
        if not request.user.organisme_id or not request.user.organisme.actif:
            logger.warning(
                f"Alerte de sécurité: Gestionnaire {request.user.email} sans organisme actif "
                f"vers {view_func.__name__} sur {request.path}."
            )
            raise PermissionDenied("Ce compte gestionnaire n'est rattaché à aucun organisme actif.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def organisme_gestionnaire(request):
    """Retourne l'organisme actif du gestionnaire connecté ou lève PermissionDenied."""
    user = getattr(request, "user", None)
    if (
        user is None
        or not user.is_authenticated
        or user.role != User.Role.GESTIONNAIRE
        or not user.organisme_id
        or not user.organisme.actif
    ):
        raise PermissionDenied("Accès réservé à un gestionnaire rattaché à un organisme actif.")
    return user.organisme


def filtrer_par_organisme(request, queryset, champ="organisme"):
    """Filtre un queryset par l'organisme du gestionnaire connecté."""
    organisme = organisme_gestionnaire(request)
    return queryset.filter(**{champ: organisme})


def get_object_or_404_organisme(request, modele_ou_qs, champ="organisme", **kwargs):
    """Récupère un objet appartenant strictement à l'organisme du gestionnaire (sinon 404)."""
    qs = (
        modele_ou_qs
        if hasattr(modele_ou_qs, "filter")
        else modele_ou_qs._default_manager.all()
    )
    qs = filtrer_par_organisme(request, qs, champ=champ)
    return get_object_or_404(qs, **kwargs)


def compteurs_files_attente(request=None):
    """Compteurs des files d'attente (isolés par organisme pour un Gestionnaire)."""
    if request is not None and hasattr(request, "_compteurs_files_attente"):
        return request._compteurs_files_attente

    maintenant = timezone.now()
    il_y_a_48h = maintenant - datetime.timedelta(hours=48)

    user = getattr(request, "user", None) if request is not None else None
    pec_qs = PriseEnCharge.objects.all()
    paiement_qs = Paiement.objects.all()
    remb_qs = DemandeRemboursement.objects.filter(
        statut=DemandeRemboursement.Statut.EN_ATTENTE
    )
    ayants_droit_qs = Patient.objects.filter(
        type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT,
        statut_validation=Patient.StatutValidation.EN_ATTENTE,
    )

    if (
        user is not None
        and user.is_authenticated
        and user.role == User.Role.GESTIONNAIRE
        and user.organisme_id
    ):
        pec_qs = pec_qs.filter(patient__organisme_id=user.organisme_id)
        paiement_qs = paiement_qs.filter(consultation__patient__organisme_id=user.organisme_id)
        remb_qs = remb_qs.filter(organisme_id=user.organisme_id)
        ayants_droit_qs = ayants_droit_qs.filter(organisme_id=user.organisme_id)

    pec_stats = pec_qs.aggregate(
        total_attente=Count("id", filter=Q(statut="en_attente")),
        urgentes_48h=Count("id", filter=Q(statut="en_attente", date_demande__lte=il_y_a_48h)),
    )
    if user is not None and user.is_authenticated:
        if user.role == User.Role.ADMIN:
            demandes_support_attente = DemandeSupport.objects.filter(
                statut=DemandeSupport.Statut.EN_ATTENTE,
                categorie=DemandeSupport.Categorie.TECHNIQUE,
            ).count()
        elif user.role == User.Role.GESTIONNAIRE:
            qs_support = DemandeSupport.objects.filter(statut=DemandeSupport.Statut.EN_ATTENTE).exclude(
                categorie=DemandeSupport.Categorie.TECHNIQUE
            )
            if user.organisme_id:
                qs_support = qs_support.filter(patient__organisme_id=user.organisme_id)
            demandes_support_attente = qs_support.count()
        else:
            demandes_support_attente = 0
    else:
        demandes_support_attente = 0

    compteurs = {
        "prises_en_charge_attente": pec_stats["total_attente"] or 0,
        "nb_pec_urgentes_48h": pec_stats["urgentes_48h"] or 0,
        "paiements_non_regles": paiement_qs.filter(statut=Paiement.Statut.NON_REGLE).count(),
        "remboursements_attente": remb_qs.count(),
        "ayants_droit_en_attente": ayants_droit_qs.count(),
        "demandes_support_attente": demandes_support_attente,
    }
    if request is not None:
        request._compteurs_files_attente = compteurs
    return compteurs


def user_role(request):
    """Context processor : role, organisme, notifications non lues, et compteurs de file
    d'attente pour les pastilles du menu lateral.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {
            'current_role': None,
            'current_role_label': None,
            'current_organisme': None,
            'notifications_non_lues': 0,
            'whatsapp_bot_phone': getattr(settings, 'WHATSAPP_SENDER_PHONE', '221789576145'),
        }

    contexte = {
        'current_role': user.role,
        'current_role_label': user.get_role_display(),
        'current_organisme': user.organisme if user.organisme_id else None,
        'notifications_non_lues': user.notifications.filter(lue=False).count(),
        'whatsapp_bot_phone': getattr(settings, 'WHATSAPP_SENDER_PHONE', '221789576145'),
    }
    if user.role in (User.Role.ADMIN, User.Role.GESTIONNAIRE):
        compteurs = compteurs_files_attente(request)
        contexte['nb_prises_en_charge_attente'] = compteurs["prises_en_charge_attente"]
        contexte['nb_paiements_non_regles'] = compteurs["paiements_non_regles"]
        contexte['nb_remboursements_attente'] = compteurs["remboursements_attente"]
        contexte['nb_ayants_droit_en_attente'] = compteurs["ayants_droit_en_attente"]
        contexte['nb_demandes_support_attente'] = compteurs["demandes_support_attente"]
    return contexte
