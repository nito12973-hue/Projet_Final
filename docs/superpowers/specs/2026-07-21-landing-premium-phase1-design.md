# Landing page premium — feuille de route + Phase 1 (design)

Date : 2026-07-21
Statut : approuvé, en attente de plan d'implémentation (Phase 1 uniquement)

## Contexte et objectif

La landing page (`Plateform_medicale/templates/landing.html`) est déjà fonctionnelle
et plutôt soignée (header sticky glassmorphism-lite, hero animé, cartes de
services avec hover, timeline "parcours", section à-propos, bandeau CTA,
contact, footer, animations au défilement via `IntersectionObserver`).

L'objectif est de la transformer en une landing page **premium**, au niveau
visuel d'une plateforme SaaS moderne (Doctolib/Qare/MyChart/Stripe/Linear —
inspiration uniquement, aucune copie), avec de nombreuses sections
nouvelles (statistiques, partenaires, timeline QR Code, showcase des
dashboards, carte du Sénégal, témoignages, FAQ, contact enrichi, footer
premium) et une identité visuelle rehaussée (glassmorphism léger, dégradés,
ombres premium, animations).

**Portée : uniquement visuelle/UX.** Aucune logique métier nouvelle, aucune
route Django nouvelle, aucun modèle nouveau. La vue `landing` (`views.py:210`)
reste `return render(request, "landing.html")` sans contexte — c'est un
changement de template pur.

## Feuille de route (4 phases, une spec/plan/implémentation par phase)

Ce document ne couvre en détail que la **Phase 1**. Les décisions de contenu
ci-dessous s'appliquent à l'ensemble des 4 phases (actées une fois, pour ne
pas les rouvrir à chaque phase) ; le détail de conception de chaque phase
sera fait dans sa propre spec, au moment de l'aborder.

1. **Phase 1 (ce document)** — Fondations visuelles (tokens CSS) + Hero
   (nouvelle illustration téléphone + cartes flottantes) + section
   Statistiques.
2. **Phase 2** — Section "Ils nous font confiance" (partenaires), refonte
   des cartes Services, "Comment ça marche" en vraie timeline visuelle.
3. **Phase 3** — Section dédiée au parcours QR Code (illustration), showcase
   des 4 dashboards (maquettes stylisées), carte interactive du Sénégal
   (illustrative).
4. **Phase 4** — Témoignages, FAQ (accordéon), Contact enrichi (formulaire
   mailto + carte), footer premium (réseaux sociaux/liens légaux), passe
   finale responsive/accessibilité sur l'ensemble de la page.

## Décisions retenues (cadrage utilisateur, valables pour les 4 phases)

- **Aucune nouvelle dépendance externe.** Pas de Bootstrap 5, pas d'icônes
  Lucide. Le CSS autonome existant de `landing.html` et le système d'icônes
  maison (`templatetags/icones.py`, dict `_ICONES`, `{% icone "nom" %}`)
  sont conservés et étendus — cohérence avec `base.html`/`base_auth.html` et
  avec la convention du projet ("aucun émoji, toujours réutiliser une icône
  existante avant d'en ajouter une nouvelle").
- **Aucun nom d'institution réelle et identifiable** dans la section
  partenaires (Phase 2) : noms génériques/fictifs (ex. "Clinique du
  Plateau", "Pharmacie Almadies", "Groupe IPM Sénégal" en tant que
  catégorie générique) — présenter des noms précis et réels (Hôpital
  Principal, Clinique Pasteur, Pharmacie Guigon...) comme partenaires
  laisserait croire à un partenariat réel non confirmé.
- **Témoignages (Phase 4) : avatars illustrés/initiales**, pas de photos
  "réalistes" — ni outil de génération d'image disponible dans cet
  environnement, ni photos de vrais visages associées à de faux noms sur
  une plateforme médicale (risque de tromperie).
- **Dashboards (Phase 3) : maquettes HTML/CSS stylisées**, pas de vraies
  captures d'écran — aucun outil d'automatisation navigateur connecté dans
  cette session pour se connecter avec chaque rôle et capturer l'écran.
- **Carte du Sénégal (Phase 3) : illustrative/statique**, quelques
  marqueurs d'exemple, pas de données réelles de la table `Prestataire` —
  les exposer publiquement nécessiterait une route Django publique
  nouvelle, exclu par la contrainte "ne pas changer les routes".
- **Formulaire de contact (Phase 4) : `mailto:`**, pas de soumission
  serveur — cohérent avec "aucune nouvelle route/logique".
- **Liens légaux et réseaux sociaux du footer (Phase 4) : présents mais
  visuellement désactivés** (pas de `href` fonctionnel) — aucune page
  légale ni compte social réel n'existe ; les afficher comme des liens
  actifs serait une fausse promesse.
- **Statistiques chiffrées (Phase 1, détaillé ci-dessous) : présentées
  comme des objectifs/capacité de déploiement**, jamais comme des données
  d'usage réelles (la base ne contient qu'une poignée de comptes de démo).

