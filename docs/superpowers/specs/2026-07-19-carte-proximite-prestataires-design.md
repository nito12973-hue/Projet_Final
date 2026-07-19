# Carte de proximité des prestataires — design

Date : 2026-07-19
Statut : approuvé, en attente de plan d'implémentation

## Contexte et objectif

Un assuré (ou un ayant droit géré par lui) doit pouvoir voir, en un coup
d'œil, quels prestataires partenaires (hôpitaux, cliniques, pharmacies,
cabinets) du réseau SantéSN sont les plus proches de l'endroit où il se
trouve actuellement (ex. Dakar), et prendre rendez-vous directement avec l'un
d'eux. Aujourd'hui, le choix d'un prestataire dans le formulaire de
rendez-vous est un simple menu déroulant sans aucune notion de proximité
géographique, et le modèle `Prestataire` ne stocke aucune coordonnée.

Portée : plateforme de prise en charge médicale SantéSN (voir CLAUDE.md,
section "Thème du projet"). Cette fonctionnalité reste dans le périmètre
existant (prestataires + rendez-vous), elle ajoute une couche de
géolocalisation, elle ne dérive pas vers un sujet hors thème.

## Décisions retenues (issues du cadrage)

- **Source de localisation de l'assuré** : l'API de géolocalisation du
  navigateur (demande de permission côté client), pas une adresse en texte
  libre ni un sélecteur manuel de ville.
- **Coordonnées des prestataires** : saisies par l'admin en plaçant un pin
  sur une mini-carte lors de la création/modification d'un prestataire — pas
  de géocodage automatique depuis l'adresse.
- **Emplacement** : nouvel écran dédié dans l'espace Assuré ("Prestataires
  proches"), pas une modification du formulaire de rendez-vous existant.
- **Technologie de carte** : Leaflet.js (CDN, licence libre) + tuiles
  OpenStreetMap — pas de clé API, cohérent avec l'usage déjà fait de Chart.js
  en CDN avec intégrité SRI dans `rapports.html`.
- **Calcul de distance** : formule de haversine (distance à vol d'oiseau),
  calculée côté serveur en Python — pas de service de routage externe.

## Architecture

### 1. Modèle de données

Ajout de deux champs sur `Prestataire` (`models.py`) :

```python
latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
```

Nullable et facultatifs : les prestataires existants n'ont pas de
coordonnées tant qu'un admin ne les définit pas. Un prestataire sans
coordonnées reste utilisable partout ailleurs dans l'application (rendez-vous
classique, etc.) — il est seulement absent du tri par distance sur le nouvel
écran. Migration Django à générer (`makemigrations`/`migrate`).

### 2. Fonction de distance

Nouvelle fonction pure dans `models.py` (à côté de `Prestataire`, ou en
haut du fichier près des autres helpers comme `valider_telephone`) :

```python
def distance_km(lat1, lon1, lat2, lon2):
    """Distance a vol d'oiseau entre deux points (formule de haversine)."""
```

Fonction pure, sans dépendance Django ni requête base de données —
facilement testable unitairement avec des coordonnées connues (ex. Dakar ↔
Thiès ≈ 70 km, tolérance de quelques km).

### 3. Côté Admin — placer le pin

`ajouter_prestataire.html` et `modifier_prestataire.html` : sous les champs
de formulaire existants, une mini-carte Leaflet (centrée sur Dakar par
défaut — 14.6928, -17.4467 — ou sur les coordonnées existantes en
modification). Un clic sur la carte place/déplace un marqueur ; sa position
alimente deux champs cachés `latitude`/`longitude` soumis avec le reste du
formulaire. `PrestataireForm` (`forms.py`) ajoute ces deux champs (facultatifs
— un admin peut enregistrer un prestataire sans placer de pin, à compléter
plus tard).

### 4. Côté Assuré — écran "Prestataires proches"

Nouvelle route `prestataires_proches` (`role_required(User.Role.ASSURE)`),
nouveau template `prestataires_proches.html`, nouvel item de menu dans
`base.html` (section nav Assuré), nouvelle icône si aucune icône existante du
dict `_ICONES` ne convient (vérifier `map-pin`, déjà présente, avant d'en
ajouter une autre).

**Flux :**
1. Au chargement de la page, un script demande la géolocalisation au
   navigateur (`navigator.geolocation.getCurrentPosition`).
