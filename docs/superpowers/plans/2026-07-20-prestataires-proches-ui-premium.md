# Prestataires proches — interface premium — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer l'écran Assuré "Prestataires proches" (déjà fonctionnel) en interface deux colonnes premium — filtres, cartes prestataires riches (icône par type, distance, temps estimé, nombre de médecins réel), carte Leaflet avec marqueurs colorés par type et popups redessinés, état vide soigné — sans toucher à la logique métier, aux URLs ni aux modèles.

**Architecture:** Un seul changement serveur (enrichir le dict `prestataires_geojson` déjà transmis au client avec 3 champs réels : `type_code`, `telephone`, `medecin_count`). Tout le reste — filtrage, tri, rendu de la liste, rendu des marqueurs, popups — est réécrit côté client dans `prestataires_proches.html`, en étendant le pipeline JS de suivi de position en direct déjà en place (`watchPosition`) plutôt qu'en le dupliquant.

**Tech Stack:** Django (vue existante, changement minimal), Leaflet.js 1.9.4 (déjà en place), JavaScript vanilla (aucune dépendance ajoutée), CSS du design system existant (`.panel`, `.button`, `.filtres`, `.dash-stat-icon`, palette navy/turquoise) — pas de Bootstrap.

## Global Constraints

- Aucune nouvelle route, aucune nouvelle vue, aucun nouveau modèle. Le seul changement de `views.py` est l'enrichissement du dict `prestataires_geojson` (3 clés ajoutées, toutes des données déjà en base).
- Pas de Bootstrap ni de Bootstrap Icons — réutiliser les classes CSS existantes (`.panel`, `.button`/`.primary`/`.btn-sm`, `.filtres`, `.dash-stat-icon`, `.avis`/`.avis-attente`) et le système d'icônes existant (`templatetags/icones.py`, dict `_ICONES` : `building`, `stethoscope`, `pill`, `map-pin`).
- Aucun émoji nulle part.
- Aucune donnée fictive : pas de note/étoiles, pas de statut Ouvert/Fermé, pas de filtre "Ouvert actuellement" ni "Disponible aujourd'hui". Seules des données réelles sont affichées (nom, type, ville, distance calculée, temps estimé clairement affiché comme estimation, nombre de médecins réel via `prestataire.medecins.count()`).
- CDN externe (Leaflet, déjà en place) : toujours avec `integrity` (SRI) + `crossorigin`.
- Tout contenu construit dans le DOM à partir de données stockées en base (nom, ville, téléphone d'un prestataire) doit passer par `createElement`/`textContent`, jamais par de la concaténation de chaînes HTML (`innerHTML` avec des données utilisateur) — règle anti-XSS déjà appliquée aux popups existants. Exception explicite et volontaire : le contenu des icônes SVG lues depuis le bloc `#icones-types-source` (Task 3) est une source fixe et fiable (rendue par `{% icone %}` côté serveur, jamais dérivée de données stockées) — l'assigner via `innerHTML` y est sûr et justifié, contrairement aux champs `nom`/`ville`/`telephone` d'un prestataire.
- `python manage.py test Plateform_medicale` doit rester vert après chaque tâche (144 tests actuels + 1 nouveau test à la Task 1 = 145).
- Commits séparés par tâche, jamais de commit combinant plusieurs tâches.
- Aucun test Python n'est attendu pour le comportement JS lui-même (filtrage, tri live, rendu des cartes/marqueurs) — cohérent avec le suivi de position en direct déjà livré et documenté ainsi dans `FONCTIONNEMENT.txt`. Chaque tâche JS se vérifie par `python manage.py check` (le template ne doit pas lever de `TemplateSyntaxError`) + vérification manuelle obligatoire (`runserver`).

---

### Task 1 : Vue — enrichir `prestataires_geojson` (données réelles)

**Files:**
- Modify: `Plateform_medicale/views.py:1529-1539` (dict `prestataires_geojson` dans `prestataires_proches`)
- Test: `Plateform_medicale/tests.py` (classe `PrestatairesProchesTests`, actuellement lignes 1659-1721)

**Interfaces:**
- Consumes: `Prestataire.type_prestataire`, `Prestataire.telephone`, `Medecin.prestataire` (`related_name="medecins"`) — tous déjà sur le modèle, aucun changement de modèle.
- Produces: chaque élément de `prestataires_geojson` gagne `type_code` (str, une des 4 valeurs `Prestataire.Type` : `HOPITAL`/`CLINIQUE`/`PHARMACIE`/`CABINET`), `telephone` (str, `""` si non renseigné — jamais `None`), `medecin_count` (int, `>= 0`). La clé `pk` existe déjà (ajoutée lors d'un travail précédent) — ne pas la dupliquer.

- [ ] **Step 1: Écrire le test qui échoue**

Dans `Plateform_medicale/tests.py`, dans la classe `PrestatairesProchesTests`, ajouter après `test_lat_lng_invalides_ignores` (la dernière méthode de la classe, ligne 1721) :

```python
    def test_geojson_contient_les_champs_enrichis(self):
        Medecin.objects.create(
            nom='Diallo', prenom='Awa', specialite='Generaliste',
            telephone='338001122', email='awa.diallo@example.sn',
            prestataire=self.proche,
        )
        response = self.client.get(reverse('prestataires_proches'))
        geojson = response.context['prestataires_geojson']
        item = next(p for p in geojson if p['nom'] == 'Clinique Proche')
        self.assertEqual(item['pk'], self.proche.pk)
        self.assertEqual(item['type_code'], 'CLINIQUE')
        self.assertEqual(item['telephone'], '')
        self.assertEqual(item['medecin_count'], 1)
```

`Medecin` est déjà importé en tête de `tests.py` (ligne 15). `self.proche` (créé dans `setUp`, `type_prestataire='CLINIQUE'`) n'a pas de `telephone` renseigné → chaîne vide attendue (`CharField(blank=True)` sans `null=True`, jamais `None`).

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests.test_geojson_contient_les_champs_enrichis -v 2`
Expected: FAIL — `KeyError: 'type_code'` (les clés `pk`/`nom`/`type`/`ville`/`latitude`/`longitude` existent déjà, `type_code`/`telephone`/`medecin_count` non).

- [ ] **Step 3: Implémenter**

Dans `Plateform_medicale/views.py`, remplacer :

```python
    prestataires_geojson = [
        {
            "pk": prestataire.pk,
            "nom": prestataire.nom,
            "type": prestataire.get_type_prestataire_display(),
            "ville": prestataire.ville,
            "latitude": float(prestataire.latitude),
            "longitude": float(prestataire.longitude),
        }
        for prestataire in avec_coordonnees
    ]
```

par :

```python
    prestataires_geojson = [
        {
            "pk": prestataire.pk,
            "nom": prestataire.nom,
            "type": prestataire.get_type_prestataire_display(),
            "type_code": prestataire.type_prestataire,
            "ville": prestataire.ville,
            "telephone": prestataire.telephone,
            "latitude": float(prestataire.latitude),
            "longitude": float(prestataire.longitude),
            "medecin_count": prestataire.medecins.count(),
        }
        for prestataire in avec_coordonnees
    ]
```

- [ ] **Step 4: Lancer le test pour vérifier qu'il passe**

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests.test_geojson_contient_les_champs_enrichis -v 2`
Expected: `Ran 1 test ... OK`

- [ ] **Step 5: Vérifier que les tests existants de la classe passent toujours**

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests -v 2`
Expected: `Ran 7 tests ... OK`

- [ ] **Step 6: Vérification globale et commit**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (145 tests)

```bash
git add Plateform_medicale/views.py Plateform_medicale/tests.py
git commit -m "feat(assure): prestataires_geojson inclut type_code, telephone, medecin_count"
```

---

### Task 2 : Mise en page deux colonnes + barre de filtres (structure)

**Files:**
- Modify: `Plateform_medicale/templates/base.html` (nouvelle classe CSS `.proches-layout`, à ajouter juste après la règle `.admin-layout` existante)
- Modify: `Plateform_medicale/templates/prestataires_proches.html` (structure HTML complète du `{% block content %}`, jusqu'à la ligne `{{ prestataires_geojson|json_script:"donnees-prestataires-proches" }}` incluse — le CSS des popups et le `<script>` existants, après cette ligne, ne sont pas touchés par cette tâche)

**Interfaces:**
- Consumes: `prestataires_sans_coordonnees`, `localisation_active`, `prestataires_geojson` (contexte de vue, inchangé depuis Task 1). `prestataires_tries` reste dans le contexte (consommé par `tests.py`, voir `PrestatairesProchesTests`) mais n'est **plus utilisé par le template** à partir de cette tâche — le rendu de la liste devient entièrement piloté par JS (Task 3), cohérent avec le fait que la carte Leaflet elle-même dépend déjà entièrement de JS (pas de repli sans JS existant sur cette page).
- Produces: éléments HTML avec les `id` suivants, que Task 3 doit retrouver exactement : `#filtre-recherche`, `#filtre-ville`, `#filtre-type`, `#filtre-distance`, `#carte-prestataires-proches`, `#liste-prestataires-proches`, `#avis-localisation`, `#sous-titre-page`. Classe CSS `.liste-prestataires-proches` (conteneur de la colonne droite) et `.carte-prestataire-entete` (réservée pour la Task 3, définie ici).

- [ ] **Step 1 : Ajouter `.proches-layout` dans `base.html`**

Dans `Plateform_medicale/templates/base.html`, remplacer :

```css
        .admin-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.75fr);
            gap: 20px;
            margin-top: 28px;
        }
```

par :

```css
        .admin-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.75fr);
            gap: 20px;
            margin-top: 28px;
        }

        .proches-layout {
            display: grid;
            grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr);
            gap: 20px;
            align-items: start;
            margin-top: 20px;
        }

        .proches-layout .carte-colonne {
            position: sticky;
            top: 16px;
        }

        @media (max-width: 860px) {
            .proches-layout {
                grid-template-columns: 1fr;
            }

            .proches-layout .carte-colonne {
                position: static;
            }
        }
```

- [ ] **Step 2 : Réécrire la structure HTML de `prestataires_proches.html`**

Remplacer tout le contenu du fichier depuis `{% block content %}` jusqu'à la ligne contenant `{{ prestataires_geojson|json_script:"donnees-prestataires-proches" }}` (incluse) par :

```html
{% block content %}
<section class="page-title">
    <div>
        <h1>Prestataires proches</h1>
        <p class="subtitle" id="sous-titre-page">
            {% if localisation_active %}
            Prestataires du reseau tries du plus proche au plus loin de votre position.
            {% else %}
            Liste complete du reseau partenaire, triee par ville.
            {% endif %}
        </p>
    </div>
</section>

{% if not localisation_active %}
<div class="avis avis-attente" id="avis-localisation">
    <p class="avis-titre">Localisation non activee</p>
    <p>Autorisez la geolocalisation dans votre navigateur pour trier les prestataires du plus proche au plus loin, mis a jour en direct pendant vos deplacements.</p>
</div>
{% endif %}

<form class="filtres" onsubmit="return false;">
    <div>
        <label for="filtre-recherche">Recherche</label>
        <input type="search" id="filtre-recherche" placeholder="Nom du prestataire">
    </div>
    <div>
        <label for="filtre-ville">Ville</label>
        <select id="filtre-ville">
            <option value="">Toutes les villes</option>
        </select>
    </div>
    <div>
        <label for="filtre-type">Type</label>
        <select id="filtre-type">
            <option value="">Tous les types</option>
            <option value="HOPITAL">Hopital</option>
            <option value="CLINIQUE">Clinique</option>
            <option value="PHARMACIE">Pharmacie</option>
            <option value="CABINET">Cabinet medical</option>
        </select>
    </div>
    <div>
        <label for="filtre-distance">Distance max</label>
        <select id="filtre-distance" disabled title="Disponible une fois votre position connue">
            <option value="">Toutes distances</option>
            <option value="2">2 km</option>
            <option value="5">5 km</option>
            <option value="10">10 km</option>
            <option value="20">20 km</option>
            <option value="50">50 km</option>
        </select>
    </div>
</form>

<section class="proches-layout">
    <div class="carte-colonne">
        <div id="carte-prestataires-proches" class="panel" style="height: 480px; padding: 0; overflow: hidden;"></div>
    </div>
    <div id="liste-prestataires-proches" class="liste-prestataires-proches"></div>
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
```

- [ ] **Step 3 : Ajouter les classes CSS de la colonne liste dans le `<style>` existant de la page**

Dans `Plateform_medicale/templates/prestataires_proches.html`, remplacer le `<style>` existant (juste après les balises Leaflet) :

```html
<style>
    /* Habillage des popups Leaflet aux couleurs/typo de l'application
       (par defaut : coins carres, police navigateur). */
    .leaflet-popup-content-wrapper {
        border-radius: 12px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.22);
    }
    .leaflet-popup-content {
        margin: 12px 16px;
        font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif;
        font-size: 13.5px;
        line-height: 1.5;
        color: var(--text);
    }
    .leaflet-popup-content strong {
        color: var(--primary-dark);
        font-size: 14px;
    }
</style>
```

par :

```html
<style>
    /* Habillage des popups Leaflet aux couleurs/typo de l'application
       (par defaut : coins carres, police navigateur). */
    .leaflet-popup-content-wrapper {
        border-radius: 12px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.22);
    }
    .leaflet-popup-content {
        margin: 12px 16px;
        font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif;
        font-size: 13.5px;
        line-height: 1.5;
        color: var(--text);
    }
    .leaflet-popup-content strong {
        color: var(--primary-dark);
        font-size: 14px;
    }

    .liste-prestataires-proches {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    .carte-prestataire-entete {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 10px;
    }

    .carte-prestataire-entete h3 {
        margin: 0;
        font-size: 16px;
        color: var(--primary-dark);
    }
</style>
```

- [ ] **Step 4 : Vérification (pas de test Python nouveau — structure/CSS)**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests -v 2`
Expected: `Ran 7 tests ... OK` (le template continue de fournir un contexte identique ; ces tests n'inspectent que `response.context`, jamais le HTML rendu, donc la réécriture du template ne peut pas les casser — mais on vérifie qu'aucune `TemplateSyntaxError` n'apparaît).

- [ ] **Step 5 : Vérification manuelle (obligatoire, JS non testé automatiquement à ce stade)**

Run: `python manage.py runserver`. Connecté en Assuré, ouvrir "Prestataires proches" : la page doit se charger sans erreur ; la carte (vide de tout marqueur/liste pour l'instant, c'est normal — Task 3 n'est pas encore faite) occupe la colonne de gauche, la barre de filtres s'affiche au-dessus avec les 4 champs (le champ Distance max est visiblement désactivé/grisé), la colonne de droite est vide. Réduire la fenêtre sous ~860px : la carte passe au-dessus de la liste (une seule colonne).

- [ ] **Step 6 : Commit**

```bash
git add Plateform_medicale/templates/base.html Plateform_medicale/templates/prestataires_proches.html
git commit -m "feat(assure): mise en page deux colonnes + barre de filtres (structure)"
```

---

### Task 3 : Pipeline JS — filtrage, tri, rendu de la liste et des marqueurs

**Files:**
- Modify: `Plateform_medicale/templates/prestataires_proches.html` (le bloc `<script>` en fin de fichier, réécrit en totalité ; ajout d'un petit bloc HTML caché juste avant, pour les icônes par type)

**Interfaces:**
- Consumes: `id`s produits par Task 2 (`#filtre-recherche`, `#filtre-ville`, `#filtre-type`, `#filtre-distance`, `#carte-prestataires-proches`, `#liste-prestataires-proches`, `#avis-localisation`, `#sous-titre-page`) ; champs du geojson enrichis par Task 1 (`pk`, `nom`, `type`, `type_code`, `ville`, `telephone`, `latitude`, `longitude`, `medecin_count`) ; icônes `_ICONES` existantes (`building`, `stethoscope`, `pill`) via le tag `{% icone %}`.
- Produces : fonction `rafraichirAffichage()` (aucun paramètre, relit l'état courant des filtres et de la position), variable `marqueursParPk` (objet `{pk: marqueur Leaflet}`, utilisée par Task 4 n'est pas nécessaire ici mais est déjà consommée par le bouton "Voir le profil" de cette même tâche). Le comportement de repli "aucun résultat" de cette tâche (message texte simple) sera remplacé par un état vide illustré en Task 4 — la Task 3 doit fonctionner seule sans dépendre de Task 4.

- [ ] **Step 1 : Ajouter le bloc caché d'icônes par type**

Dans `Plateform_medicale/templates/prestataires_proches.html`, juste avant la ligne `{{ prestataires_geojson|json_script:"donnees-prestataires-proches" }}`, ajouter :

```html
<div id="icones-types-source" style="display:none;" aria-hidden="true">
    <span data-type="HOPITAL">{% icone "building" %}</span>
    <span data-type="CLINIQUE">{% icone "building" %}</span>
    <span data-type="PHARMACIE">{% icone "pill" %}</span>
    <span data-type="CABINET">{% icone "stethoscope" %}</span>
</div>
```

Le fichier doit charger le tag `{% icone %}` : vérifier que la ligne `{% extends "base.html" %}` en tête de fichier est bien précédée ou suivie de `{% load icones %}` — si absent, l'ajouter juste après `{% extends "base.html" %}` :

```html
{% extends "base.html" %}
{% load icones %}
```

- [ ] **Step 2 : Réécrire le `<script>` final**

Remplacer tout le contenu du dernier bloc `<script>...</script>` du fichier (celui qui contient `(function () { ... })();`) par :

```html
<script>
    (function () {
        var DAKAR = [14.6928, -17.4467];
        var donnees = JSON.parse(document.getElementById('donnees-prestataires-proches').textContent);
        var urlRendezVous = "{% url 'ajouter_rendez_vous_assure' %}";

        var iconesParType = {};
        document.querySelectorAll('#icones-types-source [data-type]').forEach(function (element) {
            iconesParType[element.getAttribute('data-type')] = element.innerHTML;
        });

        var COULEURS_TYPE = {
            HOPITAL: '#0f172a',
            CLINIQUE: '#0f766e',
            PHARMACIE: '#14b8a6',
            CABINET: '#2dd4bf',
        };

        function creerIconePrestataire(typeCode) {
            var couleur = COULEURS_TYPE[typeCode] || '#0f766e';
            return L.divIcon({
                className: 'pin-prestataire',
                html: '<svg width="30" height="30" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 3px 5px rgba(15, 23, 42, 0.35));">'
                    + '<path d="M12 21s7-6.4 7-11.5A7 7 0 0 0 5 9.5C5 14.6 12 21 12 21z" fill="' + couleur + '"/>'
                    + '<circle cx="12" cy="9.5" r="2.6" fill="#ffffff"/>'
                    + '</svg>',
                iconSize: [30, 30],
                iconAnchor: [15, 27],
                popupAnchor: [0, -24],
            });
        }

        // Distance a vol d'oiseau (haversine), miroir exact de distance_km
        // cote serveur (Plateform_medicale/models.py) pour un tri identique.
        function distanceKm(lat1, lon1, lat2, lon2) {
            var rayonTerreKm = 6371.0;
            var phi1 = lat1 * Math.PI / 180;
            var phi2 = lat2 * Math.PI / 180;
            var deltaPhi = (lat2 - lat1) * Math.PI / 180;
            var deltaLambda = (lon2 - lon1) * Math.PI / 180;
            var a = Math.pow(Math.sin(deltaPhi / 2), 2)
                + Math.cos(phi1) * Math.cos(phi2) * Math.pow(Math.sin(deltaLambda / 2), 2);
            return rayonTerreKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        }

        function estimerMinutes(distanceKmValeur) {
            return Math.max(1, Math.round(distanceKmValeur / 30 * 60));
        }

        function creerContenuPopup(prestataire, distance) {
            var conteneur = document.createElement('div');

            var titre = document.createElement('strong');
            titre.textContent = prestataire.nom;
            conteneur.appendChild(titre);

            var ligneType = document.createElement('div');
            ligneType.textContent = prestataire.type + ' - ' + prestataire.ville;
            conteneur.appendChild(ligneType);

            if (prestataire.telephone) {
                var ligneTelephone = document.createElement('div');
                ligneTelephone.textContent = 'Tel. ' + prestataire.telephone;
                conteneur.appendChild(ligneTelephone);
            }

            if (distance !== null) {
                var ligneDistance = document.createElement('div');
                ligneDistance.textContent = distance.toFixed(1) + ' km';
                conteneur.appendChild(ligneDistance);
            }

            var actions = document.createElement('div');
            actions.className = 'popup-actions';

            var lienItineraire = document.createElement('a');
            lienItineraire.className = 'button btn-sm';
            lienItineraire.href = 'https://www.google.com/maps/dir/?api=1&destination=' + prestataire.latitude + ',' + prestataire.longitude;
            lienItineraire.target = '_blank';
            lienItineraire.rel = 'noopener';
            lienItineraire.textContent = 'Itineraire';
            actions.appendChild(lienItineraire);

            var lienRdv = document.createElement('a');
            lienRdv.className = 'button primary btn-sm';
            lienRdv.href = urlRendezVous + '?prestataire=' + prestataire.pk;
            lienRdv.textContent = 'Prendre rendez-vous';
            actions.appendChild(lienRdv);

            conteneur.appendChild(actions);
            return conteneur;
        }

        function creerCarteProche(prestataire, distance) {
            var article = document.createElement('article');
            article.className = 'panel carte-prestataire-proche';
            article.style.padding = '18px';

            var entete = document.createElement('div');
            entete.className = 'carte-prestataire-entete';

            var badge = document.createElement('span');
            badge.className = 'dash-stat-icon';
            badge.innerHTML = iconesParType[prestataire.type_code] || '';
            entete.appendChild(badge);

            var titreBloc = document.createElement('div');
            var titre = document.createElement('h3');
            titre.textContent = prestataire.nom;
            titreBloc.appendChild(titre);
            var sousTitre = document.createElement('p');
            sousTitre.className = 'subtitle';
            sousTitre.style.margin = '0';
            sousTitre.textContent = prestataire.type + ' - ' + prestataire.ville;
            titreBloc.appendChild(sousTitre);
            entete.appendChild(titreBloc);

            article.appendChild(entete);

            if (distance !== null) {
                var ligneDistance = document.createElement('p');
                var fort = document.createElement('strong');
                fort.textContent = distance.toFixed(1) + ' km';
                ligneDistance.appendChild(fort);
                ligneDistance.appendChild(document.createTextNode(' - ~' + estimerMinutes(distance) + ' min'));
                article.appendChild(ligneDistance);
            }

            if (prestataire.medecin_count > 0) {
                var ligneMedecins = document.createElement('p');
                ligneMedecins.className = 'subtitle';
                ligneMedecins.textContent = prestataire.medecin_count + (prestataire.medecin_count > 1 ? ' medecins' : ' medecin');
                article.appendChild(ligneMedecins);
            }

            var actions = document.createElement('div');
            actions.className = 'actions';

            var lienProfil = document.createElement('a');
            lienProfil.className = 'button';
            lienProfil.href = '#';
            lienProfil.textContent = 'Voir le profil';
            lienProfil.addEventListener('click', function (evenement) {
                evenement.preventDefault();
                var marqueur = marqueursParPk[prestataire.pk];
                if (marqueur) {
                    carte.flyTo(marqueur.getLatLng(), 15);
                    marqueur.openPopup();
                }
            });
            actions.appendChild(lienProfil);

            var lienRdv = document.createElement('a');
            lienRdv.className = 'button primary';
            lienRdv.href = urlRendezVous + '?prestataire=' + prestataire.pk;
            lienRdv.textContent = 'Prendre rendez-vous';
            actions.appendChild(lienRdv);

            article.appendChild(actions);
            return article;
        }

        var carte = L.map('carte-prestataires-proches').setView(DAKAR, 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(carte);

        var groupeMarqueurs = L.layerGroup().addTo(carte);
        var marqueursParPk = {};

        var champRecherche = document.getElementById('filtre-recherche');
        var champVille = document.getElementById('filtre-ville');
        var champType = document.getElementById('filtre-type');
        var champDistance = document.getElementById('filtre-distance');
        var conteneurListe = document.getElementById('liste-prestataires-proches');
        var baniereLocalisation = document.getElementById('avis-localisation');
        var sousTitrePage = document.getElementById('sous-titre-page');

        var villes = Array.from(new Set(donnees.map(function (p) { return p.ville; }).filter(Boolean))).sort();
        villes.forEach(function (ville) {
            var option = document.createElement('option');
            option.value = ville;
            option.textContent = ville;
            champVille.appendChild(option);
        });

        function appliquerFiltres(liste) {
            var recherche = champRecherche.value.trim().toLowerCase();
            var ville = champVille.value;
            var type = champType.value;
            var distanceMax = champDistance.value ? parseFloat(champDistance.value) : null;

            return liste.filter(function (item) {
                var prestataire = item.prestataire;
                if (recherche && prestataire.nom.toLowerCase().indexOf(recherche) === -1) {
                    return false;
                }
                if (ville && prestataire.ville !== ville) {
                    return false;
                }
                if (type && prestataire.type_code !== type) {
                    return false;
                }
                if (distanceMax !== null && item.distance !== null && item.distance > distanceMax) {
                    return false;
                }
                return true;
            });
        }

        var dernierePositionUtilisateur = { lat: null, lng: null };
        var marqueurUtilisateur = null;
        var carteRecentree = false;

        function calculerListe() {
            return donnees.map(function (prestataire) {
                var distance = (dernierePositionUtilisateur.lat !== null && dernierePositionUtilisateur.lng !== null)
                    ? distanceKm(dernierePositionUtilisateur.lat, dernierePositionUtilisateur.lng, prestataire.latitude, prestataire.longitude)
                    : null;
                return { prestataire: prestataire, distance: distance };
            });
        }

        function rafraichirAffichage() {
            var liste = appliquerFiltres(calculerListe());

            liste.sort(function (a, b) {
                if (a.distance !== null && b.distance !== null) {
                    return a.distance - b.distance;
                }
                return a.prestataire.ville.localeCompare(b.prestataire.ville) || a.prestataire.nom.localeCompare(b.prestataire.nom);
            });

            groupeMarqueurs.clearLayers();
            marqueursParPk = {};
            liste.forEach(function (item) {
                var marqueur = L.marker([item.prestataire.latitude, item.prestataire.longitude], {
                    icon: creerIconePrestataire(item.prestataire.type_code),
                }).bindPopup(creerContenuPopup(item.prestataire, item.distance));
                marqueur.addTo(groupeMarqueurs);
                marqueursParPk[item.prestataire.pk] = marqueur;
            });

            if (conteneurListe) {
                conteneurListe.innerHTML = '';
                if (liste.length === 0) {
                    var vide = document.createElement('p');
                    vide.className = 'subtitle';
                    vide.textContent = "Aucun prestataire ne correspond a votre recherche.";
                    conteneurListe.appendChild(vide);
                } else {
                    liste.forEach(function (item) {
                        conteneurListe.appendChild(creerCarteProche(item.prestataire, item.distance));
                    });
                }
            }
        }

        function surPosition(position) {
            dernierePositionUtilisateur.lat = position.coords.latitude;
            dernierePositionUtilisateur.lng = position.coords.longitude;

            if (marqueurUtilisateur) {
                marqueurUtilisateur.setLatLng([dernierePositionUtilisateur.lat, dernierePositionUtilisateur.lng]);
            } else {
                marqueurUtilisateur = L.circleMarker([dernierePositionUtilisateur.lat, dernierePositionUtilisateur.lng], {
                    radius: 8, color: '#0f766e', fillColor: '#14b8a6', fillOpacity: 1,
                }).addTo(carte).bindPopup('Vous');
            }
            if (!carteRecentree) {
                carte.setView([dernierePositionUtilisateur.lat, dernierePositionUtilisateur.lng], 12);
                carteRecentree = true;
            }

            if (baniereLocalisation) {
                baniereLocalisation.remove();
                baniereLocalisation = null;
            }
            if (sousTitrePage) {
                sousTitrePage.textContent = 'Prestataires du reseau tries du plus proche au plus loin de votre position (mise a jour en direct pendant vos deplacements).';
            }
            if (champDistance) {
                champDistance.disabled = false;
            }

            rafraichirAffichage();
        }

        [champRecherche, champVille, champType, champDistance].forEach(function (champ) {
            champ.addEventListener('input', rafraichirAffichage);
            champ.addEventListener('change', rafraichirAffichage);
        });

        var parametres = new URLSearchParams(window.location.search);
        var latInitial = parseFloat(parametres.get('lat'));
        var lngInitial = parseFloat(parametres.get('lng'));
        if (isFinite(latInitial) && isFinite(lngInitial)) {
            dernierePositionUtilisateur.lat = latInitial;
            dernierePositionUtilisateur.lng = lngInitial;
            marqueurUtilisateur = L.circleMarker([latInitial, lngInitial], {
                radius: 8, color: '#0f766e', fillColor: '#14b8a6', fillOpacity: 1,
            }).addTo(carte).bindPopup('Vous');
            carte.setView([latInitial, lngInitial], 12);
            carteRecentree = true;
            if (champDistance) {
                champDistance.disabled = false;
            }
        }

        rafraichirAffichage();

        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(surPosition, function () {
                // Permission refusee ou indisponible : on reste sur la liste de repli deja affichee.
            }, { enableHighAccuracy: true, maximumAge: 10000 });
        }
    })();
</script>
```

Note de comportement (intentionnelle, documentée) : avant cette tâche, si l'URL contenait `?lat=&lng=`, le suivi de position en direct ne démarrait pas du tout (branches `if`/`else if` mutuellement exclusives). À partir de cette tâche, `watchPosition` démarre toujours ; `?lat=&lng=` sert uniquement à préremplir l'affichage initial (premier rendu instantané, avant que le premier événement `watchPosition` n'arrive), qui est ensuite mis à jour normalement dès que la position réelle est connue. Comportement plus cohérent, aucun test Python ne dépend de l'ancien comportement (ces tests portent sur le rendu serveur via les query params, inchangé).

- [ ] **Step 3 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale.tests.PrestatairesProchesTests -v 2`
Expected: `Ran 7 tests ... OK`

- [ ] **Step 4 : Vérification manuelle (obligatoire, JS non testé automatiquement)**

Run: `python manage.py runserver`. Connecté en Assuré (au moins deux prestataires avec coordonnées de types différents en base — utiliser ceux créés via "Ajouter un prestataire" avec pin posé sur la carte) :
- Ouvrir la console navigateur (F12) : aucune erreur JS au chargement.
- La colonne de droite affiche une carte par prestataire (icône, nom, type/ville, nombre de médecins si > 0).
- Taper dans "Recherche" : la liste et les marqueurs sur la carte se filtrent en direct.
- Choisir une ville puis un type dans les listes déroulantes : la liste se filtre en conséquence.
- Autoriser la géolocalisation : le champ "Distance max" devient actif ; la liste se trie par distance et affiche "X km - ~Y min" ; les marqueurs sur la carte reprennent la couleur attendue par type.
- Cliquer "Voir le profil" sur une carte : la carte Leaflet se centre sur le marqueur correspondant et son popup s'ouvre (nom, ville, téléphone si renseigné, distance, boutons Itinéraire/Prendre rendez-vous).
- Cliquer "Itinéraire" dans un popup : ouvre Google Maps dans un nouvel onglet, direction vers les bonnes coordonnées.
- Filtrer jusqu'à n'avoir aucun résultat (ex. recherche avec un nom inexistant) : le message "Aucun prestataire ne correspond a votre recherche." s'affiche (sera remplacé par l'état vide illustré en Task 4).

- [ ] **Step 5 : Commit**

```bash
git add Plateform_medicale/templates/prestataires_proches.html
git commit -m "feat(assure): filtrage/tri/rendu en direct des prestataires proches (liste + carte)"
```

---

### Task 4 : État vide illustré + restylage des contrôles de zoom Leaflet

**Files:**
- Modify: `Plateform_medicale/templates/prestataires_proches.html` (le `<style>` de la page, et la branche "liste vide" dans `rafraichirAffichage()`)

**Interfaces:**
- Consumes: `conteneurListe`, `rafraichirAffichage()`, `champRecherche`/`champVille`/`champType`/`champDistance` (tous définis en Task 3).
- Produces: fonction `afficherEtatVide(conteneur)` appelée depuis `rafraichirAffichage()` à la place du message texte simple introduit en Task 3.

- [ ] **Step 1 : Ajouter le CSS des contrôles de zoom et de l'état vide**

Dans `Plateform_medicale/templates/prestataires_proches.html`, dans le `<style>` de la page (ajouté en Task 2), ajouter à la fin, avant `</style>` :

```html
    .leaflet-control-zoom a {
        border-radius: 8px !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
        color: var(--primary-dark) !important;
    }

    .leaflet-control-zoom {
        border: none !important;
    }

    .etat-vide {
        text-align: center;
        padding: 32px 20px;
    }

    .etat-vide svg {
        margin-bottom: 12px;
    }

    .etat-vide p {
        color: var(--muted);
        margin: 0 0 16px;
    }

    .etat-vide .actions {
        justify-content: center;
    }
```

- [ ] **Step 2 : Ajouter la fonction `afficherEtatVide` et la brancher**

Dans le `<script>` de `prestataires_proches.html` (introduit en Task 3), remplacer :

```javascript
        function rafraichirAffichage() {
            var liste = appliquerFiltres(calculerListe());

            liste.sort(function (a, b) {
                if (a.distance !== null && b.distance !== null) {
                    return a.distance - b.distance;
                }
                return a.prestataire.ville.localeCompare(b.prestataire.ville) || a.prestataire.nom.localeCompare(b.prestataire.nom);
            });

            groupeMarqueurs.clearLayers();
            marqueursParPk = {};
            liste.forEach(function (item) {
                var marqueur = L.marker([item.prestataire.latitude, item.prestataire.longitude], {
                    icon: creerIconePrestataire(item.prestataire.type_code),
                }).bindPopup(creerContenuPopup(item.prestataire, item.distance));
                marqueur.addTo(groupeMarqueurs);
                marqueursParPk[item.prestataire.pk] = marqueur;
            });

            if (conteneurListe) {
                conteneurListe.innerHTML = '';
                if (liste.length === 0) {
                    var vide = document.createElement('p');
                    vide.className = 'subtitle';
                    vide.textContent = "Aucun prestataire ne correspond a votre recherche.";
                    conteneurListe.appendChild(vide);
                } else {
                    liste.forEach(function (item) {
                        conteneurListe.appendChild(creerCarteProche(item.prestataire, item.distance));
                    });
                }
            }
        }
```

par :

```javascript
        function reinitialiserFiltres() {
            champRecherche.value = '';
            champVille.value = '';
            champType.value = '';
            champDistance.value = '';
            rafraichirAffichage();
        }

        function afficherEtatVide(conteneur, aucunResultatFiltre) {
            var bloc = document.createElement('div');
            bloc.className = 'etat-vide';

            var illustration = document.createElement('div');
            illustration.innerHTML = '<svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">'
                + '<circle cx="36" cy="36" r="34" stroke="#d9e2ea" stroke-width="2"/>'
                + '<path d="M24 44s7-6.2 7-11A7 7 0 0 0 17 33c0 4.8 7 11 7 11z" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                + '<circle cx="24" cy="33" r="2.2" fill="#14b8a6"/>'
                + '<circle cx="46" cy="30" r="9" stroke="#0f766e" stroke-width="2"/>'
                + '<line x1="52.5" y1="36.5" x2="58" y2="42" stroke="#0f766e" stroke-width="2" stroke-linecap="round"/>'
                + '</svg>';
            bloc.appendChild(illustration);

            var message = document.createElement('p');
            message.textContent = aucunResultatFiltre
                ? "Aucun prestataire ne correspond a vos filtres actuels."
                : "Aucun prestataire du reseau n'a encore de position enregistree.";
            bloc.appendChild(message);

            var actions = document.createElement('div');
            actions.className = 'actions';

            var boutonActualiser = document.createElement('button');
            boutonActualiser.type = 'button';
            boutonActualiser.className = 'button';
            boutonActualiser.textContent = 'Actualiser';
            boutonActualiser.addEventListener('click', function () {
                rafraichirAffichage();
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(surPosition, function () {}, { enableHighAccuracy: true });
                }
            });
            actions.appendChild(boutonActualiser);

            if (aucunResultatFiltre) {
                var boutonReinitialiser = document.createElement('button');
                boutonReinitialiser.type = 'button';
                boutonReinitialiser.className = 'button primary';
                boutonReinitialiser.textContent = 'Reinitialiser les filtres';
                boutonReinitialiser.addEventListener('click', reinitialiserFiltres);
                actions.appendChild(boutonReinitialiser);
            }

            bloc.appendChild(actions);
            conteneur.appendChild(bloc);
        }

        function rafraichirAffichage() {
            var liste = appliquerFiltres(calculerListe());

            liste.sort(function (a, b) {
                if (a.distance !== null && b.distance !== null) {
                    return a.distance - b.distance;
                }
                return a.prestataire.ville.localeCompare(b.prestataire.ville) || a.prestataire.nom.localeCompare(b.prestataire.nom);
            });

            groupeMarqueurs.clearLayers();
            marqueursParPk = {};
            liste.forEach(function (item) {
                var marqueur = L.marker([item.prestataire.latitude, item.prestataire.longitude], {
                    icon: creerIconePrestataire(item.prestataire.type_code),
                }).bindPopup(creerContenuPopup(item.prestataire, item.distance));
                marqueur.addTo(groupeMarqueurs);
                marqueursParPk[item.prestataire.pk] = marqueur;
            });

            if (conteneurListe) {
                conteneurListe.innerHTML = '';
                if (liste.length === 0) {
                    var aucunFiltreActif = !champRecherche.value && !champVille.value && !champType.value && !champDistance.value;
                    afficherEtatVide(conteneurListe, !aucunFiltreActif);
                } else {
                    liste.forEach(function (item) {
                        conteneurListe.appendChild(creerCarteProche(item.prestataire, item.distance));
                    });
                }
            }
        }
```

`afficherEtatVide` est définie avant `rafraichirAffichage` dans le fichier (les déclarations de fonction JS sont "hoisted", l'ordre n'a pas d'impact fonctionnel, mais ce placement suit l'ordre de lecture logique). `reinitialiserFiltres` est ajoutée pour le bouton "Réinitialiser les filtres" — elle vide les 4 champs puis rappelle `rafraichirAffichage()`, cohérent avec le pipeline existant (aucune logique dupliquée).

- [ ] **Step 3 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (145 tests, aucune régression)

- [ ] **Step 4 : Vérification manuelle (obligatoire, JS non testé automatiquement)**

Run: `python manage.py runserver`. Connecté en Assuré sur "Prestataires proches" :
- Filtrer jusqu'à n'avoir aucun résultat (ex. type "Pharmacie" alors qu'aucune pharmacie n'a de coordonnées) : l'illustration + le message "Aucun prestataire ne correspond a vos filtres actuels." + les boutons "Actualiser" et "Réinitialiser les filtres" s'affichent, centrés.
- Cliquer "Réinitialiser les filtres" : tous les champs reviennent à leur valeur par défaut, la liste complète réapparaît.
- Si aucun prestataire du réseau n'a de coordonnées du tout (base vide de test) : le message "Aucun prestataire du reseau n'a encore de position enregistree." s'affiche, avec seulement le bouton "Actualiser" (pas de "Réinitialiser les filtres", puisqu'aucun filtre n'est actif).
- Vérifier les boutons de zoom (+/-) en haut à gauche de la carte : coins arrondis, légère ombre, cohérents visuellement avec le reste des boutons de l'application.

- [ ] **Step 5 : Commit**

```bash
git add Plateform_medicale/templates/prestataires_proches.html
git commit -m "feat(assure): etat vide illustre + boutons zoom Leaflet restyles"
```

---

## Après l'implémentation

Une fois les 4 tâches terminées : mettre à jour `FONCTIONNEMENT.txt` (description de `prestataires_proches` — filtres, marqueurs par type, popups enrichis, état vide) et `GUIDE_UTILISATEUR.md` (section Assuré, "Prestataires proches" — mentionner les filtres et le contenu enrichi des cartes). Pas une tâche du plan (pas de code), mais à ne pas oublier avant de considérer la fonctionnalité terminée (règle de documentation du projet, voir `CLAUDE.md`). Une fois la documentation à jour, consolider et supprimer ce plan et le spec associé de `docs/superpowers/` (convention documentée dans `CLAUDE.md`, section "Documents de travail").
