# Prestataires proches — interface premium (design)

Date : 2026-07-20
Statut : approuvé, en attente de plan d'implémentation

## Contexte et objectif

L'écran Assuré "Prestataires proches" (`prestataires_proches.html`) fonctionne
déjà : carte Leaflet, tri par distance, suivi de position en direct
(`watchPosition`), liste de secours pour les prestataires sans coordonnées.
L'objectif de ce travail est **uniquement visuel/UX** : transformer cette
page en interface deux colonnes façon plateforme de santé premium
(inspiration Doctolib/Google Maps/MyChart/Qare/Practo, sans copier leur
design), avec filtres, cartes prestataires riches, popup carte redessiné,
état vide soigné.

Portée : reste dans le périmètre existant (écran Assuré déjà livré). Aucune
logique métier nouvelle, aucune nouvelle route, aucun nouveau modèle.

## Décisions retenues (issues du cadrage avec l'utilisateur)

- **Pas de Bootstrap.** Cette page est rendue via `{% extends "base.html" %}`
  (sidebar + shell partagés avec tout le reste de l'application connectée).
  Charger le CSS de Bootstrap sur cette page réinitialiserait des éléments
  globaux (`body`, `<button>`, `<table>`, `<a>`) et entrerait en conflit avec
  des classes qui existent déjà sous le même nom (`.badge` notamment,
  utilisée par le design system de l'app pour les statuts). Le rendu premium
  demandé (cartes modernes, coins arrondis, ombres douces, filtres) est
  obtenu avec le système CSS déjà en place (`.panel`, `.badge`, `.button`,
  `.filtres`, palette navy/turquoise) — cohérent avec le reste de
  l'application plutôt qu'un produit visuellement différent greffé dessus.
- **Pas de note (★) ni de statut Ouvert/Fermé.** Aucune donnée réelle
  n'existe pour ça (pas de champ horaires sur `Prestataire`, pas de système
  d'avis patients). Sur une vraie plateforme médicale, inventer une note ou
  un statut d'ouverture pourrait induire un assuré en erreur dans son choix
  de soins — décision explicite de ne rien afficher plutôt que d'afficher du
  factice, même étiqueté "démo".
- **Pas de filtre "Ouvert actuellement" ni "Disponible aujourd'hui".** Même
  raison (pas de données réelles) ; "disponible aujourd'hui" demanderait en
  plus une vraie fonctionnalité métier (plannings médecins par prestataire),
  hors périmètre ("pas de changement de logique métier" demandé
  explicitement).
- **"Voir le profil" ne crée pas de nouvelle page/URL.** Aucune vue de détail
  prestataire n'existe côté Assuré aujourd'hui, et en créer une nouvelle irait
  à l'encontre de "ne pas changer les URLs/vues si ce n'est pas nécessaire" —
  l'essentiel (nom, type, ville, distance, nb. médecins) est déjà visible sur
  la carte. Le bouton fait défiler jusqu'au marqueur correspondant sur la
  carte Leaflet et ouvre son popup (`flyTo` + `openPopup`), sans navigation.
- **Nombre de médecins : donnée réelle**, pas fictive.
  `prestataire.medecins.count()` existe déjà (FK `Medecin.prestataire`,
  `related_name="medecins"` — voir `Plateform_medicale/models.py`). Affiché
  seulement si > 0.

## Architecture

Un seul fichier modifié pour le rendu : `prestataires_proches.html`. Un seul
changement dans `views.py` : enrichir le dict `prestataires_geojson` déjà
transmis au navigateur (aucune nouvelle route, aucune nouvelle vue).

### 1. Changement `views.py` (minimal)

Dans la fonction `prestataires_proches`, le dict `prestataires_geojson`
gagne deux clés :

```python
prestataires_geojson = [
    {
        "pk": prestataire.pk,
        "nom": prestataire.nom,
        "type": prestataire.get_type_prestataire_display(),
        "type_code": prestataire.type_prestataire,       # NOUVEAU — HOPITAL/CLINIQUE/PHARMACIE/CABINET, pour le filtre JS
        "ville": prestataire.ville,
        "telephone": prestataire.telephone,               # NOUVEAU — deja sur le modele, pour le popup (chaine vide si non renseigne, jamais None : CharField blank=True sans null=True)
        "latitude": float(prestataire.latitude),
        "longitude": float(prestataire.longitude),
        "medecin_count": prestataire.medecins.count(),    # NOUVEAU — donnee reelle, related_name="medecins"
    }
    for prestataire in avec_coordonnees
]
```

`type_code` sert au filtre JS (comparaison stable sur la constante, pas sur
le libellé traduit). `telephone` existe déjà sur `Prestataire`
(`Plateform_medicale/models.py`) et n'était simplement pas transmis au
template — l'ajouter au dict JSON n'est pas un changement de logique
métier, juste une donnée en plus dans une structure qui existe déjà.

Aucun autre changement de vue. `prestataires_tries` /
`prestataires_sans_coordonnees` (contexte serveur, utilisé pour le premier
rendu et par `tests.py`) restent identiques.

### 2. Rendu côté client (JS, dans `prestataires_proches.html`)

Le script existant (suivi de position en direct, ajouté précédemment) est
étendu, pas dupliqué. Un pipeline unique :

```
donnees (geojson, avec pk/type_code/telephone/medecin_count)
   -> appliquerFiltres(donnees, etatFiltres)   // recherche, ville, type, distance max
   -> calculerDistances(liste, position)       // si position connue (distanceKm existant)
   -> trier par distance (si position connue) sinon par ville
   -> rendreListe(liste)                        // reconstruit #liste-prestataires-proches
   -> rendreMarqueurs(liste)                    // deplace/recree les marqueurs Leaflet
```

Cette fonction (`rafraichirAffichage()`) est appelée :
- au chargement initial,
- à chaque mise à jour de `watchPosition` (comme aujourd'hui),
- à chaque changement d'un champ de filtre (`input`/`change` sur la barre de
  filtres, sans soumission de formulaire — tout reste côté client).

Pas de requête réseau supplémentaire : `donnees` est déjà entièrement
disponible côté client via `json_script` (comme aujourd'hui).

## Mise en page

Desktop (> ~860px) : grille CSS 2 colonnes, carte à gauche (~68%), liste à
droite (~32%) — nouvelle classe `.proches-layout` dans `base.html` (à côté de
`.admin-layout`, même famille de grilles CSS, ratio différent). Colonne carte
en `position: sticky; top: 16px;` pour rester visible pendant le défilement
de la liste.

Mobile (≤ ~860px) : une seule colonne, carte en haut (hauteur réduite),
liste en dessous — media query dans la même feuille de style que
`.proches-layout`.

Barre de filtres au-dessus des deux colonnes, pleine largeur, réutilise la
classe existante `.filtres` (`display:flex; flex-wrap:wrap; gap:12px`).

## Barre de filtres

Quatre champs, tous des contrôles natifs (`<input>`/`<select>`), aucune
soumission serveur :

1. **Recherche** — `<input type="search">`, filtre sur `nom` (contient,
   insensible à la casse).
2. **Ville** — `<select>`, options générées en JS depuis les valeurs
   distinctes de `ville` présentes dans `donnees` (+ option "Toutes les
   villes").
3. **Type** — `<select>` avec les 4 valeurs fixes (Hôpital/Clinique/
   Pharmacie/Cabinet médical, valeurs = `type_code`) + "Tous les types".
4. **Distance max** — `<select>` avec paliers fixes (2 / 5 / 10 / 20 / 50 km
   + "Toutes distances"). Désactivé (`disabled`, avec une infobulle) tant
   qu'aucune position n'est connue — un filtre par distance n'a pas de sens
   sans distance calculée.

Les filtres ne s'appliquent qu'à la liste avec coordonnées (colonne
droite + carte). La section "Autres prestataires du réseau" (sans
coordonnées, repli existant) reste inchangée, non filtrée — elle n'a pas de
position à filtrer/trier de toute façon.

## Cartes prestataires (colonne droite)

Remplace le rendu actuel (nom/type-ville/distance/bouton) par une carte plus
riche, en réutilisant `.panel` :

- Icône ronde colorée par type (voir "Icônes et couleurs par type"
  ci-dessous), même style que `.dash-stat-icon`.
- Nom (`h3`), type + ville (`.subtitle`).
- Distance (si connue) + **temps estimé** : calcul simple côté client,
  `distance_km / 30 * 60` minutes (30 km/h, vitesse moyenne urbaine
  raisonnable pour Dakar) arrondi à la minute, affiché "~N min" —
  explicitement une estimation, pas un itinéraire réel (cohérent avec le
  hors-périmètre déjà acté pour la fonctionnalité de proximité : pas de
  calcul d'itinéraire réel).
- Nombre de médecins rattachés (`medecin_count`), affiché seulement si > 0
  ("N médecins" / "1 médecin").
- Bouton **Voir le profil** (`.button`) — centre la carte sur le marqueur
  (`flyTo`) et ouvre son popup.
- Bouton **Prendre rendez-vous** (`.button.primary`) — inchangé, même lien
  `ajouter_rendez_vous_assure?prestataire=<pk>`.

## Carte Leaflet

- **Marqueurs colorés par type**, dans la palette déjà déclarée dans
  `:root` de `base.html` (aucune couleur hors palette) :
  - Hôpital → `--primary-dark` (`#0f172a`, navy)
  - Clinique → `--primary-strong` (`#0f766e`, teal foncé)
  - Pharmacie → `--primary` (`#14b8a6`, turquoise vif)
  - Cabinet médical → `--primary-accent` (`#2dd4bf`, teal clair)

  Même forme de pin que l'existant (tracé `map-pin`), fonction factory
  `creerIconePrestataire(typeCode)` au lieu de l'icône unique actuelle.
- **Clic sur une carte prestataire** → `carte.flyTo([lat, lng], 15)` +
  `marqueur.openPopup()`. Clic sur un marqueur → comportement Leaflet
  standard (popup), inchangé.
- **Popup redessiné** (le CSS `.leaflet-popup-*` existe déjà, complété) :
  nom, ville, téléphone (si renseigné — nouveau champ `telephone` du
  geojson), distance (si connue), bouton **Itinéraire** (lien
  `https://www.google.com/maps/dir/?api=1&destination=<lat>,<lng>`,
  `target="_blank" rel="noopener"` — aucune dépendance, aucune clé API),
  bouton **Prendre rendez-vous**. Construit en DOM (`createElement`/
  `textContent`), même règle anti-XSS déjà appliquée aux popups actuels —
  pas de `innerHTML` avec des données stockées.
- **Contrôles de zoom** restylés en CSS (`.leaflet-control-zoom a`) : coins
  arrondis, ombre douce, cohérents avec `.button`.
- **Animation de chargement** : la carte (conteneur `.panel`) réutilise le
  keyframe `entree-carte` déjà défini dans `base.html` (fondu + léger
  déplacement vertical), pas de nouvelle animation à inventer.
- Le cercle "Vous" (position en direct) existe déjà, inchangé.

## Icônes et couleurs par type

Le dict `_ICONES` (`templatetags/icones.py`) contient déjà `building`,
`stethoscope`, `pill` — pas de nouvelle icône SVG à ajouter :

| Type | Icône `_ICONES` | Couleur marqueur |
|---|---|---|
| Hôpital | `building` | `--primary-dark` |
| Clinique | `building` | `--primary-strong` |
| Pharmacie | `pill` | `--primary` |
| Cabinet médical | `stethoscope` | `--primary-accent` |

## État vide

Remplace le texte actuel ("Aucun prestataire du réseau n'a encore de
position enregistrée." / résultat de filtre vide) par un bloc structuré,
affiché quand la liste filtrée est vide (que ce soit parce que le réseau est
vide ou parce que les filtres ne laissent rien passer) :

- Illustration SVG simple (trait fin, même style que les icônes existantes
  — pas d'émoji, pas d'image externe), ex. une carte + point d'interrogation
  stylisés dans la palette turquoise/navy.
- Message convivial et informatif (distinct selon la cause : réseau vide vs
  filtres trop restrictifs, si détectable côté JS).
- Deux boutons : **Actualiser** (relance `rafraichirAffichage()` avec une
  nouvelle tentative de géolocalisation) et **Réinitialiser les filtres**
  (remet les 4 champs à leur valeur par défaut, sans rechargement de page).

## Tests

Aucun test Python nouveau attendu pour le rendu/comportement JS lui-même
(déjà le cas pour le suivi en direct existant — voir `FONCTIONNEMENT.txt`,
"le tri live côté client n'est pas couvert par la suite Django"). Le seul
changement testable côté serveur est l'enrichissement de
`prestataires_geojson` (`type_code`, `telephone`, `medecin_count`) — un test
qui vérifie la présence de ces clés dans `response.context['...]` n'est pas
possible directement (le dict n'est pas mis dans le contexte tel quel, il
est sérialisé en JSON dans le template via `json_script`) ; le plan
d'implémentation devra soit exposer temporairement le dict pour l'assertion,
soit vérifier sa présence dans le HTML rendu (`response.content`) —
décision technique laissée au plan.

`python manage.py test Plateform_medicale` doit rester vert (144 tests
actuels, aucune régression attendue côté serveur).

## Hors périmètre (explicitement exclu)

- Note/avis patients, statut Ouvert/Fermé (pas de donnée réelle).
- Filtres "Ouvert actuellement" / "Disponible aujourd'hui".
- Nouvelle page "profil prestataire" (le bouton "Voir le profil" reste sur
  la même page, ouvre le popup de la carte).
- Bootstrap 5 / Bootstrap Icons (conflit avec le design system existant).
- Calcul d'itinéraire réel (le "temps estimé" est une approximation
  affichée comme telle, pas un appel à un service de routage).
