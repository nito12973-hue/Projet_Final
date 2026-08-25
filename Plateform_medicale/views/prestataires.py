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
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PlanCouvertureForm, PrestataireForm
from ..models import JournalActivite, PlanCouverture, Prestataire
from .utils import _avertissement_cascade, _paginer, _trier, admin_required, journaliser


@admin_required
def liste_prestataires(request):
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
        .values("nom", "type_prestataire", "ville", "latitude", "longitude")
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


@admin_required
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


@admin_required
def ajouter_prestataire(request):
    if request.method == "POST":
        form = PrestataireForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Prestataire ajouté.")
            return redirect("liste_prestataires")
    else:
        form = PrestataireForm()
    return render(request, "ajouter_prestataire.html", {"form": form})


@admin_required
def modifier_prestataire(request, pk):
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


@admin_required
def supprimer_prestataire(request, pk):
    prestataire = get_object_or_404(Prestataire, pk=pk)
    if request.method == "POST":
        journaliser(request, JournalActivite.Action.SUPPRESSION, f"Prestataire : {prestataire}")
        prestataire.delete()
        messages.success(request, "Prestataire supprimé.")
        return redirect("liste_prestataires")
    return render(request, "confirmer_suppression.html", {"objet": prestataire, "type": "Prestataire"})


# ---------------------------------------------------------------------------
# Plans de couverture
# ---------------------------------------------------------------------------

@admin_required
def liste_plans_couverture(request):
    plans = _trier(request, PlanCouverture.objects.all(), ["nom", "taux_couverture", "plafond_annuel"], "nom")
    return render(request, "liste_plans_couverture.html", {"plans": _paginer(request, plans)})


@admin_required
def ajouter_plan_couverture(request):
    if request.method == "POST":
        form = PlanCouvertureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan de couverture ajouté.")
            return redirect("liste_plans_couverture")
    else:
        form = PlanCouvertureForm()
    return render(request, "ajouter_plan_couverture.html", {"form": form})


@admin_required
def modifier_plan_couverture(request, pk):
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


@admin_required
def supprimer_plan_couverture(request, pk):
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if request.method == "POST":
        journaliser(request, JournalActivite.Action.SUPPRESSION, f"Plan de couverture : {plan}",
                    f"{plan.beneficiaires.count()} bénéficiaire(s) perdent ce plan")
        plan.delete()
        messages.success(request, "Plan de couverture supprimé.")
        return redirect("liste_plans_couverture")
    avertissement = _avertissement_cascade({"assuré(s)/ayant(s) droit rattachés (plan retiré, pas supprimés)": plan.beneficiaires.count()})
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": plan, "type": "Plan de couverture", "avertissement": avertissement},
    )
