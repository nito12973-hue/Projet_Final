# Logo Croix-Pouls — révision de l'identité visuelle SantéSN

Date : 2026-07-22
Statut : approuvé (mark, système de logo) — en attente de plan d'implémentation

## Contexte

Cette spec **remplace uniquement la section Logo** de
`docs/superpowers/specs/2026-07-22-identite-visuelle-design.md` (concept
« F1 — Carte-bouclier »). Suite à une nouvelle session de direction
artistique (positionnement SaaS santé premium, vente à hôpitaux/cliniques/
IPM/assurances/entreprises/pharmacies/médecins), 4 concepts de logo ont été
comparés visuellement (mockups en contexte réel : cartes isolées fond clair/
fond sombre/échelle favicon, puis intégration dans sidebar/en-tête landing/
pied de page/panneau de connexion). Le concept **Croix-Pouls** a été retenu.

**Palette et typographie ne changent pas.** Les deux ont été re-comparées
(4 territoires de palette, 3 pairings typographiques) dans la même session
et le choix précédent a été reconfirmé à l'identique :
- Palette : **Territoire A — Lagune** (`--ink:#0B2027`, `--primary:#0E7C86`,
  `--primary-dark:#095059`, `--primary-light:#4FB8AE`, `--accent:#E0824F`,
  `--bg:#EFF4F3`) — déjà en place et inchangée sur `base.html` et
  `landing.html`.
- Typographie : **Manrope** (titres) / **Public Sans** (corps) /
  **IBM Plex Mono** (données) — déjà en place et inchangée.
- Ancrage sénégalais : reste **discret** (teinte terracotta + « SN » du
  wordmark uniquement, aucun motif ethnique littéral dans le mark).

Voir la spec du 2026-07-22 pour le détail complet de ces deux sections
(inchangées, non reproduites ici).

## Portée

Uniquement le mark et le système de logo. Aucune nouvelle route, vue ou
modèle Django. Remplace le mark Carte-bouclier partout où il apparaît
aujourd'hui — y compris dans `base.html` et `landing.html`, où il a déjà été
implémenté avec l'ancien concept (commits `feature/identite-visuelle`) : ce
travail doit être révisé, pas juste complété. `base_auth.html` (jamais
touché, Task 3 du plan précédent) reçoit directement Croix-Pouls.

## Mark — Croix-Pouls

Une croix médicale aux angles arrondis (deux rectangles perpendiculaires,
`rx` généreux), traversée en son centre par un tracé de pouls simplifié en
terracotta — le pouls « perce » visuellement la croix plutôt que de la
longer. Plus directement lisible comme symbole santé qu'un bouclier
générique ou que la Carte-bouclier précédente, tout en restant géométrique/
épuré (pas une croix rouge de pharmacie classique).

**Géométrie de référence** (`viewBox="0 0 48 48"`) :
```html
<rect x="18" y="6"  width="12" height="36" rx="4" fill="{couleur-croix}"/>
<rect x="6"  y="18" width="36" height="12" rx="4" fill="{couleur-croix}"/>
<path d="M6 24 H14 L17 16 L21 32 L25 19 L27.5 24 H42"
      fill="none" stroke="#E0824F" stroke-width="2.6"
      stroke-linecap="round" stroke-linejoin="round"/>
```
(`stroke-width` du pouls et dimensions du `<svg>` ajustés selon le contexte
d'usage — voir tailles ci-dessous, cohérent avec les tailles déjà en place :
36px sidebar, 38px en-tête landing, 30px pied de page, 46px panneau de
connexion.)

**Règle de couleur (constante du système)** : le pouls est **toujours**
`#E0824F` (terracotta), quel que soit le fond — seule exception : la
variante monochrome dédiée (voir plus bas), où tout passe dans l'unique
teinte du support.

**Couleur de la croix selon le fond** :
- Fond clair (`--bg`/`--surface`) : croix pleine `--ink` (`#0B2027`).
- Fond sombre uni (sidebar `--sb-bg`, pied de page) : croix pleine
  quasi-blanc (`#EFF4F3`).
- Fond sombre en dégradé (panneau de marque `base_auth.html`) : croix
  blanc à opacité réduite (`rgba(255,255,255,0.9)`), pour rester cohérent
  avec le traitement « translucide » déjà utilisé sur ce gabarit pour
  l'ancien mark.
