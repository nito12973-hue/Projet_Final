# Refonte du Dashboard Administrateur — spec de design

Date : 2026-08-14
Direction retenue : **B — Clinique claire**

---

## 1. Objectif

Faire du Dashboard Administrateur un poste de pilotage qui ouvre sur ce qu'il
y a à traiter, et non sur des compteurs inertes. Le résultat doit se lire
comme un logiciel SaaS médical, pas comme un gabarit générique.

Référence visuelle demandée (fichier Figma « ATS Resume Analyzer Dashboard ») :
**inaccessible** (HTTP 403, Figma bloque l'accès automatisé aux fichiers
Community). Validé avec l'utilisateur : on travaille sur des principes de
dashboard SaaS et sur un audit du rendu réel, pas sur une copie de cette
référence. Même situation qu'au 2026-08-09 (8ᵉ/9ᵉ passes).

## 2. Périmètre

Dans le périmètre :

- `dashboard.html` — refonte complète de la disposition.
- `base.html` — nouvelle barre supérieure (header) + ajustements sidebar.
  Le shell étant partagé, les 4 rôles en bénéficient.
- **Deux nouvelles pages admin** : `liste_rendez_vous` et `liste_ordonnances`
  (décision utilisateur du 2026-08-14, voir §6.9).
- `views.py`, `urls.py` — contexte enrichi, processeur de contexte, deux vues.
- `tests.py` — couverture des nouveaux agrégats, du processeur et des deux vues.

Hors périmètre :

- Les pages `liste_*` existantes et leurs tableaux/filtres.
- La carte Leaflet des prestataires : elle **reste** sur `liste_prestataires`
  (décision de la 8ᵉ passe, confirmée le 2026-08-14). Le dashboard signale
  seulement le taux de couverture réel des coordonnées.
- Les dashboards Assuré / Médecin / Pharmacien (ils héritent seulement du
  nouveau header).
- Toute modification de rendez-vous ou d'ordonnance depuis l'admin : les deux
  nouvelles pages sont en **lecture seule**. Changer un statut de rendez-vous
  reste l'affaire du médecin, valider une délivrance celle du pharmacien.

Contraintes : structure du projet, modèles, permissions et logique métier
**inchangés**. Aucune migration. Les routes existantes sont toutes conservées ;
deux routes sont ajoutées.

## 3. Constat de l'audit

Audit mené sur rendu navigateur réel (Edge headless via CDP, session admin),
1440 px et 390 px, et non sur lecture de code.

1. Le tracé décoratif `.dc-hero-trace` traverse « 43 500 FCFA » et « 69 % » —
   effet de texte barré.
2. Le hero est vide sur ~60 % de sa largeur ; la légende de la sparkline est
   posée par-dessus la zone du graphique.
3. « Actions rapides » est deux fois plus haute que son contenu : le 4ᵉ bouton
   passe seul à la ligne.
4. Les 6 cartes KPI sont des compteurs sans tendance ni information
   secondaire ; `consultations_7j` / `ordonnances_7j` ne s'affichent pas
   quand ils valent 0.
5. Un liseré terracotta distingue 2 cartes KPI sans que rien ne l'explique.
6. Aucune barre supérieure : ni recherche, ni notifications, ni menu
   utilisateur, ni fil d'ariane.
7. La page ouvre sur « Aujourd'hui : 0 rendez-vous, 0 consultations » alors
   que des demandes attendent depuis 26 jours.
8. Mobile : les titres de panneaux se cassent sur 3 lignes à côté de leur
   bouton « Voir tout ».

## 4. Signaux réels non exploités

Relevés dans la base au 2026-08-14. Tous calculables sans migration :

| Signal | Valeur | Source |
|---|---|---|
| Ordonnances sans délivrance | 6 sur 13 | `Ordonnance.objects.filter(delivrance__isnull=True)` |
| Rendez-vous à confirmer | 5 | `RendezVous.Statut.DEMANDE` |
| Prestataires sans coordonnées | 8 sur 11 | `latitude` ou `longitude` nulle |
| Assurés principaux sans plan | 4 sur 15 | `plan_couverture__isnull=True` |
| Répartition principaux / ayants droit | 15 / 11 | `Patient.type_beneficiaire` |
| Médecins sans prestataire | 3 | `prestataire__isnull=True` |

## 5. Direction artistique B — « Clinique claire »

### Principe

