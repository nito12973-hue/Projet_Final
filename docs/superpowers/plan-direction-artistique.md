# SantéSN — Revue de direction artistique (plan d'action)

> Document de travail temporaire (voir CLAUDE.md, "Documents de travail"). Reçu
> le 2026-07-23 sous forme d'artifact (revue complète : identité visuelle,
> design system, 14 parcours notés, plan d'action priorisé). Retranscrit ici
> pour ne pas dépendre d'un lien externe. À supprimer une fois les 50 items
> traités et le contenu utile reporté dans FONCTIONNEMENT.txt.

Verdict global au moment de l'audit : **6,2 / 10** — identité de marque mature
(palette Territoire A, logo Croix-Pouls : ne pas rouvrir), socle produit
inégal. Écrans forts : Landing (8/10), Rapports (8/10). Écrans faibles :
Dashboard Pharmacien (4,5/10), Notifications (4,5/10), Consultations (5/10),
Profil (5/10).

## Scores par écran (état au 2026-07-23, avant ce plan)

| Écran | Score | Point faible principal |
|---|---|---|
| Landing | 8/10 | Pas de preuve sociale, pas de showcase des dashboards |
| Connexion | 6/10 | Générique, pas de "mot de passe oublié" |
| Dashboard Admin | 6,5/10 | Aucun graphique, encart "gouvernance" statique |
| Dashboard Assuré | 7/10 | Stat ordonnances non actionnable |
| Dashboard Médecin | 6/10 | Stat non cliquable (incohérence) — **item 17, fait** |
| Dashboard Pharmacien | 4,5/10 | 1 seule carte stat — **item 4, fait** |
| Prestataires | 7,5/10 | Formulaire admin non accessible (0 aria-*) |
| Consultations | 5/10 | Formulaire brut, tableau nu, pas de filtre |
| Ordonnances | 5,5/10 | Scan = saisie texte, pas de caméra |
| Paiements | 6/10 | Version assuré pauvre (pas de filtre/stat) |
| Rapports | 8/10 | État "graphique indisponible" en texte JS brut |
| Profil | 5/10 | changer_mot_de_passe.html nu, sans contexte |
| Carte utilisateur (.carte-assure) | 7,5/10 | Sous-exploitée (2 usages, variante .mini inutilisée) |
| Notifications | 4,5/10 | Pas de filtre lu/non-lu, pas de pagination |

## Décisions déjà tranchées (ne pas rouvrir)

- **Palette** : Territoire A — Lagune (navy `#0B2027`, teal `#0E7C86`,
  `--primary-strong` `#095059`, `--primary-accent` `#4FB8AE`, terracotta accent
  `#E0824F`, `#EFF4F3`). Alternatives écartées : "Clinique Nordique" (trop
  froid/générique), "Sahel Chaleureux" (trop risqué en contexte clinique, à
  garder en réserve).
- **Typographie** : Manrope (titres) / Public Sans (texte) / IBM Plex Mono
  (identifiants). Alternatives écartées : famille unique façon Inter (efface
  la distinction titres/données), serif éditorial (trop "cabinet médical
  individuel").
- **Logo** : Croix-Pouls (croix arrondie + tracé de pouls terracotta),
  4 concepts comparés, déployé sur les 5 gabarits qui portent une marque.
  Manquant mais non prioritaire : logo secondaire empilé, icône PWA
  (voir item 47), version monochrome — à ne traiter que si besoin concret.
- **Cartes/boutons/tableaux/dashboards** : un seul style cohérent existe déjà
  pour chacun (panneaux plats à bordure fine, boutons à dégradé restreint au
  primaire, tableaux natifs à en-tête teal) — le vrai chantier est de
  compléter les composants manquants (modale, pagination, recherche,
  tooltip), pas de choisir entre variantes.

## Design system — inventaire

Mature : boutons, badges/statuts, cartes/panneaux, alertes/avis, sidebar/
navbar/footer, icônes (39, style unique cohérent).
Incomplet : tableaux (pas de tri, `min-width:680px` fixe pénalise
mobile), formulaires (plusieurs écrans hors `.panel`), états vides (13/23
écrans).
**Absent** : rien d'identifié à ce jour parmi P0/P1 (item 13 tranché
"non retenu", voir plus bas — ne correspond pas au modele de
navigation server-rendered du projet).
Modale, pagination, toasts, recherche dédiée et tooltip on-brand
(sidebar réduite uniquement, cas isolé du `select` de
`prestataires_proches.html` resté en `title` natif) déjà livrés
(items 1-3, 11-12).
Dette CSS morte : aucune connue à ce jour (`.action-tiles`/`.action-tile`
retiré item 9, `.carte-assure.mini` retiré item 10).

## Plan d'action — 50 chantiers (numérotés par priorité décroissante)

Aucun ne recouvre les ~30 correctifs déjà livrés sous "audit Top 50 v1".
Statut par item : voir la colonne "Chantier" des tableaux ci-dessous
(barré + **FAIT** (commit) = livré).

### P0 — Fondations manquantes (8 chantiers, bloquent une image "prêt pour l'échelle")

