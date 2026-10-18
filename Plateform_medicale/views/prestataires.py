"""
Prestataires (CRUD, géolocalisation Nominatim) et Plans de couverture (CRUD).
"""

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.db.models import Avg, Count, ProtectedError, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms import ConventionPrestataireForm, PlanCouvertureForm, PrestataireForm
from ..models import ConventionPrestataire, JournalActivite, PlanCouverture, Prestataire, User
from .utils import _avertissement_cascade, _paginer, _trier, journaliser, organisme_gestionnaire, role_required


@role_required(User.Role.GESTIONNAIRE)
def liste_prestataires(request):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    prestataires = Prestataire.objects.all()

    localisation = request.GET.get("localisation", "")
    if localisation == "sans":
        prestataires = prestataires.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        )
    elif localisation == "avec":
        prestataires = prestataires.filter(
            latitude__isnull=False, longitude__isnull=False
        )

    prestataires = _trier(
        request, prestataires, ["id", "nom", "type_prestataire", "ville", "partenaire"], "nom",
    )

    # Reseau de partenaires geolocalises, pour la carte (deplacee ici
    # depuis le dashboard admin) : seuls les champs necessaires au rendu.
    prestataires_carte = list(
        Prestataire.objects.filter(partenaire=True, latitude__isnull=False, longitude__isnull=False)
        .values("id", "nom", "type_prestataire", "ville", "telephone", "latitude", "longitude")
    )

    contexte = {
        "prestataires": _paginer(request, prestataires),
        "localisation_choisie": localisation,
        "prestataires_carte": prestataires_carte,
    }
    return render(request, "liste_prestataires.html", contexte)


# --- Nominatim : politesse et conformite -------------------------------------
#
# La politique d'usage d'OpenStreetMap impose au maximum UNE requete par
# seconde et decourage les appels repetes pour la meme recherche. Le code
# precedent n'avait ni l'un ni l'autre : chaque clic partait directement chez
# eux. Deux garde-fous, dans cet ordre :
#
#   1. cache (24 h) -- une recherche deja faite ne repart jamais ;
#   2. verrou + attente -- deux requetes ne peuvent pas partir a moins d'une
#      seconde d'intervalle.
#
# Limite connue et assumee : sans CACHES configure, Django utilise
# LocMemCache, donc cache ET verrou sont par PROCESSUS. Avec plusieurs
# workers, le debit reel peut atteindre 1 req/s par worker. C'est deja
# infiniment mieux que rien ; un cache partage (Redis, Memcached) leverait
# la reserve le jour ou la plateforme tourne sur plusieurs processus.

_NOMINATIM_VERROU = threading.Lock()
_NOMINATIM_DERNIER_APPEL = [0.0]
_NOMINATIM_DELAI_MINIMAL = 1.0
_NOMINATIM_DUREE_CACHE = 60 * 60 * 24

# Correspondance entre les etiquettes OpenStreetMap et nos types internes.
# On ne devine pas : ce qui n'est pas reconnu reste sans type, et
# l'administrateur choisit lui-meme.
_TYPES_OSM = {
    "hospital": Prestataire.Type.HOPITAL,
    "clinic": Prestataire.Type.CLINIQUE,
    "pharmacy": Prestataire.Type.PHARMACIE,
    "doctors": Prestataire.Type.CABINET,
    "doctor": Prestataire.Type.CABINET,
    "health_post": Prestataire.Type.CABINET,
    "health_centre": Prestataire.Type.CLINIQUE,
}