Le fond de page passe au clair. La sidebar navy est conservée. Le sombre
n'est plus le fond par défaut : il est réservé à **un seul bandeau**, « À
traiter maintenant ». Le contraste devient un geste délibéré au service de
la hiérarchie, au lieu d'être un décor.

Cohérent avec `landing.html` et `base_auth.html`, restés clairs.

### Jetons de couleur

Réutilise la palette SantéSN existante ; aucune teinte nouvelle inventée.

```
Fond de page       #f2f6f6   neutre légèrement teinté teal, pas un gris pur
Surface (carte)    #ffffff
Surface secondaire #f7fafa
Bordure            #e0e9e9
Encre (titres)     #0b2027   --primary-dark existant
Texte courant      #294249
Texte discret      #6b858c
Sidebar / bandeau  #0b2027   --primary-dark existant
Accent             #0e7c86   --primary existant
Accent clair       #4fb8ae   --primary-accent existant
Urgence            #e0824f   --accent existant
```

Couleurs sémantiques, distinctes de l'accent de marque :

```
Réglé / validé    texte #1f8a5c  fond #e6f5ee
En attente        texte #9a6a10  fond #fdf3e0
Refusé            texte #b3352b  fond #fbebe9
Neutre            texte #6b858c  fond #eef3f3
```

Contraste à vérifier en fin d'implémentation : chaque couple texte/fond
doit atteindre au moins 4.5:1.

### Typographie

Inchangée : Manrope (titres), Public Sans (texte), IBM Plex Mono (chiffres).
IBM Plex Mono, jusqu'ici « importée mais réservée à un usage futur », prend
enfin son rôle : tous les nombres et montants, avec `font-variant-numeric:
tabular-nums`.

Correctif : le monospace actuel avec `letter-spacing` négatif produit des
écarts disgracieux sur « 96 500 FCFA ». L'unité (« FCFA ») passe en Public
Sans, à taille réduite et en couleur discrète, à côté du nombre.

### Disposition

Colonne unique, sections empilées, séparées par des intertitres discrets en
capitales espacées. De haut en bas :

1. **En-tête de page** — titre, date du jour.
2. **Bandeau « À traiter maintenant »** (navy) — 4 files d'attente.
3. **Couverture & finances** — carte Paiements (2/3) + carte Assurés (1/3).
4. **Activité** — 5 cartes KPI.
5. **Deux listes** — prises en charge récentes + derniers comptes.
6. **Bas de page** — Fiches à compléter (2/3) + Actions rapides (1/3).

Le sélecteur de période présent sur les maquettes est **retiré** : `rapports`
porte déjà la bascule 30 j / 6 mois / 5 ans, et la dupliquer ici imposerait
de recalculer tous les agrégats de la page par période, ce qui n'a pas été
demandé.

## 6. Contenu écran par écran

### 6.1 Barre supérieure (`base.html`, tous rôles)

- Fil d'ariane : « Administration / Tableau de bord ».
- Champ de recherche → soumet en GET vers `liste_utilisateurs?q=`.
  Libellé **« Rechercher un utilisateur »**. Les filtres de cette vue
  (`role`, `statut`, `q`) vivent dans le helper `_filtrer_utilisateurs`.
  Champ **masqué pour les rôles non-admin**, qui n'ont pas accès à cette vue.
- Cloche de notifications → `mes_notifications`, avec le nombre de
  notifications non lues **de l'utilisateur connecté**. Vaut pour les 4 rôles.
- Pastille utilisateur : initiales, nom, rôle. Liens vers
  `changer_mot_de_passe` et `logout`.
- Sur mobile : fil d'ariane et recherche disparaissent, le bouton d'ouverture
  du tiroir existant reprend sa place à gauche.

### 6.2 Bandeau « À traiter maintenant »

Quatre tuiles, **chacune menant à une liste filtrée réellement existante** :

| Tuile | Chiffre | Destination (vérifiée) |
|---|---|---|
| Prises en charge en attente | compte + ancienneté max | `liste_prises_en_charge?statut=en_attente` |
| Rendez-vous à confirmer | `rdv_a_confirmer` | `liste_rendez_vous?statut=DEMANDE` (§6.9) |
| Ordonnances non délivrées | `ordonnances_non_delivrees` | `liste_ordonnances?delivrance=non` (§6.9) |
| Règlements en attente | compte + montant | `liste_paiements?statut=non_regle` |