| # | Chantier | Pourquoi | Difficulté | Temps | Fichiers |
|---|---|---|---|---|---|
| 1 | ~~Pagination sur toutes les listes~~ | **FAIT** (commit 0d10bc0) | Moyenne | 2-3 j | views.py (vues liste_*), templates liste_*.html |
| 2 | ~~Modale on-brand pour remplacer `confirm()`~~ | **FAIT** (commit 49acae5) | Moyenne | 2 j | base.html, liste_utilisateurs.html |
| 3 | ~~Toasts pour les messages Django~~ | **FAIT** (commit 6c438cd) | Faible | 1-2 j | base.html |
| 4 | ~~Enrichir le dashboard Pharmacien~~ | **FAIT** (commit 24a467e) | Faible | 1 j | dashboard_pharmacien.html, views.py |
| 5 | ~~Refondre l'écran Consultations~~ | **FAIT** (commit 70b026f) | Moyenne | 2 j | ajouter_consultation_medecin.html, historique_consultations.html |
| 6 | ~~Filtres + recherche sur Notifications~~ | **FAIT** (commit 4a6e728) | Moyenne | 1 j | mes_notifications.html, liste_notifications_envoyees.html, views.py |
| 7 | ~~Passe accessibilité (aria) sur les formulaires~~ | **FAIT** (commit 4240642) | Moyenne | 3-4 j | ajouter_prestataire.html, liste_utilisateurs.html, puis reste |
| 8 | ~~Clarifier le scan pharmacien (caméra vs douchette)~~ | **FAIT** (commit 8789440) | Faible-moyenne | 0,5-3 j | scanner_ordonnance.html |

### P1 — Consolidation du design system (12 chantiers)

| # | Chantier | Pourquoi | Difficulté | Temps | Fichiers |
|---|---|---|---|---|---|
| 9 | ~~Retirer `.action-tiles`/`.action-tile`~~ | **FAIT** (commit 7067c92) | Faible | 15 min | base.html |
| 10 | ~~Trancher le sort de `.carte-assure.mini`~~ | **FAIT** (commit f31d8fc) | Faible | 15 min – 0,5 j | base.html |
| 11 | ~~Composant recherche dédié~~ | **FAIT** (commit 45a52e8) | Faible | 1 j | base.html + écrans avec recherche |
| 12 | ~~Composant tooltip on-brand~~ | **FAIT** (commit ffd2408) | Faible | 1 j | base.html |
| 13 | ~~Skeleton loaders sur les tableaux~~ | **Non retenu** (2026-08-02) : la pagination (item 1) est un lien `<a href="?page=N">` classique, navigation complete cote serveur -- pas de fetch client qui laisserait un tableau vide a couvrir. Un skeleton supposerait d'intercepter les clics en JS (fetch + history API + re-render), un changement d'architecture disproportionne par rapport au gain, sans precedent ailleurs dans l'app. Le retour visuel existe deja au niveau global (#barre-chargement). | Moyenne | 1-2 j | base.html |
| 14 | ~~Mini-graphique de tendance (Admin/Médecin)~~ | **FAIT** (commit 4f0ff44) | Moyenne | 2 j | dashboard.html, dashboard_medecin.html, views.py |
| 15 | Uniformiser les formulaires bruts | Plusieurs écrans hors `.panel` | Moyenne | 2-3 j | ajouter_consultation_medecin.html, changer_mot_de_passe.html, etc. |
| 16 | Rendre utile l'encart "gouvernance" du dashboard admin | Actuellement pavé de texte statique | Faible-moyenne | 1 j | dashboard.html, views.py |
| 17 | ~~Corriger la stat non cliquable du dashboard médecin~~ | **FAIT** (commit dd11904) | Faible | 15 min | dashboard_medecin.html |
| 18 | Étendre les états vides illustrés aux 9-10 listes CRUD restantes | Tag `illustration_vide` existe déjà | Faible | 1 j | liste_utilisateurs.html, liste_patients.html, etc. |
| 19 | ~~En-tête de tableau collant (sticky)~~ | **FAIT** (commit 63c0839) | Faible | 0,5 j | base.html |
| 20 | Tri de colonnes (dates, statuts) | Aucun tri possible nulle part | Moyenne | 2 j | base.html, vues liste_* |

### P2 — Confiance commerciale (5 chantiers)

| # | Chantier | Pourquoi | Difficulté | Temps | Fichiers |
|---|---|---|---|---|---|
| 21 | Section "ils nous font confiance" (landing) | Aucune preuve sociale actuellement | Faible (dev) | 1 j | landing.html |
| 22 | Showcase des 4 dashboards (landing) | Phase déjà planifiée dans FONCTIONNEMENT.txt | Moyenne | 3-4 j | landing.html |
| 23 | Captures réelles des dashboards (section Services) | Actuellement texte seul | Moyenne | 2 j | landing.html |
| 24 | Mention conformité RGPD / hébergement santé | Absent, question fréquente acheteur assurance/hôpital | Faible (texte) | 0,5 j | landing.html |
| 25 | Page contact commercial / processus de vente | "L'admin crée les comptes" pas expliqué au visiteur B2B | Faible-moyenne | 1 j | landing.html |