2. **Permission accordée** : les coordonnées sont envoyées au serveur (GET
   avec `lat`/`lng` en query params, rechargement de la page ou requête
   fetch — détail laissé au plan d'implémentation). La vue calcule la
   distance de l'assuré à chaque `Prestataire` partenaire (`partenaire=True`)
   **ayant des coordonnées renseignées**, trie du plus proche au plus loin,
   et transmet la liste au template. Le template affiche une carte Leaflet
   (un pin pour l'assuré, un pin par prestataire, avec popup nom/type/adresse
   /distance) et, en parallèle, la même liste sous forme de cartes/lignes
   classiques (cohérent avec le reste du design system — `.panel`, `.badge`
   par type de prestataire) avec la distance affichée en km.
3. **Permission refusée/indisponible/navigateur sans support** : repli sur
   la liste complète des prestataires partenaires ayant des coordonnées,
   **non triée par distance** (tri alphabétique ou par ville), avec un
   message inline expliquant que l'activation de la localisation permettrait
   un tri par proximité. Pas d'erreur bloquante, la page reste utilisable.
4. Les prestataires partenaires **sans coordonnées du tout** sont affichés à
   part, dans une section "Autres prestataires du réseau" sans distance —
   pour ne jamais les faire disparaître silencieusement de la vue de
   l'assuré.

### 5. Lien vers la prise de rendez-vous

Chaque prestataire de la liste a un bouton "Prendre rendez-vous" qui pointe
vers `ajouter_rendez_vous_assure?prestataire=<id>`. La vue
`ajouter_rendez_vous_assure` lit ce paramètre GET (s'il est présent et
correspond à un prestataire partenaire valide) pour pré-sélectionner le champ
`prestataire` du formulaire via son `initial`. Le choix du médecin n'est
**pas** filtré par prestataire dans cette itération (reste la liste complète
des médecins, comme aujourd'hui) — un filtrage médecin/prestataire est un
possible chantier futur, hors périmètre ici (YAGNI).

## Gestion des erreurs

| Cas | Comportement |
|---|---|
| Géolocalisation refusée par l'utilisateur | Repli liste non triée + message explicatif, pas d'erreur |
| Géolocalisation indisponible (navigateur/contexte non sécurisé) | Même repli |
| Prestataire partenaire sans coordonnées | Affiché à part ("Autres prestataires du réseau"), jamais masqué |
| Prestataire non partenaire (`partenaire=False`) | Exclu entièrement, comme dans le formulaire de rendez-vous actuel |
| `?prestataire=` invalide ou prestataire non partenaire | Ignoré silencieusement, formulaire de rendez-vous sans présélection (comportement actuel) |

## Tests à ajouter (`tests.py`)

- `distance_km` : valeurs connues (ex. deux points identiques → 0 ; Dakar ↔
  Thiès ≈ 70 km à quelques km près).
- Accès à `prestataires_proches` refusé aux autres rôles (403), autorisé à
  un Assuré.
- Tri correct par distance croissante quand `lat`/`lng` sont fournis en query
  params.
- Repli correct (liste non triée, pas d'erreur) quand `lat`/`lng` absents.
- Un prestataire `partenaire=False` n'apparaît jamais dans la liste.
- Un prestataire partenaire sans coordonnées apparaît dans la section à part,
  pas dans la liste triée.
- `PrestataireForm` : sauvegarde correcte de `latitude`/`longitude` quand
  fournis, formulaire valide quand absents (facultatifs).
- `ajouter_rendez_vous_assure?prestataire=<id>` pré-sélectionne bien ce
  prestataire dans le formulaire affiché.

## Hors périmètre (explicitement exclu de cette itération)

- Géocodage automatique d'adresse (choix retenu : pin manuel par l'admin).
- Filtrage des médecins par prestataire sélectionné.
- Calcul d'itinéraire/temps de trajet réel (seulement la distance à vol
  d'oiseau).
- Vue carte côté Admin (visualisation globale du réseau) — pourrait être un
  futur réemploi du même composant Leaflet, non demandé ici.
- Le second point soulevé par l'utilisateur dans la même conversation (scan
  de QR code par caméra côté Pharmacien) est une fonctionnalité distincte,
  volontairement traitée séparément (une seule fonctionnalité à la fois, cf.
  méthode de travail imposée par CLAUDE.md).