## Phase 1 — Détail de conception

### 1. Fondations visuelles (tokens CSS)

Nouvelles variables ajoutées au `:root` existant de `landing.html`, sans
modifier les tokens actuels (`--primary`, `--primary-strong`,
`--primary-dark`, `--primary-accent`, `--primary-soft`, `--border`,
`--text`, `--muted`, `--surface`) :

- `--ombre-douce`, `--ombre-flottante`, `--ombre-forte` : ombres
  multi-couches (plus subtiles que les `box-shadow` actuels codés en dur
  dans certaines règles), réutilisées par les nouvelles cartes flottantes
  et sections.
- `--verre-fond`, `--verre-flou` : glassmorphism léger
  (`rgba(255,255,255,.65)` + `backdrop-filter: blur(...)`), extension du
  principe déjà utilisé sur le `<header>` sticky — appliqué aux cartes
  flottantes du Hero et aux badges de confiance, pas généralisé à toute la
  page.
- 2-3 formes organiques de fond (blobs SVG, courbes fluides), basse
  opacité, position absolue, derrière le Hero et la section Stats —
  viennent en complément des `.croix` animées existantes (inchangées).
- Nouveaux `@keyframes` : `flotter-lent` et `flotter-inverse` (variantes de
  délai/amplitude/sens du `@keyframes flotter` existant, pour désynchroniser
  les cartes flottantes entre elles).
- Nouvelle classe `.badge-confiance` : pastille discrète (icône + texte
  court), fond `--verre-fond`, utilisée sous les CTA du Hero.
- Toutes les nouvelles règles respectent le bloc `@media
  (prefers-reduced-motion: reduce)` déjà présent (animations désactivées).

### 2. Hero

**Colonne gauche**
- Nouveau titre, garde le mot-clé "connectée" (identité déjà posée par le
  reste du site) : *« La santé, connectée — du premier clic au
  remboursement. »* (mot "connectée" en dégradé accent, comme aujourd'hui
  via `.accent`).
- Sous-titre resserré, même message qu'aujourd'hui (RDV, consultations,
  ordonnances QR, remboursement d'assurance, une seule plateforme).
- **Les 2 boutons CTA sont conservés à l'identique** (mêmes libellés « Accéder
  à mon espace » / « Comment obtenir un compte ? », mêmes URLs `{% url
  'login' %}` / `#acces`) — seul le traitement visuel est rehaussé (ombres
  premium au survol).
- 3 badges de confiance sous les CTA (classe `.badge-confiance`), icônes
  existantes de `_ICONES` : `shield-check` « Ordonnances infalsifiables »,
  `lock` « Données sécurisées », `zap` « Suivi en temps réel » — uniquement
  des capacités réelles déjà décrites ailleurs sur la page (section
  à-propos), aucune certification inventée.

**Colonne droite — illustration**
- Mockup téléphone en CSS pur (silhouette arrondie, bordure foncée façon
  bezel `--primary-dark`, petite encoche haute) contenant une mini-interface
  SantéSN : en-tête avec logo, puis la carte "Rendez-vous du jour"
  **existante** (Dr Ndiaye, les 3 lignes de rendez-vous avec Mamadou Diallo/
  Aïssatou Diallo/Fatou Diallo, les mini-stats "37 RDV"/"12 Ordonnances")
  simplement redimensionnée au format mobile — le contenu métier reproduit
  est identique à l'actuel, seul son cadre visuel change (téléphone plutôt
  que simple carte flottante).
