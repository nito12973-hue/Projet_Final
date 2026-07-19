# Carte de proximité des prestataires — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre à un assuré de voir, sur une carte, les prestataires partenaires les plus proches de sa position et de prendre rendez-vous directement avec l'un d'eux ; permettre à l'admin de positionner chaque prestataire en cliquant sur une carte.

**Architecture:** Deux champs `latitude`/`longitude` nullable ajoutés à `Prestataire`. L'admin les renseigne en cliquant sur une mini-carte Leaflet dans les formulaires prestataire existants. Un nouvel écran Assuré demande la géolocalisation du navigateur, envoie les coordonnées au serveur en query params, le serveur trie les prestataires par distance (haversine, calcul Python pur) et renvoie une liste + une carte Leaflet. Chaque prestataire de la liste ouvre le formulaire de rendez-vous existant, pré-rempli.

**Tech Stack:** Django (vues/formulaires/templates existants), Leaflet.js 1.9.4 + tuiles OpenStreetMap (CDN, licence libre, aucune clé API), JavaScript vanilla (aucune dépendance ajoutée au projet, cohérent avec le reste de l'app).

## Global Constraints

- Une seule app Django (`Plateform_medicale`), pas de nouvelle app. Voir CLAUDE.md.
- Réutiliser les classes CSS existantes (`.panel`, `.avis`/`.avis-attente`, `.button`/`.primary`, `.erreurs`/`.erreurs-formulaire`) — ne pas dupliquer de style inline pour ce qui existe déjà.
- Réutiliser une icône existante du dict `_ICONES` avant d'en ajouter une nouvelle (`map-pin` existe déjà — voir `Plateform_medicale/templatetags/icones.py`).
- Aucun émoji nulle part dans l'application.
- CDN externe : toujours avec `integrity` (SRI) + `crossorigin`, comme Chart.js dans `rapports.html`.
- Seuls les prestataires `partenaire=True` doivent apparaître dans les écrans orientés Assuré (cohérent avec `RendezVousAssureForm` existant).
- `python manage.py test Plateform_medicale` doit rester vert après chaque tâche.
- Commits séparés par tâche, jamais de commit combinant plusieurs tâches.

---

### Task 1: Modèle — coordonnées du prestataire et calcul de distance

**Files:**
- Modify: `Plateform_medicale/models.py:1-16` (imports + helper), `Plateform_medicale/models.py:162-165` (modèle `Prestataire`)
- Test: `Plateform_medicale/tests.py` (nouvelle classe, insérée après `AdminPrestatairesTests`, actuellement ligne 787)
- Create: migration via `python manage.py makemigrations`

**Interfaces:**
- Produces: `Prestataire.latitude` (DecimalField, `max_digits=9`, `decimal_places=6`, `null=True`, `blank=True`), `Prestataire.longitude` (idem). `distance_km(lat1, lon1, lat2, lon2) -> float` dans `Plateform_medicale/models.py`, distance en kilomètres, fonction pure sans accès base de données.

- [ ] **Step 1: Écrire le test qui échoue pour `distance_km`**

Dans `Plateform_medicale/tests.py`, insérer après la ligne 787 (juste avant `class AdminPharmaciensTests(TestCase):`) :

```python
class DistanceKmTests(TestCase):
    def test_meme_point_distance_nulle(self):
        self.assertEqual(distance_km(14.6928, -17.4467, 14.6928, -17.4467), 0)

    def test_un_degre_de_latitude(self):
        resultat = distance_km(0, 0, 1, 0)
        self.assertAlmostEqual(resultat, 111.19, delta=0.5)

    def test_un_degre_de_longitude_a_l_equateur(self):
        resultat = distance_km(0, 0, 0, 1)
        self.assertAlmostEqual(resultat, 111.19, delta=0.5)


```

Ajouter `distance_km` à l'import existant en haut de `tests.py` :

```python
from .models import (
    Consultation,
    Delivrance,
    Medecin,
    Notification,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
    distance_km,
)
```

(remplace le bloc d'import `from .models import (...)` existant — ajoute uniquement `distance_km,` avant la parenthèse fermante, en gardant tous les noms déjà présents).

- [ ] **Step 2: Lancer le test pour verifier qu'il echoue**

Run: `python manage.py test Plateform_medicale.tests.DistanceKmTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'distance_km' from 'Plateform_medicale.models'`

- [ ] **Step 3: Implementer `distance_km` et les champs du modele**

Dans `Plateform_medicale/models.py`, remplacer les imports en tête de fichier :

```python
import io
import uuid
from math import atan2, cos, radians, sin, sqrt

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

valider_telephone = RegexValidator(
    regex=r'^\+?[0-9 \-]{7,20}$',
    message="Numero de telephone invalide (chiffres, espaces, tirets et + uniquement).",
)


def distance_km(lat1, lon1, lat2, lon2):
    """Distance a vol d'oiseau entre deux points, en kilometres (formule de haversine)."""
    rayon_terre_km = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return rayon_terre_km * 2 * atan2(sqrt(a), sqrt(1 - a))
```

Puis, dans la classe `Prestataire`, remplacer :

```python
    partenaire = models.BooleanField(
        "partenaire actif", default=True, help_text="Fait partie du reseau conventionne."
    )
    date_conventionnement = models.DateField(null=True, blank=True)
```

par :

```python
    partenaire = models.BooleanField(
        "partenaire actif", default=True, help_text="Fait partie du reseau conventionne."
    )
    date_conventionnement = models.DateField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Renseignee en placant un point sur la carte (formulaire prestataire).",
    )
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
```

- [ ] **Step 4: Generer et appliquer la migration**

Run: `python manage.py makemigrations Plateform_medicale`
Expected: Un nouveau fichier `Plateform_medicale/migrations/0009_xxxxx.py` est cree (le nom exact depend de la version de Django — verifier avec `ls Plateform_medicale/migrations/` que le fichier existe et ajoute bien `latitude`/`longitude` a `Prestataire`).

Run: `python manage.py migrate Plateform_medicale`
Expected: `Applying Plateform_medicale.0009_xxxxx... OK`

- [ ] **Step 5: Lancer le test pour verifier qu'il passe**

Run: `python manage.py test Plateform_medicale.tests.DistanceKmTests -v 2`
Expected: `Ran 3 tests ... OK`

- [ ] **Step 6: Verification globale et commit**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (tous les tests existants + les 3 nouveaux passent)

```bash
git add Plateform_medicale/models.py Plateform_medicale/tests.py Plateform_medicale/migrations/
git commit -m "feat(prestataires): coordonnees GPS + calcul de distance haversine"
```

---

### Task 2: Formulaire Prestataire — champs latitude/longitude

**Files:**
- Modify: `Plateform_medicale/forms.py:318-327` (`PrestataireForm`)
- Test: `Plateform_medicale/tests.py` (dans `DistanceKmTests` ou nouvelle classe juste apres)

**Interfaces:**
- Consumes: `Prestataire.latitude`/`longitude` (Task 1).
- Produces: `PrestataireForm` accepte et sauvegarde `latitude`/`longitude` ; ces deux champs sont rendus avec `forms.HiddenInput()` (donc `field.is_hidden` vaut `True` pour eux — utilise par Task 3). Les ids HTML generes par Django restent les ids par defaut : `id_latitude`, `id_longitude`.

- [ ] **Step 1: Ecrire le test qui echoue**

Ajouter dans `Plateform_medicale/tests.py`, juste apres la classe `DistanceKmTests` (avant `class AdminPharmaciensTests`) :

```python
class PrestataireCoordonneesTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_creation_prestataire_avec_coordonnees(self):
        response = self.client.post(reverse('ajouter_prestataire'), {
            'nom': 'Hopital Principal', 'type_prestataire': 'HOPITAL',
            'adresse': 'Dakar', 'ville': 'Dakar', 'telephone': '338000001',
            'partenaire': 'on', 'date_conventionnement': '',
            'latitude': '14.6928', 'longitude': '-17.4467',
        })
        self.assertRedirects(response, reverse('liste_prestataires'))
        prestataire = Prestataire.objects.get(nom='Hopital Principal')
        self.assertAlmostEqual(float(prestataire.latitude), 14.6928, places=4)
        self.assertAlmostEqual(float(prestataire.longitude), -17.4467, places=4)

    def test_creation_prestataire_sans_coordonnees_reste_valide(self):
        response = self.client.post(reverse('ajouter_prestataire'), {
            'nom': 'Cabinet Sans Pin', 'type_prestataire': 'CABINET',
            'adresse': '', 'ville': '', 'telephone': '',
            'partenaire': 'on', 'date_conventionnement': '',
            'latitude': '', 'longitude': '',
        })
        self.assertRedirects(response, reverse('liste_prestataires'))
        prestataire = Prestataire.objects.get(nom='Cabinet Sans Pin')
        self.assertIsNone(prestataire.latitude)
        self.assertIsNone(prestataire.longitude)
```

- [ ] **Step 2: Lancer le test pour verifier qu'il echoue**

Run: `python manage.py test Plateform_medicale.tests.PrestataireCoordonneesTests -v 2`
Expected: FAIL — le premier test echoue sur `Prestataire.objects.get(nom='Hopital Principal')` (le champ `latitude` n'est pas encore accepte par le formulaire, donc non sauvegarde) ou une erreur de validation de formulaire.

- [ ] **Step 3: Implementer**

Dans `Plateform_medicale/forms.py`, remplacer :

```python
class PrestataireForm(forms.ModelForm):
    """Creation/modification d'un prestataire de sante partenaire (par l'administrateur)."""

    class Meta:
        model = Prestataire
        fields = ['nom', 'type_prestataire', 'adresse', 'ville', 'telephone', 'partenaire', 'date_conventionnement']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'date_conventionnement': forms.DateInput(attrs={'type': 'date'}),
        }
```

par :

```python
class PrestataireForm(forms.ModelForm):
    """Creation/modification d'un prestataire de sante partenaire (par l'administrateur)."""

    class Meta:
        model = Prestataire
        fields = [
            'nom', 'type_prestataire', 'adresse', 'ville', 'telephone',
            'partenaire', 'date_conventionnement', 'latitude', 'longitude',
        ]
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'date_conventionnement': forms.DateInput(attrs={'type': 'date'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
```

- [ ] **Step 4: Lancer le test pour verifier qu'il passe**

Run: `python manage.py test Plateform_medicale.tests.PrestataireCoordonneesTests -v 2`
Expected: `Ran 2 tests ... OK`

- [ ] **Step 5: Verifier que les tests prestataire existants passent toujours**

Run: `python manage.py test Plateform_medicale.tests.AdminPrestatairesTests -v 2`
Expected: `Ran 3 tests ... OK` (ces tests ne postent pas `latitude`/`longitude` — les champs etant facultatifs, ils doivent continuer a passer sans modification)

- [ ] **Step 6: Commit**

```bash
git add Plateform_medicale/forms.py Plateform_medicale/tests.py
git commit -m "feat(prestataires): formulaire accepte latitude/longitude (champs caches)"
```

---

### Task 3: Carte Leaflet pour placer le pin (formulaires admin)

**Files:**
- Modify: `Plateform_medicale/templates/ajouter_prestataire.html` (fichier complet, 27 lignes)
- Modify: `Plateform_medicale/templates/modifier_prestataire.html` (fichier complet, 26 lignes)

**Interfaces:**
- Consumes: `PrestataireForm` avec champs caches `id_latitude`/`id_longitude` (Task 2).
- Produces: aucune nouvelle interface Python — modification visuelle uniquement. Les deux templates utilisent le meme bloc CSS/JS Leaflet (duplique intentionnellement, ces deux fichiers n'ont pas de template partiel commun dans ce projet — voir CLAUDE.md, "Templates a plat, pas de sous-dossier par app").

- [ ] **Step 1: Remplacer `ajouter_prestataire.html`**

Remplacer tout le contenu de `Plateform_medicale/templates/ajouter_prestataire.html` par :

```html
{% extends "base.html" %}

{% block title %}Ajouter un prestataire{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Ajouter un prestataire</h1>
        <p class="subtitle">Hopital, clinique, pharmacie ou cabinet medical.</p>
    </div>
    <a class="button" href="{% url 'liste_prestataires' %}">Retour</a>
</section>

{% if form.non_field_errors %}
<div class="erreurs-formulaire">{{ form.non_field_errors }}</div>
{% endif %}

<form method="post">
    {% csrf_token %}
    {% for field in form %}
    {% if not field.is_hidden %}<label for="{{ field.id_for_label }}">{{ field.label }}</label>{% endif %}
    {{ field }}
    {% if field.errors %}<div class="erreurs">{{ field.errors }}</div>{% endif %}
    {% endfor %}

    <label>Emplacement sur la carte (facultatif)</label>
    <div id="carte-prestataire" style="height: 320px; border-radius: 12px; margin-bottom: 8px;"></div>
    <p class="subtitle" style="margin-top:0;margin-bottom:16px;">Cliquez sur la carte pour placer le prestataire.</p>

    <button class="button primary" type="submit">Enregistrer</button>
</form>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
    (function () {
        var DAKAR = [14.6928, -17.4467];
        var latInit = "{{ form.latitude.value|default_if_none:'' }}";
        var lngInit = "{{ form.longitude.value|default_if_none:'' }}";
        var lat = latInit ? parseFloat(latInit) : null;
        var lng = lngInit ? parseFloat(lngInit) : null;

        var champLatitude = document.getElementById('id_latitude');
        var champLongitude = document.getElementById('id_longitude');

        var carte = L.map('carte-prestataire').setView((lat && lng) ? [lat, lng] : DAKAR, 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(carte);

        var marqueur = (lat && lng) ? L.marker([lat, lng]).addTo(carte) : null;

        carte.on('click', function (evenement) {
            var position = evenement.latlng;
            if (marqueur) {
                marqueur.setLatLng(position);
            } else {
                marqueur = L.marker(position).addTo(carte);
            }
            champLatitude.value = position.lat.toFixed(6);
            champLongitude.value = position.lng.toFixed(6);
        });
    })();
</script>
{% endblock %}
```

- [ ] **Step 2: Remplacer `modifier_prestataire.html`**

Remplacer tout le contenu de `Plateform_medicale/templates/modifier_prestataire.html` par :

```html
{% extends "base.html" %}

{% block title %}Modifier {{ prestataire.nom }}{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Modifier {{ prestataire.nom }}</h1>
    </div>
    <a class="button" href="{% url 'liste_prestataires' %}">Retour</a>
</section>

{% if form.non_field_errors %}
<div class="erreurs-formulaire">{{ form.non_field_errors }}</div>
{% endif %}

<form method="post">
    {% csrf_token %}
    {% for field in form %}
    {% if not field.is_hidden %}<label for="{{ field.id_for_label }}">{{ field.label }}</label>{% endif %}
    {{ field }}
    {% if field.errors %}<div class="erreurs">{{ field.errors }}</div>{% endif %}
    {% endfor %}

    <label>Emplacement sur la carte (facultatif)</label>
    <div id="carte-prestataire" style="height: 320px; border-radius: 12px; margin-bottom: 8px;"></div>
    <p class="subtitle" style="margin-top:0;margin-bottom:16px;">Cliquez sur la carte pour placer ou deplacer le prestataire.</p>

    <button class="button primary" type="submit">Enregistrer</button>
</form>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
    (function () {
        var DAKAR = [14.6928, -17.4467];
        var latInit = "{{ form.latitude.value|default_if_none:'' }}";
        var lngInit = "{{ form.longitude.value|default_if_none:'' }}";
        var lat = latInit ? parseFloat(latInit) : null;
        var lng = lngInit ? parseFloat(lngInit) : null;

        var champLatitude = document.getElementById('id_latitude');
        var champLongitude = document.getElementById('id_longitude');

        var carte = L.map('carte-prestataire').setView((lat && lng) ? [lat, lng] : DAKAR, 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(carte);

        var marqueur = (lat && lng) ? L.marker([lat, lng]).addTo(carte) : null;

        carte.on('click', function (evenement) {
            var position = evenement.latlng;
            if (marqueur) {
                marqueur.setLatLng(position);
            } else {
                marqueur = L.marker(position).addTo(carte);
            }
            champLatitude.value = position.lat.toFixed(6);
            champLongitude.value = position.lng.toFixed(6);
        });
    })();
</script>
{% endblock %}
```

- [ ] **Step 3: Verifier que les pages se chargent (test Django, pas de rendu JS)**

Run: `python manage.py test Plateform_medicale.tests.AdminPrestatairesTests Plateform_medicale.tests.PrestataireCoordonneesTests -v 2`
Expected: `OK` (ces tests postent sur les vues, ils ne verifient pas le rendu HTML du template en detail mais confirment que le template ne casse pas le rendu — un `TemplateSyntaxError` ferait echouer ces tests avec une erreur 500)

- [ ] **Step 4: Verification manuelle (obligatoire, JS non teste automatiquement)**

Run: `python manage.py runserver`

Se connecter en admin, aller sur "Prestataires" → "Ajouter un prestataire" : verifier que la carte s'affiche centree sur Dakar, qu'un clic pose un marqueur, et qu'apres soumission le prestataire cree a bien ses coordonnees (verifiable dans le Django admin ou en rouvrant "Modifier" sur ce prestataire — le marqueur doit apparaitre a la position enregistree).

- [ ] **Step 5: Commit**

```bash
git add Plateform_medicale/templates/ajouter_prestataire.html Plateform_medicale/templates/modifier_prestataire.html
git commit -m "feat(prestataires): carte Leaflet pour positionner le prestataire (admin)"
```

---

### Task 4: Écran Assuré "Prestataires proches"

**Files:**
- Modify: `Plateform_medicale/urls.py:85-86`
- Modify: `Plateform_medicale/views.py` (nouvelle vue, section "Espace Assure")
- Modify: `Plateform_medicale/templates/base.html:970-971` (nav Assure)
- Create: `Plateform_medicale/templates/prestataires_proches.html`
- Test: `Plateform_medicale/tests.py` (nouvelle classe)

**Interfaces:**
- Consumes: `distance_km` et `Prestataire.latitude`/`longitude`/`partenaire` (Task 1).
- Produces: URL nommee `prestataires_proches` (`GET /assure/prestataires-proches/`, params optionnels `lat`, `lng`), vue `views.prestataires_proches`, template `prestataires_proches.html`.

- [ ] **Step 1: Ecrire les tests qui echouent**

`ImportUtilisateursExcelTests` (ligne 1497 au moment de ce plan) est la derniere classe du fichier (1597 lignes au total). Ajouter la nouvelle classe tout a la fin de `Plateform_medicale/tests.py`, apres la derniere ligne existante :

```python
class PrestatairesProchesTests(TestCase):
    def setUp(self):
        self.utilisateur = creer_utilisateur(User.Role.ASSURE, 'assure1@santesn.sn')
        self.client.login(username='assure1@santesn.sn', password=PASSWORD)
        self.proche = Prestataire.objects.create(
            nom='Clinique Proche', type_prestataire='CLINIQUE', partenaire=True,
            ville='Dakar', latitude=Decimal('14.6928'), longitude=Decimal('-17.4467'),
        )
        self.loin = Prestataire.objects.create(
            nom='Hopital Lointain', type_prestataire='HOPITAL', partenaire=True,
            ville='Saint-Louis', latitude=Decimal('16.0179'), longitude=Decimal('-16.4896'),
        )
        self.sans_coordonnees = Prestataire.objects.create(
            nom='Cabinet Sans Pin', type_prestataire='CABINET', partenaire=True, ville='Dakar',
        )
        self.non_partenaire = Prestataire.objects.create(
            nom='Ancien Partenaire', type_prestataire='CLINIQUE', partenaire=False,
            ville='Dakar', latitude=Decimal('14.70'), longitude=Decimal('-17.44'),
        )

    def test_interdit_aux_non_assures(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('prestataires_proches'))
        self.assertEqual(response.status_code, 403)

    def test_sans_localisation_liste_non_triee(self):
        response = self.client.get(reverse('prestataires_proches'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['localisation_active'])
        noms = [p.nom for p, distance in response.context['prestataires_tries']]
        self.assertIn('Clinique Proche', noms)
        self.assertIn('Hopital Lointain', noms)

    def test_avec_localisation_tri_par_distance(self):
        response = self.client.get(reverse('prestataires_proches'), {'lat': '14.6928', 'lng': '-17.4467'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['localisation_active'])
        resultats = response.context['prestataires_tries']
        self.assertEqual(resultats[0][0], self.proche)
        self.assertEqual(resultats[1][0], self.loin)
        self.assertLess(resultats[0][1], resultats[1][1])

    def test_prestataire_sans_coordonnees_affiche_a_part(self):
        response = self.client.get(reverse('prestataires_proches'))
        noms_tries = [p.nom for p, distance in response.context['prestataires_tries']]
        self.assertNotIn('Cabinet Sans Pin', noms_tries)
        noms_sans_coordonnees = [p.nom for p in response.context['prestataires_sans_coordonnees']]
        self.assertIn('Cabinet Sans Pin', noms_sans_coordonnees)

    def test_prestataire_non_partenaire_absent(self):
        response = self.client.get(reverse('prestataires_proches'))
        noms_tries = [p.nom for p, distance in response.context['prestataires_tries']]
        noms_sans_coordonnees = [p.nom for p in response.context['prestataires_sans_coordonnees']]
        self.assertNotIn('Ancien Partenaire', noms_tries)
        self.assertNotIn('Ancien Partenaire', noms_sans_coordonnees)

    def test_lat_lng_invalides_ignores(self):
        response = self.client.get(reverse('prestataires_proches'), {'lat': 'abc', 'lng': 'def'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['localisation_active'])
```

Verifier que `Decimal` est deja importe en tete de `tests.py` (c'est le cas : `from decimal import Decimal` existe deja ligne 3).

- [ ] **Step 2: Lancer les tests pour verifier qu'ils echouent**

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'prestataires_proches' not found`

- [ ] **Step 3: Ajouter la route**

Dans `Plateform_medicale/urls.py`, remplacer :

```python
    path('assure/ayants-droit/<int:pk>/supprimer/', views.supprimer_ayant_droit, name='supprimer_ayant_droit'),
    path('assure/rendez-vous/', views.mes_rendez_vous_assure, name='mes_rendez_vous_assure'),
```

par :

```python
    path('assure/ayants-droit/<int:pk>/supprimer/', views.supprimer_ayant_droit, name='supprimer_ayant_droit'),
    path('assure/prestataires-proches/', views.prestataires_proches, name='prestataires_proches'),
    path('assure/rendez-vous/', views.mes_rendez_vous_assure, name='mes_rendez_vous_assure'),
```

- [ ] **Step 4: Ajouter la vue**

Dans `Plateform_medicale/views.py`, ajouter la vue suivante juste avant `def dashboard_assure(request):` (apres les helpers `_patient_principal`/`_beneficiaires`, section "Espace Assure") :

```python
@role_required(User.Role.ASSURE)
def prestataires_proches(request):
    prestataires_partenaires = Prestataire.objects.filter(partenaire=True)
    avec_coordonnees = prestataires_partenaires.filter(
        latitude__isnull=False, longitude__isnull=False
    )
    sans_coordonnees = prestataires_partenaires.filter(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    ).order_by("ville", "nom")

    lat_param = request.GET.get("lat")
    lng_param = request.GET.get("lng")
    lat_utilisateur = lng_utilisateur = None
    if lat_param and lng_param:
        try:
            lat_utilisateur = float(lat_param)
            lng_utilisateur = float(lng_param)
        except ValueError:
            lat_utilisateur = lng_utilisateur = None
    localisation_active = lat_utilisateur is not None and lng_utilisateur is not None

    if localisation_active:
        prestataires_tries = sorted(
            (
                (prestataire, round(distance_km(
                    lat_utilisateur, lng_utilisateur,
                    float(prestataire.latitude), float(prestataire.longitude),
                ), 1))
                for prestataire in avec_coordonnees
            ),
            key=lambda item: item[1],
        )
    else:
        prestataires_tries = [
            (prestataire, None)
            for prestataire in avec_coordonnees.order_by("ville", "nom")
        ]

    prestataires_geojson = [
        {
            "nom": prestataire.nom,
            "type": prestataire.get_type_prestataire_display(),
            "ville": prestataire.ville,
            "latitude": float(prestataire.latitude),
            "longitude": float(prestataire.longitude),
        }
        for prestataire in avec_coordonnees
    ]

    return render(request, "prestataires_proches.html", {
        "prestataires_tries": prestataires_tries,
        "prestataires_sans_coordonnees": sans_coordonnees,
        "prestataires_geojson": prestataires_geojson,
        "localisation_active": localisation_active,
    })
```

Dans `Plateform_medicale/views.py`, `distance_km` doit être importé depuis `.models`. Remplacer le bloc d'import existant :

```python
from .models import (
    Consultation,
    Delivrance,
    Medecin,
    Notification,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
    valider_telephone,
)
```

par :

```python
from .models import (
    Consultation,
    Delivrance,
    Medecin,
    Notification,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
    distance_km,
    valider_telephone,
)
```

- [ ] **Step 5: Creer le template**

Creer `Plateform_medicale/templates/prestataires_proches.html` :

```html
{% extends "base.html" %}

{% block title %}Prestataires proches{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Prestataires proches</h1>
        <p class="subtitle">
            {% if localisation_active %}
            Prestataires du reseau tries du plus proche au plus loin de votre position.
            {% else %}
            Liste complete du reseau partenaire, triee par ville.
            {% endif %}
        </p>
    </div>
</section>

{% if not localisation_active %}
<div class="avis avis-attente">
    <p class="avis-titre">Localisation non activee</p>
    <p>Autorisez la geolocalisation dans votre navigateur pour trier les prestataires du plus proche au plus loin.</p>
</div>
{% endif %}

<div id="carte-prestataires-proches" style="height: 360px; border-radius: 14px; margin-bottom: 20px;"></div>

<section class="admin-layout">
    {% for prestataire, distance in prestataires_tries %}
    <article class="panel" style="padding: 18px;">
        <h2 style="margin-top:0;">{{ prestataire.nom }}</h2>
        <p class="subtitle">{{ prestataire.get_type_prestataire_display }} - {{ prestataire.ville }}</p>
        {% if distance is not None %}
        <p><strong>{{ distance }} km</strong></p>
        {% endif %}
        <a class="button primary" href="{% url 'ajouter_rendez_vous_assure' %}?prestataire={{ prestataire.pk }}">Prendre rendez-vous</a>
    </article>
    {% empty %}
    <p class="subtitle">Aucun prestataire du reseau n'a encore de position enregistree.</p>
    {% endfor %}
</section>

{% if prestataires_sans_coordonnees %}
<section class="panel" style="margin-top: 20px; padding: 20px;">
    <h2 style="margin-top:0;">Autres prestataires du reseau</h2>
    <p class="subtitle">Localisation non renseignee, non affiches sur la carte.</p>
    <ul>
        {% for prestataire in prestataires_sans_coordonnees %}
        <li>{{ prestataire.nom }} ({{ prestataire.get_type_prestataire_display }}, {{ prestataire.ville }}) —
            <a href="{% url 'ajouter_rendez_vous_assure' %}?prestataire={{ prestataire.pk }}">Prendre rendez-vous</a></li>
        {% endfor %}
    </ul>
</section>
{% endif %}

{{ prestataires_geojson|json_script:"donnees-prestataires-proches" }}

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
    (function () {
        var DAKAR = [14.6928, -17.4467];
        var donnees = JSON.parse(document.getElementById('donnees-prestataires-proches').textContent);

        var carte = L.map('carte-prestataires-proches').setView(DAKAR, 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(carte);

        donnees.forEach(function (prestataire) {
            L.marker([prestataire.latitude, prestataire.longitude])
                .addTo(carte)
                .bindPopup('<strong>' + prestataire.nom + '</strong><br>' + prestataire.type + ' - ' + prestataire.ville);
        });

        var parametres = new URLSearchParams(window.location.search);
        if (parametres.has('lat') && parametres.has('lng')) {
            var latUtilisateur = parseFloat(parametres.get('lat'));
            var lngUtilisateur = parseFloat(parametres.get('lng'));
            L.circleMarker([latUtilisateur, lngUtilisateur], {
                radius: 8, color: '#0f766e', fillColor: '#14b8a6', fillOpacity: 1,
            }).addTo(carte).bindPopup('Vous');
            carte.setView([latUtilisateur, lngUtilisateur], 12);
        } else if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function (position) {
                var url = new URL(window.location.href);
                url.searchParams.set('lat', position.coords.latitude);
                url.searchParams.set('lng', position.coords.longitude);
                window.location.href = url.toString();
            }, function () {
                // Permission refusee ou indisponible : on reste sur la liste de repli deja affichee.
            });
        }
    })();
</script>
{% endblock %}
```

- [ ] **Step 6: Ajouter l'item de menu**

Dans `Plateform_medicale/templates/base.html`, remplacer (section nav Assure, actuellement lignes 970-971) :

```html
                <a href="{% url 'liste_ayants_droit' %}" title="Mes ayants droit" class="{% if url_name == 'liste_ayants_droit' or url_name == 'ajouter_ayant_droit' or url_name == 'modifier_ayant_droit' %}active{% endif %}">{% icone "users" %} <span class="nav-texte">Mes ayants droit</span></a>
                <a href="{% url 'mes_rendez_vous_assure' %}" title="Mes rendez-vous" class="{% if url_name == 'mes_rendez_vous_assure' or url_name == 'ajouter_rendez_vous_assure' %}active{% endif %}">{% icone "calendar" %} <span class="nav-texte">Mes rendez-vous</span></a>
```

par :

```html
                <a href="{% url 'liste_ayants_droit' %}" title="Mes ayants droit" class="{% if url_name == 'liste_ayants_droit' or url_name == 'ajouter_ayant_droit' or url_name == 'modifier_ayant_droit' %}active{% endif %}">{% icone "users" %} <span class="nav-texte">Mes ayants droit</span></a>
                <a href="{% url 'prestataires_proches' %}" title="Prestataires proches" class="{% if url_name == 'prestataires_proches' %}active{% endif %}">{% icone "map-pin" %} <span class="nav-texte">Prestataires proches</span></a>
                <a href="{% url 'mes_rendez_vous_assure' %}" title="Mes rendez-vous" class="{% if url_name == 'mes_rendez_vous_assure' or url_name == 'ajouter_rendez_vous_assure' %}active{% endif %}">{% icone "calendar" %} <span class="nav-texte">Mes rendez-vous</span></a>
```

- [ ] **Step 7: Lancer les tests pour verifier qu'ils passent**

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests -v 2`
Expected: `Ran 6 tests ... OK`

- [ ] **Step 8: Verification globale**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK`

- [ ] **Step 9: Verification manuelle**

Run: `python manage.py runserver`, se connecter avec un compte Assure ayant complete son profil. Depuis un prestataire deja positionne via Task 3, aller sur "Prestataires proches" : accepter la demande de localisation du navigateur, verifier que la liste se re-trie et que la carte affiche un marqueur pour l'utilisateur en plus des prestataires.

- [ ] **Step 10: Commit**

```bash
git add Plateform_medicale/urls.py Plateform_medicale/views.py Plateform_medicale/templates/base.html Plateform_medicale/templates/prestataires_proches.html Plateform_medicale/tests.py
git commit -m "feat(assure): ecran Prestataires proches (carte + tri par distance)"
```

---

### Task 5: Pré-remplissage du formulaire de rendez-vous

**Files:**
- Modify: `Plateform_medicale/views.py:1617-1631` (`ajouter_rendez_vous_assure`)
- Test: `Plateform_medicale/tests.py` (dans `EspaceAssureTests`)

**Interfaces:**
- Consumes: `Prestataire` (existant), route `ajouter_rendez_vous_assure` (existante). Les liens "Prendre rendez-vous" de Task 4 pointent deja vers `ajouter_rendez_vous_assure?prestataire=<id>` — cette tache les rend fonctionnels.
- Produces: `ajouter_rendez_vous_assure` pre-selectionne le champ `prestataire` du formulaire quand `?prestataire=<id>` est present et valide.

- [ ] **Step 1: Ecrire le test qui echoue**

Dans `Plateform_medicale/tests.py`, dans la classe `EspaceAssureTests`, ajouter apres `test_creation_rendez_vous_pour_beneficiaire` :

```python
    def test_prestataire_preselectionne_depuis_le_lien(self):
        patient = self._completer_profil()
        prestataire = Prestataire.objects.create(
            nom='Clinique Test', type_prestataire='CLINIQUE', partenaire=True,
        )
        response = self.client.get(reverse('ajouter_rendez_vous_assure'), {'prestataire': prestataire.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial.get('prestataire'), str(prestataire.pk))

    def test_prestataire_invalide_dans_lurl_est_ignore(self):
        self._completer_profil()
        response = self.client.get(reverse('ajouter_rendez_vous_assure'), {'prestataire': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('prestataire', response.context['form'].initial)
```

Verifier que `Prestataire` est deja importe en tete de `tests.py` (c'est le cas).

- [ ] **Step 2: Lancer les tests pour verifier qu'ils echouent**

Run: `python manage.py test Plateform_medicale.tests.EspaceAssureTests.test_prestataire_preselectionne_depuis_le_lien Plateform_medicale.tests.EspaceAssureTests.test_prestataire_invalide_dans_lurl_est_ignore -v 2`
Expected: FAIL sur le premier test — `response.context['form'].initial` ne contient pas `'prestataire'` (le formulaire est cree sans `initial`)

- [ ] **Step 3: Implementer**

Dans `Plateform_medicale/views.py`, remplacer :

```python
def ajouter_rendez_vous_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)

    if request.method == "POST":
        form = RendezVousAssureForm(request.POST, beneficiaires=beneficiaires)
        if form.is_valid():
            form.save()
            messages.success(request, "Demande de rendez-vous envoyee.")
            return redirect("mes_rendez_vous_assure")
    else:
        form = RendezVousAssureForm(beneficiaires=beneficiaires)
    return render(request, "ajouter_rendez_vous_assure.html", {"form": form})
```

par :

```python
def ajouter_rendez_vous_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)

    if request.method == "POST":
        form = RendezVousAssureForm(request.POST, beneficiaires=beneficiaires)
        if form.is_valid():
            form.save()
            messages.success(request, "Demande de rendez-vous envoyee.")
            return redirect("mes_rendez_vous_assure")
    else:
        initial = {}
        prestataire_id = request.GET.get("prestataire")
        if prestataire_id and prestataire_id.isdigit():
            if Prestataire.objects.filter(pk=prestataire_id, partenaire=True).exists():
                initial["prestataire"] = prestataire_id
        form = RendezVousAssureForm(beneficiaires=beneficiaires, initial=initial)
    return render(request, "ajouter_rendez_vous_assure.html", {"form": form})
```

- [ ] **Step 4: Lancer les tests pour verifier qu'ils passent**

Run: `python manage.py test Plateform_medicale.tests.EspaceAssureTests -v 2`
Expected: `OK` (tous les tests de la classe, y compris les 2 nouveaux)

- [ ] **Step 5: Verification globale finale**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` — compter le nombre total de tests, doit etre 131 (base actuelle) + 3 (Task 1) + 2 (Task 2) + 6 (Task 4) + 2 (Task 5) = 144.

- [ ] **Step 6: Verification manuelle bout-en-bout**

Run: `python manage.py runserver`. En tant qu'Assure : "Prestataires proches" → cliquer "Prendre rendez-vous" sur un prestataire → verifier que le formulaire "Nouveau rendez-vous" affiche bien ce prestataire deja selectionne dans le menu deroulant.

- [ ] **Step 7: Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/tests.py
git commit -m "feat(assure): pre-selection du prestataire dans le formulaire de rendez-vous"
```

---

## Après l'implémentation

Une fois les 5 tâches terminées : mettre à jour `FONCTIONNEMENT.txt` (nouvelle route `prestataires_proches`, nouveaux champs `Prestataire.latitude`/`longitude`) et `GUIDE_UTILISATEUR.md` (section Assuré — ajouter "Prestataires proches" à la liste des écrans, section Administrateur — mentionner le pin sur la carte lors de la création/modification d'un prestataire). Ce n'est pas une tâche du plan (pas de code), mais à ne pas oublier avant de considérer la fonctionnalité vraiment terminée (règle de documentation du projet).
