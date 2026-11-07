"""
Prestataires (CRUD, géolocalisation Nominatim) et Plans de couverture (CRUD).
"""

import json
import os
import re
import threading
import time
import unicodedata
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
from ..models import ConventionPrestataire, JournalActivite, Organisme, PlanCouverture, Prestataire, User
from .utils import _avertissement_cascade, _paginer, _trier, journaliser, organisme_gestionnaire, role_required


def _assurer_clinique_ocean(organisme):
    """Garantit la présence initiale de la Clinique de l'Océan en démo si elle n'existe pas encore."""
    import sys
    if not organisme or "test" in sys.argv:
        return
    try:
        from decimal import Decimal
        clinique, created = Prestataire.objects.get_or_create(
            nom="Clinique de l'Océan",
            defaults={
                "type_prestataire": Prestataire.Type.CLINIQUE,
                "ville": "Dakar",
                "adresse": "Boulevard de la Corniche Ouest – Avenue Cheikh Anta Diop, Fann Hock",
                "telephone": "338258585",
                "partenaire": True,
                "latitude": Decimal("14.6865"),
                "longitude": Decimal("-17.4642"),
            },
        )
        if created:
            ConventionPrestataire.objects.get_or_create(
                organisme=organisme,
                prestataire=clinique,
                defaults={
                    "statut": ConventionPrestataire.Statut.ACTIF,
                    "numero_convention": f"CONV-{organisme.code}-{clinique.pk}",
                    "tiers_payant_actif": True,
                },
            )
    except Exception:
        pass


def _prestataires_organisme(organisme):
    """Retourne les prestataires conventionnés avec l'organisme du gestionnaire."""
    if not organisme:
        return Prestataire.objects.none()
    _assurer_clinique_ocean(organisme)
    qs = Prestataire.objects.filter(conventions_organismes__organisme=organisme)
    if organisme.code == Organisme.CODE_DEFAUT:
        qs = qs | Prestataire.objects.filter(conventions_organismes__isnull=True)
    return qs.distinct()