- **Version pleine, sans fond propre** (favicon uniquement — SVG
  transparent affiché directement dans l'onglet du navigateur) : croix
  pleine `--primary` (`#0E7C86`), pouls toujours terracotta.

## Système de logo

- **Logo principal** (horizontal) : mark + wordmark « SantéSN » (« Santé »
  dans la couleur de texte du contexte, « SN » en `--primary-strong` sur
  fond clair / `--primary-light` sur fond sombre) — inchangé par rapport à
  la convention déjà en place, seul le mark change.
- **Logo secondaire** (empilé) : mark au-dessus du wordmark, centré — pour
  espaces étroits/carrés (avatar, en-tête mobile réduit). Non utilisé
  aujourd'hui dans les 3 gabarits concernés (aucun usage carré/avatar
  identifié) ; documenté pour un usage futur.
- **Favicon** : version pleine (croix `--primary`, pouls terracotta) —
  remplace le tracé actuel dans les 3 `data:image/svg+xml` inline des
  `<head>` (`base.html`, `landing.html`, `base_auth.html`).
- **Icône d'application** : à la différence de la favicon (transparente),
  celle-ci a un fond plein — carré à coins arrondis `--primary` (ou
  `--ink`), avec la croix en blanc (pas en `--primary`, pour rester
  visible sur ce fond coloré) + pouls terracotta, centrés. Pas d'usage
  actif dans le projet aujourd'hui (pas de manifest PWA) ; documenté pour
  cohérence future.
- **Monochrome** : croix + pouls dans une seule teinte (noir sur blanc,
  blanc sur noir) — tampons, documents légaux N&B. Pas d'usage actif
  aujourd'hui ; documenté pour cohérence future.
- **Zone de protection** : espace minimum autour du mark égal à la moitié
  de sa hauteur, sur tous les côtés.
- **Usages interdits** : croix `--ink` sur fond sombre (invisible) ; croix
  étirée/déformée (les deux barres doivent rester des rectangles égaux,
  perpendiculaires, jamais de rotation) ; pouls dans une autre couleur que
  terracotta hors version monochrome ; fond non prévu par la charte.

## Fichiers concernés (implémentation à venir)

- `Plateform_medicale/templates/base.html` — favicon (`<head>`), mark SVG
  sidebar (actuellement Carte-bouclier, commit `feature/identite-visuelle`
  déjà appliqué — **à réviser**, pas de nouveau travail sur palette/police).
- `Plateform_medicale/templates/landing.html` — favicon, mark en-tête,
  mark mockup téléphone (Hero), mark pied de page (actuellement
  Carte-bouclier, commit déjà appliqué — **à réviser**).
- `Plateform_medicale/templates/base_auth.html` — favicon, mark + wordmark
  du panneau de marque (jamais touché : palette Territoire A + typographie
  + mark Croix-Pouls, en un seul passage — c'était le Task 3 du plan
  précédent, remplacé par ce plan-ci pour le mark).
- Aucun autre fichier (pas de `views.py`, `urls.py`, `models.py`).

## Tests

Changement purement présentationnel : `python manage.py check` doit rester
sans erreur, `python manage.py test Plateform_medicale` doit rester vert
(148 tests actuels, confirmés après le merge de `main` dans
`feature/identite-visuelle`). Aucun test n'exerce le rendu SVG/CSS —
vérification manuelle obligatoire (`runserver`, inspection des 3 gabarits,
fond clair et fond sombre, échelle favicon).

## Hors périmètre (cette spec)

- Design system de composants (boutons, cartes, tableaux, badges,
  formulaires, sidebar, navbar, footer, modales, pagination, filtres),
  bibliothèque d'icônes, illustrations, langage d'animation — chantiers
  séparés, à brainstormer un par un après celui-ci (méthode du projet : un
  module à la fois).
- Audit UX écran par écran et Top 50 des améliorations — volontairement
  reportés après ces chantiers de design (ils ont besoin des décisions de
  design system/icônes/illustrations pour juger chaque écran sans être
  invalidés par un changement ultérieur).
- Tout changement de route, de vue ou de modèle Django.