def _appeler_nominatim(chemin, parametres):
    """Appel unique a Nominatim, cache et espace dans le temps.

    Renvoie (donnees, erreur). `erreur` vaut None en cas de succes.
    """
    url = (
        f"https://nominatim.openstreetmap.org/{chemin}?"
        + urllib.parse.urlencode(parametres)
    )
    cle_cache = f"nominatim:{url}"
    en_cache = cache.get(cle_cache)
    if en_cache is not None:
        return en_cache, None

    with _NOMINATIM_VERROU:
        attente = _NOMINATIM_DELAI_MINIMAL - (
            time.monotonic() - _NOMINATIM_DERNIER_APPEL[0]
        )
        if attente > 0:
            time.sleep(attente)
        _NOMINATIM_DERNIER_APPEL[0] = time.monotonic()

        requete_http = urllib.request.Request(url, headers={
            "User-Agent": "SanteSN-PlateformeMedicale/1.0 (plateforme de sante, Senegal)",
            "Accept-Language": "fr",
        })
        try:
            with urllib.request.urlopen(requete_http, timeout=6) as reponse:
                donnees = json.loads(reponse.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return None, "service_indisponible"

    cache.set(cle_cache, donnees, _NOMINATIM_DUREE_CACHE)
    return donnees, None


def _resultat_osm(lieu):
    """Normalise un resultat Nominatim en etablissement exploitable.

    IMPORTANT : ce que renvoie cette fonction est un etablissement REEL trouve
    sur OpenStreetMap. Ce n'est PAS un prestataire de la plateforme. La
    distinction est portee jusque dans l'interface (`inscrit`), elle ne doit
    jamais etre gommee.
    """
    adresse = lieu.get("address") or {}
    ville = (
        adresse.get("city") or adresse.get("town") or adresse.get("village")
        or adresse.get("municipality") or adresse.get("county") or ""
    )
    voie = " ".join(part for part in (
        adresse.get("house_number"), adresse.get("road"),
        adresse.get("suburb") or adresse.get("neighbourhood"),
    ) if part)

    nom = lieu.get("name") or (lieu.get("display_name") or "").split(",")[0]
    type_osm = (lieu.get("type") or "").lower()
    latitude = lieu.get("lat")
    longitude = lieu.get("lon")

    # Un etablissement deja inscrit est signale : l'administrateur doit voir
    # d'un coup d'oeil qu'il s'apprete a creer un doublon.
    deja_inscrit = False
    if latitude and longitude:
        try:
            deja_inscrit = Prestataire.objects.filter(
                latitude__range=(float(latitude) - 0.0005, float(latitude) + 0.0005),
                longitude__range=(float(longitude) - 0.0005, float(longitude) + 0.0005),
            ).exists()
        except (TypeError, ValueError):
            deja_inscrit = False

    return {
        "nom": nom,
        "adresse": voie,
        "ville": ville,
        "lat": latitude,
        "lon": longitude,
        "type_osm": type_osm,
        "type_suggere": _TYPES_OSM.get(type_osm, ""),
        "libelle_complet": lieu.get("display_name", ""),
        "inscrit": deja_inscrit,
    }


@role_required(User.Role.GESTIONNAIRE)
def recherche_lieu_prestataire(request):
    """
    Relais serveur vers Nominatim (recherche OpenStreetMap) pour la recherche
    d'etablissements reels des formulaires prestataire. Un appel direct
    navigateur -> Nominatim est sujet a des echecs intermittents (CORS
    incoherent derriere leur cache, User-Agent de fetch() non identifiant) ;
    en passant par le serveur, la requete est same-origin cote navigateur et
    peut porter un User-Agent conforme a la politique d'usage de Nominatim.

    Renvoie une LISTE de resultats -- l'administrateur choisit. L'ancien
    contrat (trouve/lat/lon/nom, premier resultat) est conserve pour ne pas
    casser le bouton "Rechercher sur la carte" existant.
    """
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    requete = request.GET.get("q", "").strip()
    if not requete:
        return JsonResponse({"trouve": False, "resultats": []})

    donnees, erreur = _appeler_nominatim("search", {
        "format": "json",
        "limit": 8,
        "countrycodes": "sn",
        "addressdetails": 1,
        "q": f"{requete}, Senegal",
    })
    if erreur:
        return JsonResponse({"trouve": False, "resultats": [], "erreur": erreur})
    if not donnees:
        return JsonResponse({"trouve": False, "resultats": []})

    resultats = [_resultat_osm(lieu) for lieu in donnees]
    premier = resultats[0]
    return JsonResponse({
        "trouve": True,
        "lat": premier["lat"],
        "lon": premier["lon"],
        "nom": premier["libelle_complet"] or premier["nom"],
        "resultats": resultats,
    })


@role_required(User.Role.GESTIONNAIRE)
def ajouter_prestataire(request):
    organisme = organisme_gestionnaire(request)
    if request.method == "POST":
        form = PrestataireForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                prestataire = form.save()
                if prestataire.partenaire:
                    ConventionPrestataire.objects.get_or_create(
                        organisme=organisme,
                        prestataire=prestataire,
                        defaults={
                            "statut": ConventionPrestataire.Statut.ACTIF,
                            "tiers_payant_actif": True,
                            "cree_par": request.user,
                        },
                    )
            messages.success(request, f"L'établissement {prestataire.nom} a été créé et intégré avec succès à votre réseau conventionné.")
            return redirect("liste_prestataires")
    else:
        form = PrestataireForm()
    return render(request, "ajouter_prestataire.html", {"form": form})


@role_required(User.Role.GESTIONNAIRE)
def modifier_prestataire(request, pk):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    prestataire = get_object_or_404(Prestataire, pk=pk)
    if request.method == "POST":
        form = PrestataireForm(request.POST, instance=prestataire)
        if form.is_valid():
            form.save()
            messages.success(request, "Prestataire modifié.")
            return redirect("liste_prestataires")
    else:
        form = PrestataireForm(instance=prestataire)
    return render(request, "modifier_prestataire.html", {"form": form, "prestataire": prestataire})


@role_required(User.Role.GESTIONNAIRE)
def supprimer_prestataire(request, pk):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    prestataire = get_object_or_404(Prestataire, pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                nom_prestataire = str(prestataire)
                prestataire.delete()
                journaliser(request, JournalActivite.Action.SUPPRESSION, f"Prestataire : {nom_prestataire}")
                messages.success(request, "Prestataire supprimé.")
                return redirect("liste_prestataires")
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce prestataire : des éléments protégés y sont rattachés.")
            return redirect("liste_prestataires")
    return render(request, "confirmer_suppression.html", {"objet": prestataire, "type": "Prestataire"})


# ---------------------------------------------------------------------------
# Plans de couverture
# ---------------------------------------------------------------------------

from ..models import User  # noqa: E402
from .utils import organisme_gestionnaire, role_required  # noqa: E402


@role_required(User.Role.GESTIONNAIRE)
def liste_plans_couverture(request):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    plans_base = PlanCouverture.objects.annotate(nb_beneficiaires=Count("beneficiaires"))
    stats = plans_base.aggregate(
        total_plans=Count("id"),
        taux_moyen=Avg("taux_couverture"),
        total_beneficiaires=Count("beneficiaires"),
    )
    plans = _trier(request, plans_base, ["nom", "taux_couverture", "plafond_annuel"], "nom")
    return render(
        request,
        "liste_plans_couverture.html",
        {
            "plans": _paginer(request, plans),
            "stats": stats,
        },
    )


@role_required(User.Role.GESTIONNAIRE)
def ajouter_plan_couverture(request):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    if request.method == "POST":
        form = PlanCouvertureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan de couverture ajouté.")
            return redirect("liste_plans_couverture")
    else:
        form = PlanCouvertureForm()
    return render(request, "ajouter_plan_couverture.html", {"form": form})


@role_required(User.Role.GESTIONNAIRE)
def modifier_plan_couverture(request, pk):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if request.method == "POST":
        form = PlanCouvertureForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan de couverture modifié.")
            return redirect("liste_plans_couverture")
    else:
        form = PlanCouvertureForm(instance=plan)
    return render(request, "modifier_plan_couverture.html", {"form": form, "plan": plan})


@role_required(User.Role.GESTIONNAIRE)
def supprimer_plan_couverture(request, pk):
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme_gestionnaire(request)
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                nom_plan = str(plan)
                nb_beneficiaires = plan.beneficiaires.count()
                plan.delete()
                journaliser(
                    request,
                    JournalActivite.Action.SUPPRESSION,
                    f"Plan de couverture : {nom_plan}",
                    f"{nb_beneficiaires} bénéficiaire(s) perdent ce plan",
                )
                messages.success(request, "Plan de couverture supprimé.")
                return redirect("liste_plans_couverture")
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce plan de couverture : des éléments protégés y sont rattachés.")
            return redirect("liste_plans_couverture")
    avertissement = _avertissement_cascade({"assuré(s)/ayant(s) droit rattachés (plan retiré, pas supprimés)": plan.beneficiaires.count()})
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": plan, "type": "Plan de couverture", "avertissement": avertissement},
    )


@role_required(User.Role.GESTIONNAIRE)
def liste_conventions(request):
    """
    Réseau de soins conventionné propre à l'organisme assureur (IPM).
    Permet à chaque gestionnaire de piloter ses conventions de tiers payant.
    """
    organisme = organisme_gestionnaire(request)
    conventions = ConventionPrestataire.objects.filter(organisme=organisme).select_related("prestataire")

    # Filtres par statut et type d'établissement
    statut = request.GET.get("statut", "")
    if statut in ConventionPrestataire.Statut.values:
        conventions = conventions.filter(statut=statut)
    type_p = request.GET.get("type", "")
    if type_p in Prestataire.Type.values:
        conventions = conventions.filter(prestataire__type_prestataire=type_p)

    conventions = _trier(request, conventions, ["prestataire__nom", "statut", "date_conventionnement"], "prestataire__nom")

    contexte = {
        "conventions": _paginer(request, conventions),
        "organisme": organisme,
        "statut_choisi": statut,
        "type_choisi": type_p,
        "types_prestataires": Prestataire.Type.choices,
        "statuts_conventions": ConventionPrestataire.Statut.choices,
    }
    return render(request, "liste_conventions.html", contexte)


@role_required(User.Role.GESTIONNAIRE)
def ajouter_convention(request):
    """Conventionnement d'un établissement auprès de son organisme."""
    organisme = organisme_gestionnaire(request)
    if request.method == "POST":
        form = ConventionPrestataireForm(request.POST, organisme=organisme)
        if form.is_valid():
            convention = form.save(commit=False)
            convention.organisme = organisme
            convention.cree_par = request.user
            convention.save()
            journaliser(
                request,
                JournalActivite.Action.CREATION,
                f"Convention : {convention.prestataire.nom}",
                f"Réseau conventionné de {organisme.nom} (Réf : {convention.numero_convention or 'N/A'})",
            )
            messages.success(request, f"L'établissement {convention.prestataire.nom} a été conventionné avec succès.")
            return redirect("liste_conventions")
    else:
        form = ConventionPrestataireForm(organisme=organisme)

    nb_prestataires_disponibles = form.fields["prestataire"].queryset.count()
    return render(request, "ajouter_convention.html", {
        "form": form,
        "organisme": organisme,
        "nb_prestataires_disponibles": nb_prestataires_disponibles,
    })


@role_required(User.Role.GESTIONNAIRE)
def modifier_convention(request, pk):
    """Modification d'une convention existante par son organisme."""
    organisme = organisme_gestionnaire(request)
    convention = get_object_or_404(ConventionPrestataire, pk=pk, organisme=organisme)
    if request.method == "POST":
        form = ConventionPrestataireForm(request.POST, instance=convention, organisme=organisme)
        if form.is_valid():
            form.save()
            journaliser(
                request,
                JournalActivite.Action.MODIFICATION,
                f"Convention : {convention.prestataire.nom}",
                f"Convention mise à jour pour {organisme.nom}",
            )
            messages.success(request, f"La convention avec {convention.prestataire.nom} a été mise à jour avec succès.")
            return redirect("liste_conventions")
    else:
        form = ConventionPrestataireForm(instance=convention, organisme=organisme)
    return render(request, "modifier_convention.html", {
        "form": form,
        "convention": convention,
        "organisme": organisme,
    })


@role_required(User.Role.GESTIONNAIRE)
def supprimer_convention(request, pk):
    """Supprime / retire un établissement du réseau conventionné."""
    organisme = organisme_gestionnaire(request)
    convention = get_object_or_404(ConventionPrestataire, pk=pk, organisme=organisme)
    nom_prestataire = convention.prestataire.nom
    if request.method == "POST":
        convention.delete()
        journaliser(
            request,
            JournalActivite.Action.SUPPRESSION,
            f"Convention : {nom_prestataire}",
            f"Retrait de {nom_prestataire} du réseau conventionné de {organisme.nom}",
        )
        messages.success(request, f"L'établissement {nom_prestataire} a été retiré de votre réseau conventionné.")
        return redirect("liste_conventions")
    return render(request, "confirmer_suppression.html", {
        "titre": "Retirer l'établissement du réseau",
        "message": f"Êtes-vous sûr de vouloir retirer {nom_prestataire} du réseau conventionné de {organisme.nom} ? Vos assurés ne pourront plus y bénéficier du tiers payant automatique.",
        "url_retour": reverse("liste_conventions"),
    })


@role_required(User.Role.GESTIONNAIRE)
def changer_statut_convention(request, pk):
    """Active, suspend ou résilie une convention pour son organisme."""
    organisme = organisme_gestionnaire(request)
    convention = get_object_or_404(ConventionPrestataire, pk=pk, organisme=organisme)
    if request.method == "POST":
        nouveau_statut = request.POST.get("statut")
        # Normalisation souple des alias masculin/féminin
        if nouveau_statut in ("ACTIVE", "ACTIF"):
            nouveau_statut = ConventionPrestataire.Statut.ACTIF
        elif nouveau_statut in ("SUSPENDUE", "SUSPENDU"):
            nouveau_statut = ConventionPrestataire.Statut.SUSPENDU

        if nouveau_statut in ConventionPrestataire.Statut.values:
            convention.statut = nouveau_statut
            convention.save(update_fields=["statut"])
            journaliser(
                request,
                JournalActivite.Action.MODIFICATION,
                f"Convention {convention.prestataire.nom}",
                f"Statut passé à {convention.get_statut_display()}",
            )
            messages.success(request, f"Statut de la convention mis à jour : {convention.get_statut_display()}.")
    return redirect("liste_conventions")