### P3 — Polish et cohérence fine (25 chantiers)

| # | Chantier | Pourquoi | Difficulté | Temps | Fichiers |
|---|---|---|---|---|---|
| 26 | Vérifier la cohérence 404/500 post-Croix-Pouls | CSS dupliqué en dur | Faible | 0,5 j | 404.html, 500.html |
| 27 | Animation d'entrée/sortie des toasts et de la modale | Cohérence avec `entree-page` | Faible | 0,5 j | base.html (avec items 2-3) |
| 28 | Revoir `min-width:680px` des tableaux courts | Force un scroll horizontal même pour 3 colonnes | Faible | 0,5 j | base.html |
| 29 | Mode "carte" responsive pour tableaux mobiles clés | Aujourd'hui uniquement scroll horizontal | Moyenne-élevée | 3 j | mes_rendez_vous.html, mes_ordonnances.html |
| 30 | Documenter ou utiliser le token `--info` | Ajouté mais aucun usage recensé | Faible | 0,5 j | base.html |
| 31 | Icône "vital"/"urgence" dédiée | Absente au-delà de stethoscope/pill | Faible | 0,5 j | templatetags/icones.py |
| 32 | Icône "paiement en attente" distincte | credit-card réutilisée pour tous les états | Faible | 0,5 j | templatetags/icones.py |
| 33 | Illustration dédiée pour 404/500 | Actuellement logo seul | Faible | 0,5 j | 404.html, 500.html |
| 34 | Illustration pour "graphique indisponible" | Actuellement texte JS brut | Faible | 0,5 j | rapports.html |
| 35 | Étendre le bouton "copier" à tous les identifiants copiables | Ajouté sur un écran (audit v1), pas généralisé | Faible | 1 j | mon_profil_assure.html, voir_ordonnance.html, etc. |
| 36 | Micro-interaction de succès sur actions critiques | Actuellement simple message Django statique | Moyenne | 1-2 j | ajouter_ordonnance_medecin.html, scanner_ordonnance.html, marquer_paiement_regle.html |
| 37 | Loader inline sur boutons d'action asynchrone | Export Excel/PDF, recherche de lieu : pas de retour visuel | Faible-moyenne | 1 j | rapports.html, ajouter_prestataire.html |
| 38 | Écran "Ma carte" dédié, imprimable/exportable | Carte de prise en charge sous-exploitée (2 usages) | Moyenne | 2 j | nouveau template + views.py |
| 39 | Réutiliser `.carte-assure` côté fiche patient médecin | Vérification visuelle d'identité au moment de la consultation | Faible-moyenne | 1 j | mes_patients.html |
| 40 | Uniformiser la position de la colonne statut/badge | Ordre des colonnes potentiellement incohérent | Faible | 1 j (audit + fix) | tous les templates liste_* |
| 41 | Audit des balises `<title>` par écran | Vérifier surcharge du titre générique de base.html | Faible | 1 j | 67 templates |
| 42 | Vérifier le cache CDN Leaflet (SRI, cache long) | Chargé sur 3 templates, dupliqué intentionnellement | Faible | 0,5 j | ajouter_prestataire.html, modifier_prestataire.html, prestataires_proches.html |
| 43 | Lazy-load Chart.js sur rapports.html | Chargé systématiquement même sans données | Faible-moyenne | 1 j | rapports.html |
| 44 | Auditer les suppressions hors confirmer_suppression.html | S'assurer qu'aucune suppression ne contourne la confirmation | Faible | 1 j | views.py |
| 45 | Recherche par nom sur Paiements / Prises en charge | Filtre statut seul aujourd'hui | Faible | 0,5 j | liste_paiements.html, liste_prises_en_charge.html |
| 46 | Export CSV en plus d'Excel/PDF | Utile pour intégration comptabilité côté client entreprise | Faible | 1 j | liste_paiements.html, liste_utilisateurs.html |
| 47 | Manifest PWA + icône d'application | Documenté en spec logo, jamais implémenté | Faible | 0,5 j | nouveau manifest.json, base.html |
| 48 | Comportement hors-ligne minimal | Pertinent en zone à connexion intermittente | Élevée | À chiffrer séparément | hors scope design pur |
| 49 | État "session expirée" explicite | Actuellement redirection silencieuse probable | Faible-moyenne | 1 j | views.py, base_auth.html |
| 50 | Documenter les nouveaux composants transverses dans FONCTIONNEMENT.txt | Cohérence avec la méthode du projet | Faible | 0,5 j | FONCTIONNEMENT.txt |

## Méthode d'exécution (rappel, déjà en vigueur sur ce projet)

Un seul chantier à la fois. Vérification (`manage.py check` + suite de tests
+ test manuel si UI) avant de passer au suivant. Jamais deux modules en
parallèle. Ordre recommandé par la revue : items 4 et 17 d'abord (faits),
puis attaquer la pagination (item 1), chantier structurant dont dépendent
les items 13, 19, 20.
