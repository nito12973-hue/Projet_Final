# Dashboard Administrateur — refonte "Poste de pilotage" (Direction A)

Date : 2026-08-05

## Contexte

Le dashboard admin (`dashboard.html`) a déjà eu plusieurs passes de raffinement
incrémental (voir historique git : "refonte complete", "deuxieme passe",
"debloque item 16", "refonte pilotee par l'audit", "corrige 4 ecarts qualite").
Après cette dernière passe (encore non committée au moment de la rédaction de
cette spec — filigrane du hero, `pulse-dot` sur "Aujourd'hui", KPI en style
"discret", trace de pouls sur le sparkline), le retour a été : il faut un
*autre type* de design, pas une nuance de plus sur la même composition.

Trois directions structurellement différentes ont été présentées sous forme
de maquettes HTML (mêmes tokens de couleur/typo, compositions différentes) :
A "Poste de pilotage" (canevas sombre), B "Journal d'activité" (fil
chronologique), C "Tour de contrôle" (dense, mono). **Direction A retenue.**

## Objectif

Remplacer la composition actuelle de `dashboard.html` (empilement de panels
clairs à bordures grises) par un "poste de pilotage" : canevas sombre
navy, un geste visuel fort (tracé de pouls derrière les chiffres de
paiement) plutôt que des cartes toutes égales, tableaux remplacés par des
listes condensées façon relevé de moniteur.

## Périmètre