La tuile « prises en charge » prend le traitement « urgent » (liseré et texte
terracotta) dès qu'une demande dépasse 7 jours d'ancienneté. Si les quatre
files sont vides, le bandeau affiche un état vide explicite (« Rien en
attente. ») plutôt que quatre zéros.

### 6.3 Carte Paiements

- Suppression du tracé décoratif qui traverse le texte.
- Montant principal, deux montants secondaires séparés par un filet vertical.
- Sparkline Chart.js conservée (`_montants_regles_par_jour()`, déjà en place),
  avec grille horizontale discrète, extrémité marquée, et **légende sous
  l'axe**, plus par-dessus le tracé.
- Ajout de « Facturé au total » = réglé + non réglé, qui donne son sens au
  taux de règlement.

### 6.4 Carte Assurés couverts

Nouvelle. Répartition principaux / ayants droit — donnée centrale du sujet du
projet, absente de toute l'application :

- Total des personnes couvertes.
- Barre proportionnelle à deux segments.
- Légende chiffrée avec pourcentages.
- Mention d'alerte si des principaux sont sans plan de couverture.

### 6.5 Cartes KPI

Cinq cartes, chacune portant une information secondaire vraie :

| Carte | Principal | Secondaire |
|---|---|---|
| Consultations | `total_consultations` | micro-tendance 30 j |
| Ordonnances | `total_ordonnances` | « N délivrées » |
| Médecins | `total_medecins` | « N sans prestataire » |
| Pharmaciens | `total_pharmaciens` | « N sans pharmacie » |
| Prestataires | `total_prestataires` | répartition par type |

Le liseré terracotta inexpliqué disparaît. Seule l'information secondaire
passe en ambre quand elle signale un manque.

### 6.6 Listes

- **Prises en charge récentes** : les demandes `en_attente` remontent en
  premier (tri par statut puis par date), avec leur ancienneté en jours.
- **Derniers comptes créés** : le rôle passe en badge à droite et le
  sous-titre porte « N actifs, N désactivés », ce qui absorbe la carte
  « Comptes et gouvernance » actuelle et libère sa place.

### 6.7 Fiches à compléter

Quatre entrées cliquables :

| Entrée | Destination |
|---|---|
| Prestataires sans coordonnées | `liste_prestataires?localisation=sans` |
| Assurés sans plan | `liste_patients?type=PRINCIPAL` |
| Médecins sans prestataire | `liste_medecins` |
| Pharmaciens sans pharmacie | `liste_pharmaciens` |

`liste_medecins` et `liste_pharmaciens` n'ont aucun filtre GET : le lien mène
à la liste complète. C'est assumé — mieux vaut une destination utile qu'un
chiffre mort. Chaque entrée disparaît quand son compteur est à zéro ; si les
quatre sont à zéro, le panneau entier n'est pas rendu.

### 6.8 Actions rapides

Six actions en grille de deux colonnes, avec icônes, à hauteur de contenu :
nouvel assuré, nouveau médecin, prestataire, prise en charge, rapports,
importer. Supprime la zone morte actuelle.

### 6.9 Deux nouvelles pages admin (lecture seule)

Motif : « 6 ordonnances non délivrées » et « 5 rendez-vous à confirmer » sont
les deux signaux les plus parlants de la base, mais l'administrateur n'avait
aucun écran où les consulter. Sans ces pages, les tuiles correspondantes
seraient des chiffres sans destination.

**`liste_rendez_vous`** — `path('rendez-vous/', …, name='liste_rendez_vous')`,
`@admin_required`.

- Colonnes : date et heure, patient, médecin, prestataire, motif, statut.
- Filtres GET : `statut` (DEMANDE / CONFIRME / ANNULE / TERMINE), `q`
  (nom du patient ou du médecin).
- Tri via le helper `_trier` existant, tri par défaut `-date_heure`.
- `select_related("patient", "medecin", "prestataire")` — évite le N+1.
- Template `liste_rendez_vous.html`, calqué sur les templates de liste
  existants, réutilisant `.filtres`, `.badge`, `.etat-vide`.

**`liste_ordonnances`** — `path('ordonnances/', …, name='liste_ordonnances')`,
`@admin_required`.

- Colonnes : date, patient, médecin, code de vérification, statut de
  délivrance, pharmacien et date de délivrance le cas échéant.
- Filtres GET : `delivrance` (`oui` / `non`), `q` (patient ou `code_qr`).
- Tri par défaut `-date_creation`.
- `select_related("consultation__patient", "consultation__medecin",
  "delivrance__pharmacien")`.