- 3 cartes flottantes satellites en débord autour du téléphone, animations
  `flotter-lent`/`flotter-inverse` avec délais différents :
  1. QR — icône `qr-scan` + "Ordonnance vérifiée" + motif QR décoratif
     (grille de carrés en CSS/SVG, non scannable, purement illustratif).
  2. Médecin — avatar rond (initiales, pas de photo) + "Dr Ndiaye · En
     consultation".
  3. Ordonnance — icône `pill` + "3 médicaments · Prête".
- 2 formes organiques en arrière-plan (blobs SVG, tokens de la section 1),
  basse opacité, derrière le téléphone.
- **Mobile (≤920px, seuil déjà utilisé par `.hero-grille`)** : les cartes
  satellites cessent d'être en position absolue (risque de chevauchement
  sur petit écran) et se rangent en ligne, sous le téléphone, comme des
  badges compacts non flottants.
- Respecte `prefers-reduced-motion` (animations de flottement coupées).

### 3. Section Statistiques

Nouvelle section entre le Hero et Services, fond `alterne` (même teinte
turquoise clair que la section "Comment ça marche" actuelle — garde
l'alternance visuelle des fonds de section sans changer les sections
existantes).

- Sur-titre : *"Notre ambition"*. H2 : *"Une plateforme conçue pour passer à
  l'échelle"*.
- **Ligne de transparence, visible** (pas en petite note cachée) sous le H2 :
  *"Chiffres cibles de déploiement du réseau partenaire — pas des
  statistiques d'usage actuelles."*
- 4 cartes stats, grille responsive (`repeat(auto-fit, minmax(...))`, même
  famille que `.grille-contact` existante), icône (pastille) + grand
  chiffre + libellé court :
  1. `users` — 15 000+ — Assurés couverts
  2. `stethoscope` — 500+ — Médecins partenaires
  3. `building` — 250+ — Prestataires du réseau
  4. `bar-chart` — 100 000+ — Consultations gérées
- Animation compteur : au défilement, réutilise l'`IntersectionObserver`
  déjà en place pour `.revele` (chaque `<strong data-cible="15000">` s'anime
  de 0 à sa valeur sur ~1,2s, easing simple en JS vanilla) ; désactivée si
  `prefers-reduced-motion` (affichage direct de la valeur finale).
- Cartes au style `.panel`/`.carte-service` (léger hover `translateY`),
  cohérentes avec le reste de la page.

## Fichiers concernés (Phase 1)

- `Plateform_medicale/templates/landing.html` — seul fichier modifié :
  nouvelles règles CSS dans le `<style>` existant (tokens, keyframes,
  `.badge-confiance`, mockup téléphone, cartes flottantes, section stats),
  nouveau balisage HTML (Hero restructuré + section Stats insérée), petit
  script JS ajouté (compteur animé), en plus du script de révélation au
  défilement déjà présent (étendu, pas dupliqué).
- Aucun autre fichier (pas de `views.py`, `urls.py`, `models.py`,
  `static/` — ce dernier n'existe pas dans ce projet, tout le CSS/SVG reste
  inline dans le template, cohérent avec le reste de l'application).

## Hors périmètre (Phase 1)

- Toutes les sections/décisions listées pour les Phases 2 à 4 (partenaires,
  services, timeline visuelle, QR Code, dashboards, carte, témoignages,
  FAQ, contact enrichi, footer premium).
- Tout changement de route, de vue ou de modèle Django.
- Toute donnée réelle (utilisateurs, statistiques d'usage, prestataires) —
  la section Stats est explicitement présentée comme un objectif, pas une
  mesure réelle.

## Tests

Changement purement présentationnel : la vue `landing` (`views.py:210`) ne
change pas (`return render(request, "landing.html")`, sans contexte). Il
n'existe aujourd'hui aucun test Django pour cette vue. `python manage.py
check` doit rester sans erreur ; `python manage.py test Plateform_medicale`
doit rester vert (145 tests actuels, aucune régression attendue — aucun
test n'exerce ce template). Le nouveau JS (compteur animé) n'est pas
testable par la suite Django (JS non exécuté par le test client), cohérent
avec les autres pipelines JS déjà livrés sur ce projet (ex. filtrage des
prestataires proches) — vérification manuelle obligatoire (`runserver`,
inspection visuelle desktop/mobile, `prefers-reduced-motion` activé/
désactivé).