- **Uniquement `Plateform_medicale/templates/dashboard.html`** (écran
  d'accueil du rôle Administrateur) et le CSS associé dans `base.html`
  (nouvelles règles scopées, voir "Stratégie CSS" ci-dessous).
- Aucune autre page admin (`liste_utilisateurs`, `rapports`, etc.) n'est
  concernée. Aucune vue (`views.py`) ni modèle n'est modifié — la vue
  `dashboard` continue de fournir exactement le même contexte
  (`montant_regle`, `total_patients`, `derniers_comptes`,
  `prestataires_carte`, etc.).
- Les 3 autres dashboards (Assuré/Médecin/Pharmacien) et la sidebar
  partagée (`base.html`) ne sont pas concernés visuellement.

## Structure de la page (haut en bas)

1. **`.page-title`** (h1 "Dashboard Administrateur" + sous-titre) — **inchangé**,
   reste sur le fond clair standard, cohérent avec toutes les autres pages de
   l'app. Le canevas sombre commence seulement après.
2. **Nouveau conteneur `.dash-command`** — grand panneau arrondi à fond
   navy (dégradé dérivé de `--primary-dark`/`--primary-strong`, pas de
   nouvelle teinte). Englobe tout le reste du contenu de la page. Toutes
   les redéfinitions sombres de `.panel`, `.dash-stat`, `.dash-pill`,
   `.button`, tableaux, etc. sont écrites imbriquées sous `.dash-command`
   (`.dash-command .panel { ... }`) — jamais en modifiant les règles de
   base de ces classes, pour ne rien changer sur les 3 autres dashboards
   ni sur les autres pages admin qui réutilisent ces mêmes classes.
3. **Bandeau "Aujourd'hui" compact** — une ligne (pulse-dot + 3 chiffres :
   rendez-vous, consultations, prises en charge en attente), remplace le
   panel dédié actuel. Simplification actée : aucun test ne dépend du
   markup de cette section (seulement des valeurs de contexte), libre de
   restructurer.
4. **Hero paiements** — garde le sparkline Chart.js existant
   (`tendance_consultations`, canvas `#graphe-tendance-consultations`,
   même script), ajoute un tracé de pouls décoratif en fond derrière le
   montant réglé. `montant_regle`, `montant_non_regle`, `taux_reglement`
   affichés via les mêmes filtres/conditions Django qu'aujourd'hui (voir
   contraintes).
5. **Grille de 6 KPI** (Assurés gérés, Médecins actifs, Pharmaciens actifs,
   Prestataires partenaires, Consultations, Ordonnances émises) en
   tuiles "verre" sur fond sombre — **libellés complets conservés**, pas de
   version raccourcie (voir contraintes).
6. **Actions rapides + Comptes et gouvernance** (2 colonnes) — cartes
   sombres, mêmes 4 actions et mêmes 2 chiffres qu'aujourd'hui, mêmes
   liens (dont `?statut=actif` / `?statut=inactif`, testés).
7. **4 listes condensées en grille 2×2** (Derniers assurés, Suivi des
   prises en charge, Derniers comptes créés, Derniers prestataires
   ajoutés) remplacent les 4 tableaux à bordures grises actuels. Même
   nombre d'éléments affichés qu'aujourd'hui (queryset inchangé côté vue),
   mêmes états vides (`{% illustration_vide %}` + CTA), mêmes libellés de
   statut (`dash-pill`/chip équivalent).
8. **Carte réseau de prestataires** — Leaflet/OpenStreetMap réel,
   inchangé fonctionnellement (mêmes données `prestataires_carte`, mêmes
   couleurs par type, mêmes popups construits via `textContent`).
   `id="carte-reseau-admin"` **conservé à l'identique** (testé, et utilisé
   par le script d'init Leaflet). Habillage visuel sombre autour de la
   carte (fond du panneau, légende) pour rester dans l'esprit du "poste de
   pilotage" ; la carte elle-même (tuiles OSM) reste celle du fournisseur,
   pas de thème sombre sur les tuiles.

## Contraintes à préserver (couvertes par `tests.py`, classe `DashboardAdminTests`)

Ne pas casser ces assertions existantes — elles doivent continuer à passer
sans modification :

- `'—'` et `'0\xa0FCFA'` présents quand aucune donnée (logique
  `{% if taux_reglement is not None %}...{% else %}—{% endif %}` et filtre
  `franc_cfa`, non touchés).
- Libellé exact **"Pharmaciens actifs"** dans la grille KPI (pas de version
  raccourcie — point à corriger par rapport à la maquette initiale, qui
  l'avait abrégé en "Pharmaciens").
- Titre **"Derniers comptes créés"** (texte exact, `assertContains` fait un
  match partiel sur "Derniers comptes cr").
- `id="carte-reseau-admin"` sur le conteneur de la carte.
- Texte état vide **"Aucun prestataire partenaire géolocalisé…"**.
- Liens gouvernance avec `href="...liste_utilisateurs?statut=actif"` et
  `?statut=inactif`.

## Stratégie CSS

Tout le CSS de l'app vit dans le `<style>` de `base.html` (pas de dossier
`static/`, cf. section Design system de `CLAUDE.md`) et ce fichier est
partagé par les 4 rôles. Les nouvelles règles sombres doivent donc être
**scopées sous `.dash-command`** (sélecteur composé, ex.
`.dash-command .panel`, `.dash-command .dash-stat`), jamais en modifiant les
règles de base de `.panel`/`.dash-stat`/`.button`/`.dash-pill` — ces classes
restent utilisées telles quelles par `dashboard_assure.html`,
`dashboard_medecin.html`, `dashboard_pharmacien.html`, `rapports.html`,
`liste_*.html`, etc.

Palette : uniquement les tokens existants
(`--primary-dark`, `--primary-strong`, `--primary`, `--primary-accent`,
`--accent`, `--primary-soft`). Pour le texte/bordures sur fond sombre,
réutiliser les tokens déjà conçus pour ce contexte (sidebar) plutôt que
d'inventer de nouvelles valeurs rgba : `--sb-text-muted`, `--sb-text-faint`,
`--sb-hover`, `--sb-border`. Un seul nouveau token est acceptable si
nécessaire pour le texte principal clair sur fond sombre (valeur déjà
documentée dans `CLAUDE.md` pour la croix du logo sur fond sombre,
`#EFF4F3` — pas une couleur inventée).

## Accessibilité

- Contraste texte clair / fond navy vérifié au même niveau d'exigence que
  le reste de l'app (`base.html` contient déjà des commentaires de
  vérification de contraste sur `--primary-strong`, même rigueur attendue
  ici pour les nouveaux textes sur fond sombre).
- Le tracé de pouls animé (hero) respecte `prefers-reduced-motion` (déjà
  géré globalement dans `base.html` pour `.pulse-dot`, même règle à
  appliquer à la nouvelle animation de tracé).
- Focus clavier visible sur tous les éléments interactifs des nouvelles
  listes condensées (mêmes règles `:focus-visible` que le reste de l'app).

## Non-objectifs

- Pas de mode sombre basculable par l'utilisateur (`color-scheme: light`
  reste déclaré tel quel dans les `<head>` de l'app) — c'est un choix de
  composition fixe pour cette page précise, pas un thème système.
- Pas de changement du comportement Leaflet/Chart.js au-delà de l'habillage
  visuel (pas de nouvelles données, pas de nouveaux endpoints).
- Pas de nouvelle app/route/permission.

## Tests

- `python manage.py test Plateform_medicale` doit continuer à passer sans
  modification (aucun changement de contexte/comportement serveur).
- Vérification manuelle via `runserver` : connexion admin, contrôle visuel
  du rendu, contrôle des liens (actions rapides, gouvernance, "Voir tout"),
  contrôle des états vides (aucun assuré / aucune prise en charge / aucun
  prestataire géolocalisé).