- Template `liste_ordonnances.html`, même patron.
- Pas de vue de détail : la liste porte toute l'information utile. Le QR
  n'est pas affiché ici — il n'a de sens qu'en pharmacie.

Les deux entrées rejoignent la section **OPÉRATIONS** de la sidebar, qui
devient : Prises en charge · Rendez-vous · Ordonnances · Paiements.

Aucune action d'écriture n'est exposée : la logique métier (confirmation d'un
rendez-vous par le médecin, délivrance par le pharmacien) reste intacte.

## 7. Données à ajouter à `dashboard()`

Simples `count()` / `aggregate()` sur des champs indexés. Aucune migration.

```
rdv_a_confirmer               RendezVous statut=DEMANDE
ordonnances_non_delivrees     Ordonnance delivrance__isnull=True
total_delivrances             Delivrance count
paiements_non_regles_nb       Paiement statut=NON_REGLE
montant_total_facture         réglé + non réglé (déjà calculé, à exposer)
patients_principaux           Patient type=PRINCIPAL
ayants_droit                  Patient type != PRINCIPAL
assures_sans_plan             Patient PRINCIPAL, plan_couverture null
medecins_sans_prestataire     Medecin prestataire null
pharmaciens_sans_prestataire  Pharmacien prestataire null
prestataires_sans_coordonnees Prestataire latitude|longitude null
prestataires_par_type         values('type_prestataire').annotate(Count)
```

Regrouper ce qui peut l'être en une seule requête par modèle, via
`aggregate(Count(..., filter=Q(...)))`, plutôt qu'un `count()` par ligne :
les trois comptages de `Patient` tiennent en une requête, ceux de `Paiement`
sont déjà agrégés. Objectif : ne pas dépasser environ cinq requêtes
supplémentaires par rapport à l'existant.

`dernieres_prises_en_charge` change d'ordre : `en_attente` d'abord, puis par
date décroissante, et expose l'ancienneté en jours.

## 8. Processeur de contexte du shell

Le header et la sidebar ont besoin de compteurs sur **toutes** les pages.

Fonction `contexte_global(request)` définie dans `views.py` (et non dans un
nouveau fichier, pour respecter la structure figée décrite dans `CLAUDE.md`),
enregistrée dans `config/settings.py` sous
`TEMPLATES.OPTIONS.context_processors`.

Elle fournit :

- `nb_notifications_non_lues` — pour tout utilisateur authentifié.
- `nb_prises_en_charge_attente`, `nb_paiements_non_regles`,
  `nb_rdv_a_confirmer`, `nb_ordonnances_non_delivrees` — pour le rôle ADMIN
  uniquement (pastilles de la sidebar).

Retourne un dictionnaire vide pour un visiteur anonyme : aucune requête sur
la landing page ni sur l'écran de connexion. Les statuts interrogés sont
indexés (`db_index=True` vérifié sur `PriseEnCharge.statut`,
`Paiement.statut`, `RendezVous.statut`).

Coût : jusqu'à cinq `COUNT` par page admin. Si cela s'avère trop lourd à la
mesure, replier les pastilles de sidebar sur les deux compteurs les plus
utiles (prises en charge, paiements) et laisser les deux autres au seul
dashboard.

Alternative écartée : un fichier `context_processors.py` dédié, plus
idiomatique en Django mais qui ajoute un fichier à une arborescence décrite
comme définitive.

## 9. Responsive

| Largeur | Comportement |
|---|---|
| ≥ 1180 px | Disposition complète : 4 tuiles, 5 KPI, bandes 1.55fr / 1fr |
| 900–1180 px | Tuiles sur 2 colonnes, KPI sur 3, bandes empilées |
| 640–900 px | KPI sur 2 colonnes, tout le reste sur une colonne |
| < 640 px | Une colonne partout ; header réduit au tiroir + cloche |

Correctif spécifique : les en-têtes de panneau passent en colonne sous
900 px pour que le titre cesse de se casser sur trois lignes à côté du
bouton « Voir tout ».

Les tableaux des deux nouvelles pages sont placés dans un conteneur
`overflow-x: auto` : le corps de page ne défile jamais horizontalement.

Le comportement existant de la sidebar (réduction desktop persistée en
`localStorage`, tiroir mobile) est conservé tel quel.