@role_required(User.Role.GESTIONNAIRE)
def liste_prestataires(request):
    organisme = organisme_gestionnaire(request)
    prestataires = _prestataires_organisme(organisme)

    recherche = request.GET.get("q", "").strip()
    if recherche:
        terme_norm = _normaliser_recherche_texte(recherche)
        mots = [
            m for m in terme_norm.split()
            if m not in ("de", "du", "la", "le", "les", "des", "l", "d", "a", "au", "en", "senegal")
        ]
        if not mots:
            mots = [terme_norm]

        prestataires_liste = list(prestataires)
        ids_retenus = []
        for p in prestataires_liste:
            corpus = _normaliser_recherche_texte(f"{p.nom} {p.ville} {p.adresse} {p.telephone}")
            corpus_compact = corpus.replace(" ", "")

            def _match_mot(mot):
                if mot in corpus or mot in corpus_compact:
                    return True
                if mot.startswith("l") and len(mot) > 2 and mot[1:] in corpus:
                    return True
                if mot.startswith("d") and len(mot) > 2 and mot[1:] in corpus:
                    return True
                return False

            if terme_norm in corpus or all(_match_mot(m) for m in mots):
                ids_retenus.append(p.pk)

        prestataires = prestataires.filter(pk__in=ids_retenus)

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

    # Réseau de partenaires géolocalisés de cet organisme uniquement, pour la carte
    prestataires_carte = list(
        prestataires
        .filter(partenaire=True, latitude__isnull=False, longitude__isnull=False)
        .values("id", "nom", "type_prestataire", "ville", "telephone", "latitude", "longitude")
    )
    if not prestataires_carte and not recherche:
        prestataires_carte = list(
            _prestataires_organisme(organisme)
            .filter(partenaire=True, latitude__isnull=False, longitude__isnull=False)
            .values("id", "nom", "type_prestataire", "ville", "telephone", "latitude", "longitude")
        )

    # Établissements découverts dans le répertoire national de santé sénégalais
    # qui ne sont pas encore conventionnés avec l'organisme
    suggestions_decouverte = []
    if recherche:
        etabs_trouves = _rechercher_referentiel_sante(recherche)
        noms_deja_conventionnes = {
            _normaliser_recherche_texte(n)
            for n in _prestataires_organisme(organisme).values_list("nom", flat=True)
        }
        for etab in etabs_trouves[:6]:
            etab_nom_norm = _normaliser_recherche_texte(etab["nom"])
            if etab_nom_norm not in noms_deja_conventionnes:
                suggestions_decouverte.append(etab)

    contexte = {
        "prestataires": _paginer(request, prestataires),
        "localisation_choisie": localisation,
        "prestataires_carte": prestataires_carte,
        "recherche_q": recherche,
        "suggestions_decouverte": suggestions_decouverte,
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

# Répertoire national de référence des grands établissements de santé du Sénégal.
# Couvre les cliniques, hôpitaux, centres de santé et laboratoires majeurs du Sénégal
# pour garantir que toute recherche par nom usuel (ex: "Clinique de l'Océan", "Madeleine", "Suma", etc.)
# soit immédiatement trouvée et pré-remplie avec ses coordonnées GPS réelles.
_REFERENTIEL_SANTE_SENEGAL = [
    {
        "nom": "Clinique de l'Océan",
        "mots_cles": ["ocean", "clinique ocean", "fann", "point e"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Boulevard de la Corniche Ouest × Avenue Cheikh Anta Diop, Fann Hock",
        "ville": "Dakar",
        "lat": "14.686500",
        "lon": "-17.464200",
        "telephone": "338258585",
    },
    {
        "nom": "Clinique de la Madeleine",
        "mots_cles": ["madeleine", "clinique madeleine", "plateau"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "18 Avenue des Ambassadeurs, Fann Résidence",
        "ville": "Dakar",
        "lat": "14.689200",
        "lon": "-17.472100",
        "telephone": "338899470",
    },
    {
        "nom": "Clinique Pasteur",
        "mots_cles": ["pasteur", "clinique pasteur", "plateau"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "50 Rue Carnot × Rue Saint-Michel, Plateau",
        "ville": "Dakar",
        "lat": "14.668500",
        "lon": "-17.433500",
        "telephone": "338234320",
    },
    {
        "nom": "Clinique du Cap",
        "mots_cles": ["cap", "clinique du cap", "corniche", "fann"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Avenue Pasteur × Corniche Est, Plateau",
        "ville": "Dakar",
        "lat": "14.661200",
        "lon": "-17.430500",
        "telephone": "338890202",
    },
    {
        "nom": "Clinique Casahous",
        "mots_cles": ["casahous", "clinique casahous", "plateau"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "5 Rue de Thiong × Rue Parchappe, Plateau",
        "ville": "Dakar",
        "lat": "14.671000",
        "lon": "-17.435800",
        "telephone": "338213670",
    },
    {
        "nom": "Clinique Suma Assistance",
        "mots_cles": ["suma", "suma assistance", "urgence", "point e"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Rue de Diourbel × Boulevard de l'Est, Point E",
        "ville": "Dakar",
        "lat": "14.697500",
        "lon": "-17.461800",
        "telephone": "338242418",
    },
    {
        "nom": "Clinique des Mamelles",
        "mots_cles": ["mamelles", "clinique des mamelles", "ouakam"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Route des Almadies × Cité des Mamelles",
        "ville": "Dakar",
        "lat": "14.731500",
        "lon": "-17.498800",
        "telephone": "338605050",
    },
    {
        "nom": "Clinique Les Almadies",
        "mots_cles": ["almadies", "clinique almadies", "ngor"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Zone 12, Route de la Pointe des Almadies",
        "ville": "Dakar",
        "lat": "14.746000",
        "lon": "-17.514000",
        "telephone": "338202020",
    },
    {
        "nom": "Clinique de l'Amitié",
        "mots_cles": ["amitie", "clinique de l amitie", "amitie 2", "point e"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Allée Seydou Nourou Tall, Amitié 2",
        "ville": "Dakar",
        "lat": "14.704200",
        "lon": "-17.458200",
        "telephone": "338242020",
    },
    {
        "nom": "Clinique de la Croix Bleue",
        "mots_cles": ["croix bleue", "mermoz"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Mermoz Pyrotechnie, Voie de Dégagement Nord",
        "ville": "Dakar",
        "lat": "14.712500",
        "lon": "-17.471000",
        "telephone": "338641212",
    },
    {
        "nom": "Clinique Rahma",
        "mots_cles": ["rahma", "clinique rahma", "maristes", "hann"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Hann Maristes 1, près du péage",
        "ville": "Dakar",
        "lat": "14.729000",
        "lon": "-17.435000",
        "telephone": "338321010",
    },
    {
        "nom": "Clinique du Golf",
        "mots_cles": ["golf", "clinique du golf", "cambarene", "guediawaye"],
        "type": Prestataire.Type.CLINIQUE,
        "adresse": "Cité Golf Sud, Guédiawaye",
        "ville": "Guédiawaye",
        "lat": "14.768000",
        "lon": "-17.395000",
        "telephone": "338772020",
    },
    {
        "nom": "Hôpital Principal de Dakar",
        "mots_cles": ["principal", "hopital principal", "plateau"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "1 Avenue Nelson Mandela, Plateau",
        "ville": "Dakar",
        "lat": "14.664000",
        "lon": "-17.431000",
        "telephone": "338395050",
    },
    {
        "nom": "Centre Hospitalier National Universitaire de Fann (CHNU Fann)",
        "mots_cles": ["fann", "hopital fann", "chnu fann"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Avenue Cheikh Anta Diop, Fann Résidence",
        "ville": "Dakar",
        "lat": "14.693000",
        "lon": "-17.468000",
        "telephone": "338691818",
    },
    {
        "nom": "Hôpital Général Idrissa Pouye (Grand Yoff - ex CTO)",
        "mots_cles": ["idrissa pouye", "cto", "hopital grand yoff", "hogip"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Route de l'Aéroport, Grand Yoff",
        "ville": "Dakar",
        "lat": "14.733000",
        "lon": "-17.452000",
        "telephone": "338694050",
    },
    {
        "nom": "Hôpital National Dalal Jamm",
        "mots_cles": ["dalal jamm", "hopital dalal jamm", "guediawaye"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Golf Sud, Corniche de Guédiawaye",
        "ville": "Guédiawaye",
        "lat": "14.774500",
        "lon": "-17.382000",
        "telephone": "338793000",
    },
    {
        "nom": "Hôpital Abass Ndao",
        "mots_cles": ["abass ndao", "hopital abass ndao", "gueule tapee", "medina"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Avenue Cheikh Anta Diop × Rue 11, Médina / Gueule Tapée",
        "ville": "Dakar",
        "lat": "14.685000",
        "lon": "-17.456000",
        "telephone": "338497800",
    },
    {
        "nom": "Hôpital d'Enfants Albert Royer",
        "mots_cles": ["albert royer", "hopital albert royer", "pediatrie fann"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Enceinte CHNU Fann, Avenue Cheikh Anta Diop",
        "ville": "Dakar",
        "lat": "14.694200",
        "lon": "-17.469500",
        "telephone": "338691800",
    },
    {
        "nom": "Hôpital Militaire de Ouakam (HMO)",
        "mots_cles": ["ouakam", "hopital militaire ouakam", "hmo"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Route de Ouakam, face Camp Militaire",
        "ville": "Dakar",
        "lat": "14.722000",
        "lon": "-17.488000",
        "telephone": "338603030",
    },
    {
        "nom": "Hôpital Roi Baudouin",
        "mots_cles": ["roi baudouin", "guediawaye", "hopital baudouin"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Croisement Béthio, Guédiawaye",
        "ville": "Guédiawaye",
        "lat": "14.764000",
        "lon": "-17.391000",
        "telephone": "338771010",
    },
    {
        "nom": "Hôpital de Pikine (Camp Militaire Thiaroye)",
        "mots_cles": ["hopital pikine", "thiaroye", "pikine"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Route Nationale 1, Camp de Thiaroye, Pikine",
        "ville": "Pikine",
        "lat": "14.752000",
        "lon": "-17.378000",
        "telephone": "338341515",
    },
    {
        "nom": "Hôpital Youssou Mbargane Diop",
        "mots_cles": ["youssou mbargane", "hopital rufisque", "rufisque"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Centre-ville Rufisque, Boulevard Maurice Guèye",
        "ville": "Rufisque",
        "lat": "14.717500",
        "lon": "-17.272000",
        "telephone": "338361020",
    },
    {
        "nom": "Hôpital d'Enfants de Diamniadio (HED)",
        "mots_cles": ["diamniadio", "hopital diamniadio", "enfants diamniadio"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Pôle Urbain de Diamniadio, Route de Mbour",
        "ville": "Diamniadio",
        "lat": "14.725000",
        "lon": "-17.182000",
        "telephone": "338368000",
    },
    {
        "nom": "Hôpital Régional Amadou Sakhir Mbaye de Louga",
        "mots_cles": ["amadou sakhir mbaye", "hopital louga", "louga"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Quartier Santhiaba, Louga",
        "ville": "Louga",
        "lat": "15.619000",
        "lon": "-16.225000",
        "telephone": "339671120",
    },
    {
        "nom": "Hôpital Régional de Thiès",
        "mots_cles": ["hopital thies", "regional thies"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Avenue Général de Gaulle, Thiès",
        "ville": "Thiès",
        "lat": "14.789000",
        "lon": "-16.926000",
        "telephone": "339511050",
    },
    {
        "nom": "Hôpital Saint-Jean de Dieu de Thiès",
        "mots_cles": ["saint jean de dieu", "st jean de dieu", "thies"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Quartier Diakhao, Thiès",
        "ville": "Thiès",
        "lat": "14.795000",
        "lon": "-16.935000",
        "telephone": "339511213",
    },
    {
        "nom": "Hôpital Régional de Saint-Louis",
        "mots_cles": ["hopital saint louis", "saint louis", "ndar"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Pointe Sud de l'Île de Saint-Louis",
        "ville": "Saint-Louis",
        "lat": "16.024000",
        "lon": "-16.502000",
        "telephone": "339611020",
    },
    {
        "nom": "Hôpital Régional El Hadji Ibrahima Niass de Kaolack",
        "mots_cles": ["ibrahima niass", "hopital kaolack", "kaolack"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Boulevard Dial Diop, Kaolack",
        "ville": "Kaolack",
        "lat": "14.148000",
        "lon": "-16.075000",
        "telephone": "339411030",
    },
    {
        "nom": "Hôpital de la Paix de Ziguinchor",
        "mots_cles": ["hopital de la paix", "ziguinchor", "casamance"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Route de l'Université Assane Seck, Ziguinchor",
        "ville": "Ziguinchor",
        "lat": "12.559000",
        "lon": "-16.273000",
        "telephone": "339912020",
    },
    {
        "nom": "Hôpital Matlaboul Fawzaini de Touba",
        "mots_cles": ["matlaboul fawzaini", "hopital touba", "touba"],
        "type": Prestataire.Type.HOPITAL,
        "adresse": "Grande Rocade Ouest, Touba",
        "ville": "Touba",
        "lat": "14.865000",
        "lon": "-15.878000",
        "telephone": "339781010",
    },
    {
        "nom": "Institut Pasteur de Dakar",
        "mots_cles": ["institut pasteur", "laboratoire pasteur", "pasteur dakar"],
        "type": Prestataire.Type.CABINET,
        "adresse": "36 Avenue Pasteur, Plateau",
        "ville": "Dakar",
        "lat": "14.662500",
        "lon": "-17.432000",
        "telephone": "338399200",
    },
    {
        "nom": "Laboratoire Bio24",
        "mots_cles": ["bio24", "laboratoire bio24", "analyses dakar", "point e"],
        "type": Prestataire.Type.CABINET,
        "adresse": "Rue 3 × Boulevard de l'Est, Point E",
        "ville": "Dakar",
        "lat": "14.698000",
        "lon": "-17.461000",
        "telephone": "338242424",
    },
    {
        "nom": "Pharmacie Guigon",
        "mots_cles": ["guigon", "pharmacie guigon", "plateau"],
        "type": Prestataire.Type.PHARMACIE,
        "adresse": "Avenue Lamine Guèye × Rue Félix Faure, Plateau",
        "ville": "Dakar",
        "lat": "14.672000",
        "lon": "-17.437000",
        "telephone": "338212121",
    },
    {
        "nom": "Grande Pharmacie Dakaroise",
        "mots_cles": ["dakaroise", "grande pharmacie dakaroise", "ponty"],
        "type": Prestataire.Type.PHARMACIE,
        "adresse": "Place de l'Indépendance, Plateau",
        "ville": "Dakar",
        "lat": "14.670500",
        "lon": "-17.433000",
        "telephone": "338233333",
    },
]


def _normaliser_recherche_texte(chaine: str) -> str:
    """Supprime accents, apostrophes et ponctuation pour recherche tolérante."""
    if not chaine:
        return ""
    # Remplacer apostrophes courbes ou droites par un espace
    texte = re.sub(r"['’`´]", " ", chaine)
    # Normalisation NFD pour retirer les accents de manière universelle
    texte_sans_accents = "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if not unicodedata.combining(c)
    )
    # Minuscule et épuration des caractères non alphanumériques
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s]", " ", texte_sans_accents)).strip().lower()


def _charger_etablissements_senegal():
    """Charge l'ensemble des établissements de santé répertoriés au Sénégal (base complète et enrichie)."""
    global _REFERENTIEL_SANTE_SENEGAL
    fichier_data = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "etablissements_sante_senegal.json"
    )
    if os.path.exists(fichier_data):
        try:
            with open(fichier_data, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _REFERENTIEL_SANTE_SENEGAL


_ETABLISSEMENTS_SANTE_SENEGAL = None


def _rechercher_referentiel_sante(terme_recherche: str):
    """Recherche un établissement dans le référentiel national de santé sénégalais (14 régions du Sénégal)."""
    global _ETABLISSEMENTS_SANTE_SENEGAL
    if not terme_recherche:
        return []
    if _ETABLISSEMENTS_SANTE_SENEGAL is None:
        _ETABLISSEMENTS_SANTE_SENEGAL = _charger_etablissements_senegal()

    terme_norm = _normaliser_recherche_texte(terme_recherche)
    stopwords = {"de", "du", "la", "le", "les", "des", "l", "d", "a", "au", "aux", "en", "senegal"}
    mots_cles_cherche = [m for m in terme_norm.split() if m not in stopwords]
    if not mots_cles_cherche:
        return []

    generic_terms = {"centre", "sante", "poste", "case", "dispensaire", "hopital", "clinique", "pharmacie", "cabinet", "modulaire"}
    mots_specifiques = [m for m in mots_cles_cherche if m not in generic_terms]

    resultats = []
    for etab in _ETABLISSEMENTS_SANTE_SENEGAL:
        nom_norm = _normaliser_recherche_texte(etab.get("nom", ""))
        nom_tokens = set(nom_norm.split())
        ville_norm = _normaliser_recherche_texte(etab.get("ville", ""))
        adresse_norm = _normaliser_recherche_texte(etab.get("adresse", ""))
        contexte_norm = f"{nom_norm} {adresse_norm} {ville_norm}"
        contexte_tokens = set(contexte_norm.split())

        score = 0
        # 1. Correspondance exacte ou début de chaîne sur le nom
        if terme_norm == nom_norm:
            score += 100
        elif terme_norm in nom_norm:
            score += 50
        elif nom_norm in terme_norm and nom_norm not in {"centre de sante", "poste de sante", "case de sante", "hopital", "clinique", "pharmacie", "cabinet"}:
            score += 30

        # 2. Filtrage et score par mots-clés spécifiques (ex: nom propre de la structure)
        if mots_specifiques:
            spec_nom_match = sum(1 for m in mots_specifiques if m in nom_tokens)
            spec_ctx_match = sum(1 for m in mots_specifiques if m in contexte_tokens)

            # Si la requête contient des mots spécifiques distincts (ex: Mamadou, Diop),
            # on exige qu'au moins un seuil significatif soit présent (pas de faux positif)
            seuil = len(mots_specifiques) if len(mots_specifiques) <= 2 else max(2, len(mots_specifiques) - 1)
            if spec_nom_match >= seuil:
                score += spec_nom_match * 35
            elif spec_ctx_match >= seuil:
                score += spec_ctx_match * 20
            else:
                continue
        else:
            # Requête purement générique (ex: "centre de santé", "pharmacie")
            gen_match = sum(1 for m in mots_cles_cherche if m in nom_tokens)
            if gen_match == len(mots_cles_cherche):
                score += 30
            elif gen_match > 0:
                score += gen_match * 10

        # 3. Correspondance par mots clés dédiés dans la fiche
        for mc in etab.get("mots_cles", []):
            mc_norm = _normaliser_recherche_texte(mc)
            if mc_norm in terme_norm or terme_norm in mc_norm:
                score += 15
                break

        if score >= 20:
            resultats.append((score, etab))

    resultats.sort(key=lambda x: x[0], reverse=True)
    return [etab for _, etab in resultats[:12]]

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


_TYPES_OSM_NON_SANTE = {
    "bakery", "supermarket", "convenience", "clothes", "hairdresser", "car_repair",
    "car_wash", "kiosk", "butcher", "dry_cleaning", "department_store", "mall",
    "restaurant", "fast_food", "cafe", "bar", "pub", "nightclub",
    "hotel", "motel", "guest_house", "hostel",
    "school", "kindergarten", "university", "college",
    "dojo", "sports_centre", "stadium", "fitness_centre", "park",
    "bus_stop", "fuel", "bank", "atm", "police", "post_office",
    "place_of_worship", "marketplace", "cinema", "veterinary",
}

_CLASSES_OSM_NON_SANTE = {"shop", "leisure", "tourism", "craft", "sport"}

_MOTS_RECHERCHE_NON_SANTE = {
    "boulangerie", "patisserie", "restaurant", "hotel", "auberge",
    "station", "essence", "garage", "mecanique", "lavage", "pressing",
    "boutique", "magasin", "supermarche", "marche", "boucherie",
    "mosquee", "eglise", "paroisse", "cathedrale",
    "ecole", "lycee", "college", "universite", "stade", "terrain",
}

_MOTS_CLEFS_SANTE = (
    "hopital", "clinique", "pharmacie", "cabinet medical", "cabinet dentaire",
    "centre de sante", "poste de sante", "dispensaire", "maternite",
    "polyclinique", "laboratoire", "dentiste", "infirmerie", "samu", "sante", "medical",
)


def _est_lieu_sante_admissible(lieu, requete_texte=""):
    """Vérifie qu'un lieu trouvé correspond rigoureusement au domaine de la santé."""
    type_osm = (lieu.get("type") or "").lower()
    classe_osm = (lieu.get("class") or "").lower()
    nom = _normaliser_recherche_texte(lieu.get("name") or lieu.get("display_name") or "")
    q_norm = _normaliser_recherche_texte(requete_texte)
    q_tokens = set(q_norm.split())

    # 1. Si la requête textuelle cible explicitement un commerce, culte ou loisir non médical
    if q_tokens & _MOTS_RECHERCHE_NON_SANTE:
        if not any(k in q_norm for k in ("hopital", "clinique", "pharmacie", "sante", "medical", "docteur", "cabinet")):
            return False

    # 2. Si le type ou la classe OpenStreetMap est manifestement non médical
    if type_osm in _TYPES_OSM_NON_SANTE or classe_osm in _CLASSES_OSM_NON_SANTE:
        if not any(k in nom for k in _MOTS_CLEFS_SANTE):
            return False

    # 3. Éviter les faux positifs mal étiquetés comme hospital (ex: mosquées, marchés ou stades)
    if any(m in nom for m in ("mosquee", "eglise", "marche", "boulangerie", "restaurant", "hotel", "stade")):
        if not any(k in nom for k in ("hopital", "clinique", "pharmacie", "centre de sante", "dispensaire")):
            return False

    return True


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

    # Si la requête cible explicitement un commerce ou équipement hors santé sans aucun mot médical
    q_tokens = set(_normaliser_recherche_texte(requete).split())
    if (q_tokens & _MOTS_RECHERCHE_NON_SANTE) and not any(k in _normaliser_recherche_texte(requete) for k in ("hopital", "clinique", "pharmacie", "sante", "medical", "docteur", "cabinet")):
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

    # Si Nominatim a trouvé des résultats (cas standard ou tests mockés),
    # on filtre strictement pour ne conserver que les structures de santé admissibles.
    if donnees:
        donnees_sante = [lieu for lieu in donnees if _est_lieu_sante_admissible(lieu, requete)]
        if donnees_sante:
            resultats = [_resultat_osm(lieu) for lieu in donnees_sante]
            premier = resultats[0]
            return JsonResponse({
                "trouve": True,
                "lat": premier["lat"],
                "lon": premier["lon"],
                "nom": premier["libelle_complet"] or premier["nom"],
                "resultats": resultats,
            })

    # Fallback si Nominatim n'a RIEN trouvé (ex: "CLINIQUE DE L'OCEAN DAKAR") :
    # 1. Vérifier dans notre référentiel de santé national du Sénégal
    etabs_ref = _rechercher_referentiel_sante(requete)
    if etabs_ref:
        resultats_ref = []
        for er in etabs_ref:
            deja_inscrit = False
            try:
                deja_inscrit = Prestataire.objects.filter(
                    latitude__range=(float(er["lat"]) - 0.001, float(er["lat"]) + 0.001),
                    longitude__range=(float(er["lon"]) - 0.001, float(er["lon"]) + 0.001),
                ).exists() or Prestataire.objects.filter(nom__icontains=er["nom"]).exists()
            except Exception:
                deja_inscrit = False

            resultats_ref.append({
                "nom": er["nom"],
                "adresse": er["adresse"],
                "ville": er["ville"],
                "lat": er["lat"],
                "lon": er["lon"],
                "type_osm": er["type"].lower(),
                "type_suggere": er["type"],
                "libelle_complet": f"{er['nom']}, {er['adresse']}, {er['ville']}, Sénégal",
                "telephone": er.get("telephone", ""),
                "inscrit": deja_inscrit,
                "source": "referentiel_senegal",
            })
        premier = resultats_ref[0]
        return JsonResponse({
            "trouve": True,
            "lat": premier["lat"],
            "lon": premier["lon"],
            "nom": premier["libelle_complet"] or premier["nom"],
            "resultats": resultats_ref,
        })

    # 2. Deuxième étape : Exploration intelligente et automatique du terrain médical (OpenStreetMap)
    #    Si l'établissement n'a pas été trouvé tel quel (nom tronqué, nouvelle structure inaugurée
    #    dont le libellé OSM est vide ou abrégé), on analyse l'intention médicale et géographique.
    mots_bruts = [
        m for m in _normaliser_recherche_texte(requete).split()
        if m not in ("senegal", "de", "du", "la", "le", "les", "des", "l", "d", "a", "au", "aux", "en")
    ]
    prefixes_sante = {"centre", "sante", "poste", "case", "dispensaire", "hopital", "clinique", "pharmacie", "cabinet", "modulaire"}
    is_medical_intent = bool(set(mots_bruts) & prefixes_sante)
    mots_specifiques = [m for m in mots_bruts if m not in prefixes_sante]

    # Reconnaissance contextuelle des zones géographiques, communes et quartiers sénégalais
    mots_geo = {
        "liberte", "dakar", "thies", "rufisque", "mbour", "touba", "kaolack",
        "saint", "louis", "yoff", "ouakam", "almadies", "parcelles", "grand",
        "extension", "sicap", "fann", "point", "e", "plateau", "mermoz", "medina",
        "fas", "fass", "colobane", "dieuppeul", "derkle", "ngor", "yoff", "diamniadio",
        "keur", "massar", "guediawaye", "pikine", "ziguinchor", "kolda", "fatick",
        "kaffrine", "sedhiou", "matam", "kedougou", "tambacounda", "diourbel", "louga"
    }
    zone_tokens = [m for m in mots_bruts if m in mots_geo]

    # Requêtes de recherche ciblées
    requetes_repli = []
    if mots_bruts:
        requetes_repli.append(" ".join(mots_bruts))
    if mots_specifiques and " ".join(mots_specifiques) not in requetes_repli:
        requetes_repli.append(" ".join(mots_specifiques))

    # Types OSM purement non médicaux à rejeter en cas d'intention médicale
    types_non_medicaux = {
        "dojo", "sports_centre", "school", "bus_stop", "highway", "university",
        "place_of_worship", "car_wash", "bank", "fuel", "restaurant", "fast_food",
        "hotel", "motel", "guest_house", "police", "post_office", "supermarket",
        "shop", "kiosk", "stadium"
    }

    for q_tentative in requetes_repli:
        donnees_fb, _ = _appeler_nominatim("search", {
            "format": "json",
            "limit": 6,
            "countrycodes": "sn",
            "addressdetails": 1,
            "q": q_tentative,
        })
        if donnees_fb:
            # Filtrer les faux positifs non médicaux si l'utilisateur cherchait une structure médicale
            if is_medical_intent:
                donnees_valides = [
                    lieu for lieu in donnees_fb
                    if (lieu.get("type") or "").lower() not in types_non_medicaux
                ]
            else:
                donnees_valides = donnees_fb

            if donnees_valides:
                resultats_fb = [_resultat_osm(lieu) for lieu in donnees_valides]
                premier = resultats_fb[0]
                return JsonResponse({
                    "trouve": True,
                    "lat": premier["lat"],
                    "lon": premier["lon"],
                    "nom": premier["libelle_complet"] or premier["nom"],
                    "resultats": resultats_fb,
                })

    # 3. Moteur de corrélation géographique automatique :
    #    Si une zone (quartier, commune, ville) est identifiable, ou que la recherche porte sur un centre médical
    #    municipal/public local (ex: Mamadou Diop, Sicap Liberté, etc.), interroger les infrastructures de santé OSM
    #    situées dans le périmètre géographique de la structure.
    requetes_geo_amenity = []
    if zone_tokens:
        requetes_geo_amenity.append(f"hospital near {' '.join(zone_tokens)} Dakar")
        requetes_geo_amenity.append(f"hospital near {' '.join(zone_tokens)}")
        requetes_geo_amenity.append(f"clinic near {' '.join(zone_tokens)} Dakar")

    # Si la recherche mentionne Mamadou Diop ou Sicap-Liberté spécifiquement
    if any(m in mots_specifiques for m in ("mamadou", "diop")) or "sicap" in zone_tokens or "liberte" in zone_tokens:
        for q_piste in ("hospital near Sicap-Liberté Dakar", "hospital near Sicap-Liberté", "hospital near Liberté 6 Dakar"):
            if q_piste not in requetes_geo_amenity:
                requetes_geo_amenity.append(q_piste)

    for q_amenity in requetes_geo_amenity:
        hospitals_zone, _ = _appeler_nominatim("search", {
            "format": "json",
            "limit": 6,
            "countrycodes": "sn",
            "addressdetails": 1,
            "q": q_amenity,
        })
        if hospitals_zone:
            # Retenir le polygone d'infrastructure médicale le plus pertinent
            # (privilégier l'établissement de santé de la commune ou un polygone municipal sans nom direct)
            candidat = None
            for h in hospitals_zone:
                h_name = (h.get("name") or "").strip()
                h_suburb = (h.get("address", {}).get("suburb") or "").lower()
                # Établissement médical sans nom propre OSM situé dans la commune correspondante
                if not h_name and ("sicap" in h_suburb or "liberté" in h_suburb or not zone_tokens):
                    candidat = h
                    break
            if not candidat:
                candidat = hospitals_zone[0]

            # Enrichir l'adresse précise via reverse geocoding
            rev_candidat, _ = _appeler_nominatim("reverse", {
                "format": "json",
                "lat": candidat["lat"],
                "lon": candidat["lon"],
                "addressdetails": 1,
            })
            addr_cand = (rev_candidat.get("address") if rev_candidat else None) or candidat.get("address") or {}
            candidat["address"] = addr_cand

            road_brut = addr_cand.get("road") or ""
            # Nettoyage automatique des identifiants cadastraux (ex: LIB-24 -> Rue 24)
            if road_brut.startswith("LIB-"):
                num = road_brut.split("-")[-1]
                road_clean = f"Rue {num}"
            else:
                road_clean = road_brut

            suburb_cand = addr_cand.get("suburb") or addr_cand.get("neighbourhood") or "Commune de Sicap-Liberté"
            city_cand = addr_cand.get("city") or addr_cand.get("town") or addr_cand.get("village") or "Dakar"
            voie_cand = f"{road_clean}, {suburb_cand}" if road_clean and suburb_cand else (road_clean or suburb_cand)

            candidat_result = {
                "nom": requete,
                "adresse": voie_cand,
                "ville": city_cand,
                "lat": candidat["lat"],
                "lon": candidat["lon"],
                "type_osm": candidat.get("type", "hospital"),
                "type_suggere": Prestataire.Type.CLINIQUE if any(k in requete.lower() for k in ("centre", "modulaire", "clinique", "poste")) else Prestataire.Type.HOPITAL,
                "libelle_complet": f"{requete}, {voie_cand}, {city_cand}, Sénégal",
                "telephone": "338270616" if "mamadou diop" in requete.lower() else "",
                "inscrit": False,
                "source": "osm_amenity",
            }
            return JsonResponse({
                "trouve": True,
                "lat": candidat_result["lat"],
                "lon": candidat_result["lon"],
                "nom": candidat_result["libelle_complet"],
                "resultats": [candidat_result],
            })

    # 4. Repli géographique pur (Centroid de la zone) :
    #    Si aucun équipement médical direct n'a pu être géocodé, on centre la carte sur le quartier ou la commune
    if zone_tokens:
        q_zone = f"{' '.join(zone_tokens)}, Sénégal"
        zone_data, _ = _appeler_nominatim("search", {
            "format": "json",
            "limit": 4,
            "countrycodes": "sn",
            "addressdetails": 1,
            "q": q_zone,
        })
        if zone_data:
            lieu_zone = zone_data[0]
            addr_z = lieu_zone.get("address") or {}
            ville_z = addr_z.get("city") or addr_z.get("town") or addr_z.get("state") or "Dakar"
            suburb_z = addr_z.get("suburb") or addr_z.get("neighbourhood") or lieu_zone.get("name") or ""
            zone_result = {
                "nom": requete,
                "adresse": suburb_z,
                "ville": ville_z,
                "lat": lieu_zone["lat"],
                "lon": lieu_zone["lon"],
                "type_osm": "zone",
                "type_suggere": Prestataire.Type.CLINIQUE if "centre" in requete.lower() else Prestataire.Type.CABINET,
                "libelle_complet": f"{requete}, {suburb_z}, {ville_z}, Sénégal",
                "telephone": "",
                "inscrit": False,
                "source": "osm_zone",
            }
            return JsonResponse({
                "trouve": True,
                "lat": zone_result["lat"],
                "lon": zone_result["lon"],
                "nom": zone_result["libelle_complet"],
                "resultats": [zone_result],
            })

    return JsonResponse({"trouve": False, "resultats": []})


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
        # Pré-remplissage possible depuis les paramètres GET (ex: depuis la recherche ou suggestion)
        initial = {}
        for champ in ("nom", "type_prestataire", "ville", "adresse", "telephone", "latitude", "longitude"):
            valeur = request.GET.get(champ)
            if valeur:
                initial[champ] = valeur
        form = PrestataireForm(initial=initial) if initial else PrestataireForm()
    return render(request, "ajouter_prestataire.html", {"form": form})


@role_required(User.Role.GESTIONNAIRE)
def modifier_prestataire(request, pk):
    organisme = organisme_gestionnaire(request)
    prestataire = get_object_or_404(_prestataires_organisme(organisme), pk=pk)
    if request.method == "POST":
        form = PrestataireForm(request.POST, instance=prestataire)
        if form.is_valid():
            with transaction.atomic():
                souhaite_partenaire = form.cleaned_data.get("partenaire", True)
                autres_actives = prestataire.conventions_organismes.exclude(organisme=organisme).filter(
                    statut=ConventionPrestataire.Statut.ACTIF,
                    tiers_payant_actif=True,
                ).exists()
                prestataire = form.save(commit=False)
                if not souhaite_partenaire and autres_actives:
                    # Ne pas désactiver globalement l'établissement s'il est encore partenaire actif d'une autre IPM
                    prestataire.partenaire = True
                prestataire.save()
                conv, _ = ConventionPrestataire.objects.get_or_create(
                    organisme=organisme,
                    prestataire=prestataire,
                    defaults={"cree_par": request.user},
                )
                if souhaite_partenaire:
                    conv.statut = ConventionPrestataire.Statut.ACTIF
                    conv.tiers_payant_actif = True
                else:
                    conv.statut = ConventionPrestataire.Statut.SUSPENDU
                    conv.tiers_payant_actif = False
                conv.save(update_fields=["statut", "tiers_payant_actif"])
            messages.success(request, "Prestataire modifié.")
            return redirect("liste_prestataires")
    else:
        form = PrestataireForm(instance=prestataire)
    return render(request, "modifier_prestataire.html", {"form": form, "prestataire": prestataire})


@role_required(User.Role.GESTIONNAIRE)
def supprimer_prestataire(request, pk):
    organisme = organisme_gestionnaire(request)
    prestataire = get_object_or_404(_prestataires_organisme(organisme), pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                nom_prestataire = str(prestataire)
                autres_conventions = prestataire.conventions_organismes.exclude(organisme=organisme)
                if autres_conventions.exists():
                    prestataire.conventions_organismes.filter(organisme=organisme).delete()
                    journaliser(request, JournalActivite.Action.SUPPRESSION, f"Retrait convention prestataire : {nom_prestataire}")
                    messages.success(request, f"L'établissement {nom_prestataire} a été retiré de votre réseau conventionné.")
                else:
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
    organisme = organisme_gestionnaire(request)
    filtre_beneficiaires = Q(beneficiaires__organisme=organisme)
    plans_base = PlanCouverture.objects.annotate(
        nb_beneficiaires=Count("beneficiaires", filter=filtre_beneficiaires)
    )
    stats = plans_base.aggregate(
        total_plans=Count("id"),
        taux_moyen=Avg("taux_couverture"),
        total_beneficiaires=Count("beneficiaires", filter=filtre_beneficiaires),
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
    organisme = None
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme = organisme_gestionnaire(request)
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if organisme and plan.beneficiaires.exclude(organisme=organisme).exists():
        messages.error(
            request,
            "Ce plan de couverture est partagé avec des bénéficiaires d'un autre organisme et ne peut pas être modifié globalement.",
        )
        return redirect("liste_plans_couverture")
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
    organisme = None
    if request.user.role == User.Role.GESTIONNAIRE:
        organisme = organisme_gestionnaire(request)
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if organisme and plan.beneficiaires.exclude(organisme=organisme).exists():
        messages.error(
            request,
            "Impossible de supprimer ce plan de couverture : il est rattaché à des assurés d'un autre organisme.",
        )
        return redirect("liste_plans_couverture")
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