## 10. Animations et micro-interactions

- Entrée des cartes en cascade : réutiliser `@keyframes entree-carte`
  existant, décalages courts, une seule fois au chargement.
- Survol des éléments cliquables : `translateY(-2px)` + bordure accentuée,
  uniquement sur ce qui est réellement cliquable.
- Anneau de focus clavier : jeton existant, vérifié sur les nouveaux
  éléments du header.
- `@media (prefers-reduced-motion: reduce)` : neutralise animations et
  transformations. À ajouter, absent aujourd'hui.

Pas d'animation permanente ni d'effet ambiant : une page d'administration se
consulte plusieurs fois par jour.

## 11. Accessibilité

- Chaque tuile chiffrée est un lien avec un `aria-label` explicite reprenant
  chiffre et libellé (motif déjà en place, à conserver).
- Le statut n'est jamais porté par la seule couleur : le badge contient
  toujours son libellé texte.
- Contraste minimum 4.5:1 pour tout texte, badges sémantiques et texte
  discret sur le bandeau navy compris.
- La cloche de notifications annonce son compteur en texte accessible.
- Les deux nouveaux tableaux utilisent `<th scope="col">` et une légende.

## 12. Tests

À ajouter dans `tests.py` :

1. Le contexte de `dashboard` contient les nouvelles clés avec les bonnes
   valeurs, sur un jeu de données construit pour l'occasion (une ordonnance
   sans délivrance, un rendez-vous `DEMANDE`, un patient sans plan, un
   prestataire sans coordonnées).
2. Base vide : la page se rend sans erreur et affiche les états vides.
3. Permissions inchangées : un non-admin est toujours redirigé depuis
   `dashboard`, `liste_rendez_vous` et `liste_ordonnances`.
4. `liste_rendez_vous` : le filtre `statut=DEMANDE` ne renvoie que les
   demandes ; la recherche `q` trouve par nom de patient.
5. `liste_ordonnances` : le filtre `delivrance=non` ne renvoie que les
   ordonnances sans délivrance.
6. `contexte_global` renvoie le compteur de notifications du seul utilisateur
   connecté, et n'expose les clés admin qu'au rôle ADMIN.
7. Visiteur anonyme : `contexte_global` ne déclenche aucune requête.

Commande : `python manage.py test Plateform_medicale`, exécutée en
**synchrone** (voir la note correspondante dans la mémoire projet : une suite
lancée en arrière-plan est morte silencieusement trois fois sur ce projet).

## 13. Vérification visuelle

Chaque étape est capturée au navigateur réel (Edge headless via CDP, script
`capture.py` du bac à sable) avant d'être considérée terminée, à 1440 px et
390 px au minimum. Un diagnostic « hiérarchie visuelle » ou « espaces vides »
fondé sur la seule lecture du CSS n'est pas fiable.

## 14. Ordre de livraison proposé

1. Les deux pages admin (`liste_rendez_vous`, `liste_ordonnances`) + leurs
   entrées de sidebar et leurs tests — le dashboard en dépend pour ses liens.
2. Le processeur de contexte + la barre supérieure dans `base.html`.
3. La refonte de `dashboard.html` et l'enrichissement de `dashboard()`.
4. Passe finale : contrastes, responsive, `prefers-reduced-motion`, captures
   de vérification, mise à jour de `FONCTIONNEMENT.txt` et `CLAUDE.md`.

Chaque étape se termine par `python manage.py check`, la suite de tests et
une capture visuelle.

## 15. Note sur le travail en cours mis de côté

Un travail non commité touchant `base.html`, `dashboard.html`, `views.py` et
`config/settings.py` a été mis de côté avant cette refonte :

```
git stash list  →  stash@{0}  wip-dashboard-admin-avant-refonte-2026-08-14
```

Il contenait des idées qui recoupent cette spec (regroupement des KPI par
section, panneau « Qualité des données ») mais avait perdu les accents
français du texte modifié. Cette spec les reprend proprement. Le stash pourra
être supprimé une fois la refonte livrée et validée.

Il contenait aussi des modifications de `config/settings.py` sans rapport avec
le design (`STATIC_ROOT`, `DEFAULT_AUTO_FIELD`, `SECURE_PROXY_SSL_HEADER`,
lecture tolérante de `DEBUG`). **Elles ne sont pas reprises ici** : ce sont des
changements de configuration et de déploiement, à traiter séparément et sur
décision explicite.
