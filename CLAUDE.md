# SantéSN — plateforme de prise en charge médicale
## Thème du projet
Plateforme numérique de gestion de la prise en charge médicale des assurés d'une
assurance santé et de leurs ayants droit (conjoint, enfants). Un employé assuré
enregistre ses ayants droit, chacun ayant une carte/identifiant de prise en
charge. Les frais médicaux sont couverts partiellement ou totalement par
l'assurance (part patient éventuelle, ex. 10%). La plateforme intègre un réseau
de prestataires (hôpitaux, cliniques, pharmacies) partenaires ; l'assuré ou ses
ayants droit choisissent un prestataire et prennent rendez-vous en ligne. Les
médecins génèrent des ordonnances sous forme de QR code, scanné en pharmacie
pour valider et suivre la délivrance des médicaments.

Toute fonctionnalité doit rester dans ce périmètre (gestion des utilisateurs et
des rôles, prise en charge, prestataires, rendez-vous, ordonnances/QR,
pharmacie). Ne pas dériver vers des sujets hors thème.

## Structure du projet (définitive, ne jamais modifier)

```
Plateform_medicale/     # Toute la logique métier (une seule app Django)
├── migrations/
├── templates/           # Templates à plat, pas de sous-dossier par app
├── static/
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── tests.py
├── urls.py
└── views.py

config/                  # Configuration Django uniquement
├── settings.py
├── urls.py
├── wsgi.py
└── asgi.py
```

Une seule app Django (`Plateform_medicale`). `config/` ne contient que la
configuration. Ne jamais créer d'app supplémentaire sans justification forte
(l'app `accounts` qui existait a été fusionnée dans `Plateform_medicale` — voir
historique git — car le cahier des charges exige une seule app).

## Méthode de travail (imposée par l'utilisateur, à suivre pour chaque module)

1. **Analyse** : lire l'existant (modèles, vues, urls, forms, templates),
   détecter erreurs/doublons, ne rien modifier.
2. **Proposition** : fichiers concernés, pourquoi, impacts. Attendre validation
   avant de coder si le changement est structurant ou ambigu.
3. **Développement** : un seul module à la fois, ne pas casser l'existant,
   réutiliser le code/CSS existant, code propre, commentaires seulement si
   nécessaire.
4. **Vérification** : `python manage.py check`, `python manage.py test
   Plateform_medicale`, test manuel (curl/runserver) si UI concernée.
5. **Résumé** : fichiers créés/modifiés, fonctionnalités, tests, prochaines
   étapes.

Ne jamais développer plusieurs modules en même temps. Voir "État d'avancement"
ci-dessous pour la progression réelle par rapport aux 15 phases du plan
directeur.

## État d'avancement (plan directeur en 15 phases)

Statut : ✅ fait · ⏳ partiel/à compléter · 🔄 continu.

1. ✅ Analyse fonctionnelle — audit initial du projet et du cahier des charges.
2. ✅ Audit / préparation — fusion de l'app `accounts` dans `Plateform_medicale`,
   secrets déplacés dans `.env`.
3. ✅ Authentification / Sécurité — connexion unique, `setup_wizard` (premier
   admin uniquement), limitation des tentatives de connexion, changement de
   mot de passe en libre-service pour chaque rôle.
4. ✅ Landing page — hero, services, parcours, à propos, contact, footer,
   responsive ; icônes SVG (plus aucun émoji, y compris sur `base_auth.html`) ;
   section "Accès" réécrite (l'admin crée les comptes, pas de mode démo promis).
5. ✅ Dashboard Administrateur — Gestion des utilisateurs (CRUD, rôles,
   activation, réinitialisation mot de passe, export Excel), CRUD
   patients/médecins/services/prestataires/prises en charge/plans de
   couverture, notifications. Deux écrans **en lecture seule** complètent le
   suivi : `liste_rendez_vous` (filtres `statut`/`q`) et `liste_ordonnances`
   (filtre `delivrance` oui/non — une ordonnance jamais retirée en pharmacie
   n'apparaissait sur aucun écran) et `liste_consultations` (recherche,
   date, filtre `couverture`). L'admin n'y écrit rien : confirmer un
   rendez-vous reste au médecin/assuré, valider une délivrance au pharmacien.
   **`liste_consultations` n'affiche ni diagnostic ni traitement** : données
   médicales, réservées au médecin qui les a saisies (même règle que
   `fiche_patient_medecin`). L'admin voit l'acte et sa facturation, pas son
   contenu — ne pas y ajouter ces colonnes. Son filtre `couverture` reprend
   la règle de `Paiement.calculer_pour` (couvert seulement si la prise en
   charge est `validee`) et répond à une question qu'aucun autre écran ne
   pose : quels soins sont restés à 100% à la charge du patient.
   Le tableau de bord lui-même ouvre sur les **files d'attente** (refonte
   « Clinique claire », 2026-08-15) et non sur les compteurs du jour.
6. ✅ Dashboard Assuré — profil, ayants droit, rendez-vous, ordonnances,
   historique et **suivi des prises en charge** (`mes_prises_en_charge_assure`).
   L'assuré voyait la conséquence (sa part à payer) sans jamais voir la cause :
   l'état de sa demande, qui décide pourtant s'il paie 10% ou 100%. L'écran
   n'affiche que ce que porte le modèle (patient, date, motif, statut) ; les
   montants viennent des consultations rattachées, jamais de la prise en
   charge — **ne pas y ajouter prestataire, montant ou motif de refus** : ces
   champs n'existent pas.
7. ✅ Dashboard Médecin — agenda, patients, consultations, ordonnances QR.
8. ✅ Dashboard Pharmacien — scan d'ordonnance, validation de délivrance,
   historique.
9. ✅ Rendez-vous — livré en transverse dans les phases 5-8 (demande,
   confirmation, annulation, statuts).
10. ✅ Consultations — livré dans la phase 7 (diagnostic, traitement,
    médicaments liés à une prise en charge).
11. ✅ Ordonnances / QR — livré dans les phases 7-8 (QR code SVG généré par
    ordonnance, scan et validation en pharmacie).
12. ✅ Prise en charge et paiements — modèle `Paiement` (1-1 avec
    `Consultation`) : montant total, part assurance / part patient calculées,
    statut de règlement, historique. Voir "Paiements" ci-dessous.
13. ✅ Rapports / statistiques — vue `rapports` avec graphiques Chart.js
    (consultations par mois, répartitions par role/type/statut) et exports
    dédiés (`exporter_rapports_excel` : un onglet par tableau, `exporter_rapports_pdf`
    via reportlab). Voir "Rapports" ci-dessous.
14. 🔄 Tests — suite de tests exécutée et étendue à chaque module livré
    (`python manage.py test Plateform_medicale`) ; pas de session dédiée
    "audit de couverture" menée à part.
15. ✅ Documentation / finalisation — `GUIDE_UTILISATEUR.md` : guide par rôle
    (Admin/Assuré/Médecin/Pharmacien) livré. `DEMO_USERS.md` n'existe pas (ni
    sur disque ni dans l'historique git, voir section "Comptes de
    démonstration").

## Fonctionnalités additionnelles (post plan directeur)

Fonctionnalités livrées après les 15 phases initiales, hors numérotation :

- **Carte de proximité des prestataires** (Assuré) — `Prestataire.latitude`/
  `longitude`, helper `distance_km` (haversine), écran `prestataires_proches`
  (carte Leaflet + tri par distance si le navigateur transmet sa position,
  repli par ville sinon), présélection du prestataire dans le formulaire de
  rendez-vous. Détail technique dans `FONCTIONNEMENT.txt` (modèle, vue,
  templates, règle anti-XSS pour les popups Leaflet).
- **Recherche de lieu sur la carte** (Admin, `ajouter_prestataire` /
  `modifier_prestataire`) — bouton "Rechercher sur la carte" qui combine les
  champs adresse + ville (adresse en premier, plus précis : quartier/
  commune ; interroger la seule ville ne suffisait pas à retrouver des
  lieux précis) et appelle la vue `recherche_lieu_prestataire`
  (relais serveur, même origine que le site) plutôt que Nominatim
  directement depuis le navigateur : un appel client direct s'est révélé peu
  fiable en test (le cache CDN de Nominatim ne fait pas varier ses réponses
  selon `Origin`, d'où un en-tête CORS présent une fois sur deux, et
  `fetch()` ne peut pas porter de User-Agent applicatif identifiant, ce que
  la politique d'usage de Nominatim attend). La vue interroge Nominatim
  côté serveur (`urllib.request`, pas de nouvelle dépendance) avec un
  User-Agent dédié, limité au Sénégal (`countrycodes=sn`), et renvoie un
  JSON minimal (`trouve`/`lat`/`lon`/`nom`). Si le lieu existe dans les
  données OpenStreetMap, la carte se centre dessus et le marqueur se place
  automatiquement (mêmes champs cachés `latitude`/`longitude` que le clic
  manuel sur la carte, qui reste toujours possible — nécessaire pour un
  hôpital/quartier trop précis ou trop récent pour être déjà référencé sur
  OpenStreetMap, la couverture au Sénégal restant inégale en dehors des
  grandes villes/communes). Si le lieu est introuvable ou le service indisponible,
  message inline sous le bouton (pas d'alerte navigateur).

## Journal d'activité (livré)

**Emplacement : Paramètres → Sécurité**, pas le menu latéral — c'est une
fonction d'administration et de sécurité, pas un module métier. Il garde
néanmoins son propre écran (filtres + pagination) ; la section Sécurité en est
le point d'entrée. L'entrée « Paramètres » du menu reste active pendant sa
consultation.

`JournalActivite` (models.py) + écran admin `journal_activite`. Trace **les
décisions administratives et les destructions** — 17 points d'appel, posés
via le helper `journaliser(request, action, objet, details)`.

**Ce qui n'y figure pas est aussi réfléchi que ce qui y figure.** Ne pas
ajouter sans relire cette liste :

- **connexions / navigation** — bruit ; le blocage temporaire a déjà son
  écran (`TentativeConnexion`) ;
- **actes de soin** (consultation, ordonnance, délivrance) — une
  `Consultation` porte déjà son médecin et sa date, une `Delivrance` son
  pharmacien : les réécrire ici les dupliquerait sans rien apprendre ;
- **changement de statut d'un rendez-vous** — travail quotidien du médecin,
  son volume noierait les entrées qui comptent ;
- **créations métier courantes** (service, prestataire…) — la fiche créée
  *est* la trace. On journalise la disparition d'un objet, pas sa naissance.
  **Exception : créer un compte**, qui accorde un accès — décision de
  sécurité, donc journalisée.

**Texte figé, jamais de clé étrangère vers l'objet concerné.** Une FK en
CASCADE effacerait l'entrée en même temps que l'objet supprimé — or c'est
précisément la suppression qu'on veut garder. Même raison pour
`auteur_libelle`, figé à côté de la clé `auteur` (`SET_NULL`) : supprimer le
compte d'un admin ne doit pas effacer la trace de ce qu'il a fait. Deux tests
couvrent ces deux survies.

**Lecture seule partout**, y compris `/admin/` où les trois permissions
(`add`/`change`/`delete`) sont refusées : un journal d'audit qu'un
administrateur peut retoucher ne prouve plus rien. Ne pas y ajouter d'action
d'écriture.

**Journaliser APRÈS le succès, jamais avant** — sauf pour une suppression, où
l'appel précède `delete()` parce qu'après, l'objet n'a plus de libellé à
citer. Un déblocage sans effet (compte déjà débloqué) n'écrit rien : une
entrée ferait croire à une intervention.

Un test vérifie la **couverture** des 6 écrans de suppression : un journal
partiel donnerait l'illusion d'une trace exhaustive, ce qui est pire que pas
de journal du tout.

## Carte de prise en charge (livrée)

Écran admin `carte_patient` (recto/verso, imprimable) + `carte_scan` (cible du
QR). **La carte appartient à un bénéficiaire, pas à un compte** :
`numero_carte` est porté par `Patient`, jamais par `User`. Un ayant droit a
une carte sans avoir de compte, un médecin a un compte sans avoir de carte —
d'où l'action rattachée au module **Assurés** et non à Utilisateurs.

Elle n'affiche **que des champs existants** (logo, numéro, nom, type, taux,
plan). **Ni photo ni date d'expiration : ces champs n'existent pas.** Ne pas
les ajouter à la carte sans les ajouter d'abord au modèle.

Le composant réutilisé est `.carte-assure` (espace assuré), déjà au format
ISO 7810 ID-1 — il n'y a **pas** de seconde carte à maintenir.

**Le QR n'accorde aucun droit.** Il encode l'URL de `carte_scan` ; c'est
`role_required(MEDECIN, PHARMACIEN)` qui protège. `numero_carte` n'est pas un
secret (il est imprimé sur la carte). Portée volontairement différente selon
le rôle : le **pharmacien** ne voit que les ordonnances **non délivrées** (ce
qu'il peut servir), le **médecin** que celles de **ses propres** consultations
(même règle que `fiche_patient_medecin`). Le diagnostic n'est jamais exposé.

**Piège corrigé, à ne pas réintroduire** : `qrcode` écrit ses modules en
`<svg:rect>` **préfixés**. Inliné dans du HTML, un analyseur HTML ne résout pas
les préfixes — le QR sortait en **carré blanc**. Cela touchait aussi les QR
d'**ordonnances**, invisibles depuis toujours. Le helper `_qr_svg` (models.py)
retire le préfixe ; les deux modèles passent par lui. Corollaire : le SVG n'a
**pas de viewBox**, donc sa taille se règle **à la génération** (`box_size` /
`border`) — jamais en CSS, une largeur imposée revide le code.

## Documents de travail (specs / plans)

Les specs et plans d'implémentation générés pendant le développement d'une
fonctionnalité (habituellement sous `docs/superpowers/`) sont **temporaires** :
une fois la fonctionnalité livrée et vérifiée, leur contenu utile (ce qui
change dans le modèle de données, les routes, les décisions d'architecture
non évidentes) est reporté dans `FONCTIONNEMENT.txt`, puis le dossier de
travail est supprimé. Ne pas laisser ces dossiers s'accumuler dans le dépôt :
ce ne sont pas des documents de référence durables, `FONCTIONNEMENT.txt` et
`GUIDE_UTILISATEUR.md` le sont. Un dossier `.superpowers/` peut aussi
apparaître localement pendant le travail (état d'avancement d'un plan) : il
est propre à une session de travail (worktree), pas un document du projet —
ne pas le recréer à la racine du dépôt principal.

## Authentification & rôles

- Connexion unique par email + mot de passe (`Plateform_medicale/views.py`,
  `LoginForm`). Aucune inscription publique.
- `AUTH_USER_MODEL = 'Plateform_medicale.User'`. Rôle stocké en base
  (`User.Role`), jamais choisi à la connexion.
- Rôles actuels : `ADMIN`, `ASSURE` (patient/bénéficiaire), `MEDECIN`,
  `PHARMACIEN`. **`PRATICIEN` n'existe pas encore** — à ajouter uniquement en
  même temps que son propre module (rôle + dashboard + redirection), jamais
  isolément, pour ne pas créer de compte sans destination après connexion.
- `post_login_redirect` route chaque rôle vers son tableau de bord.
- Permissions : décorateurs `admin_required` / `role_required(*roles)` définis
  dans `views.py`.
- Premier admin créé via l'assistant `setup_wizard` (accessible uniquement
  si aucun admin n'existe encore).

## Gestion des utilisateurs (livrée)

Dashboard Admin → Utilisateurs : créer/modifier/activer/désactiver/supprimer un
utilisateur, réinitialiser un mot de passe, attribuer un rôle. Mots de passe
générés automatiquement et affichés une seule fois (aucun backend email
configuré). Garde-fous anti-lockout : un admin ne peut pas changer son propre
rôle, se désactiver ou se supprimer lui-même. Export Excel de la liste filtrée
des utilisateurs (`exporter_utilisateurs_excel`, openpyxl). Chaque rôle peut
changer son propre mot de passe après connexion (`changer_mot_de_passe`,
`PasswordChangeForm` + `update_session_auth_hash` pour ne pas déconnecter
l'utilisateur), indépendamment de la réinitialisation par l'admin.

**Toute fiche métier avec connexion crée son compte automatiquement.**
`ajouter_medecin` et `ajouter_patient` (uniquement pour un assuré
**principal** — jamais pour un ayant droit) créent désormais aussi un
`User` (même email, mot de passe généré, écran `mot_de_passe_genere.html`
réutilisé), en plus de la fiche `Medecin`/`Patient`, pour que la personne
apparaisse dans "Gestion des utilisateurs". Les ayants droit n'ont
volontairement jamais de compte (gérés par leur assuré principal). Un
Pharmacien n'a pas d'écran de création dédié : il n'existe que via
"Gestion des utilisateurs" (rôle Pharmacien), donc toujours avec un compte.
`MedecinForm`/`PatientCreationForm` valident que l'email n'est pas déjà
pris par un `User` existant (pas seulement par un autre `Medecin`).

**Symétrie à la suppression.** `supprimer_medecin` et `supprimer_patient`
(assuré **principal** uniquement — un ayant droit n'a jamais de `User`)
désactivent (`is_active = False`) le `User` lié en plus de supprimer la
fiche métier : sans ça, le compte de connexion restait actif après
suppression (un assuré supprimé pouvait même se reconnecter et se
recréer une fiche `Patient` tout seul via `mon_profil_assure`). Le compte
reste réactivable depuis "Gestion des utilisateurs" si besoin.

## Paiements (livré)

Modèle `Paiement`, en relation 1-1 avec `Consultation`. Créé automatiquement
par `Paiement.calculer_pour()` quand le médecin enregistre une consultation
(`ajouter_consultation_medecin`) : `montant_total` vient de `service.prix`
(0 si aucun service lié), le taux appliqué vient de `patient.taux_couverture`
**uniquement si la `prise_en_charge` liée à la consultation a le statut
`validee`** (sinon le patient règle 100% du montant — règle métier
volontaire, une prise en charge en attente ou refusée ne couvre rien).
Dashboard Admin → Paiements (`liste_paiements`, filtrable par statut,
action "Marquer réglé" avec mode de règlement obligatoire). Le dashboard
Assuré (`mon_historique.html`) affiche la part à charge et le statut de
règlement pour chaque consultation. Les consultations créées directement en
base (fixtures/tests via l'ORM, hors vue) n'ont pas de `Paiement` associé :
les templates gèrent ce cas (`{% if consultation.paiement %}`).

## Cohérence patient ↔ prise en charge

Invariant : `consultation.prise_en_charge.patient == consultation.patient`.
Il vit dans `Consultation.clean()` et `PriseEnCharge.clean()`, **pas dans les
formulaires**. Il était auparavant dans `ConsultationForm.clean()`, donc vérifié
seulement à la **création** et seulement côté app ; deux chemins le cassaient :

- `PriseEnChargeForm` expose `patient` **aussi en modification** — réattribuer
  une prise en charge déjà pourvue de consultations donnait ces soins à
  quelqu'un d'autre, et l'écran assuré « Mes prises en charge » les affichait ;
- `/admin/` enregistre `Consultation` par `admin.site.register()` **sans
  `ModelAdmin` dédié** : le formulaire de l'app y était purement contourné (même
  classe de problème que `SuppressionGereeParLAppMixin`).

Dans les modèles, la règle est rencontrée par **tout** `ModelForm` — app comme
`/admin/` — puisque `_post_clean` appelle `full_clean()`. La `ValidationError`
est indexée par champ pour s'afficher sous `prise_en_charge` (resp. `patient`).
`ConsultationForm.clean()` a été supprimé : la même règle écrite deux fois.

Réattribuer reste **permis tant qu'aucune consultation n'est rattachée** :
corriger un patient choisi par erreur est légitime, déplacer des soins déjà
enregistrés ne l'est pas. `objects.create()` ne déclenche pas `clean()` — les
fixtures et tests ORM peuvent toujours construire l'état incohérent exprès.

## Rapports (livré)

Vue `rapports` (Dashboard Admin) : comptages (utilisateurs par rôle, assurés
par type, rendez-vous par statut, prises en charge par statut, consultations/
ordonnances/délivrances/prestataires partenaires) et trois agrégats de
consultations sur des fenêtres glissantes — `_consultations_par_jour` (30
derniers jours), `_consultations_par_mois` (6 derniers mois) et
`_consultations_par_annee` (5 dernières années), toutes incluant la période
courante. Le graphique "Consultations" bascule entre les trois via des
boutons (`#boutons-periode-consultations`, un seul Chart.js réutilisé —
`data` remplacée + `update()` — pas d'instance recréée à chaque clic).
Graphiques Chart.js (CDN jsdelivr avec intégrité SRI) rendus côté client à
partir de `json_script`, en plus des tableaux existants (pas de
remplacement). Deux exports dédiés, tous deux `@admin_required` et construits
à partir de la même fonction `_donnees_rapports()` que la vue (pas de
duplication de requêtes) : `exporter_rapports_excel` (openpyxl, un onglet par
tableau) et `exporter_rapports_pdf` (reportlab, nouvelle dépendance —
tableaux mis en forme, un par section) — les deux exports ne couvrent que la
vue "par mois" (snapshot statique, pas de bascule de période dans un
document exporté). Ne pas confondre avec `exporter_utilisateurs_excel` qui ne
couvre que la liste des utilisateurs (Dashboard Admin → Utilisateurs).

## Libellés affichés vs valeurs stockées

Les `TextChoices` du projet séparent strictement **la valeur stockée** (1er
élément, en base : `HOPITAL`, `validee`, `non_regle`…) et **le libellé
affiché** (2e élément, accentué : « Hôpital », « Validée », « Non réglé »).
Les filtres GET, les comparaisons et les requêtes utilisent **toujours la
valeur** — jamais le libellé.

**Piège vérifié** : `rapports.html` indexe ses couleurs de graphique **par
libellé** (`COULEURS_STATUT`). Changer un libellé dans `models.py` sans
mettre cette table à jour fait repasser les graphiques en gris, **sans aucune
erreur visible**. Un test le couvre désormais
(`test_table_de_couleurs_des_rapports_suit_les_libelles`). Même vigilance pour
`prestataires_proches.html`, qui écrit ses options de type en dur.

Modifier un libellé génère une migration `AlterField` **no-op** (Django suit
`choices` sans que le schéma change) : la générer et l'appliquer, c'est normal.

## Design system

Un seul shell de dashboard (sidebar + barre supérieure `.topbar`) dans
`base.html`, réutilisé par les 4 rôles (nav conditionnelle selon
`current_role`). La `.topbar` porte le fil d'ariane (dérivé du nom de route
par le filtre `libelle_page` de `templatetags/formats.py` — une seule table à
maintenir, pas un bloc à redéfinir dans chaque template ; une route inconnue
n'affiche rien plutôt qu'un libellé faux), la recherche (admin uniquement,
vers `liste_utilisateurs?q=` : c'est la seule liste qui accepte `q`), les
notifications et le compte. Le bouton du tiroir mobile vit **dans** la
`.topbar` — un seul bouton dans le DOM, ne pas en ajouter un second. Identité "Territoire A +
Croix-Pouls" : palette teal/navy/terracotta SantéSN (`--primary: #0e7c86`
teal vif — bordures/décoratif seulement, `--primary-strong: #095059` teal
foncé — seule variante sûre pour texte/icône blancs en aplat,
`--primary-dark: #0b2027` navy — titres/texte foncé, `--primary-light` /
`--primary-accent: #4fb8ae` texte/icône colorés sur fond sombre + dégradés
décoratifs non-texte, `--accent: #e0824f` terracotta — accent ponctuel
uniquement, jamais en fond/aplat large, ex. ligne de battement de cœur du logo
sur fond sombre), polices Manrope (titres, `h1`) + Public Sans (texte
courant) + IBM Plex Mono (importée, réservée à un usage futur). Menu latéral
desktop réductible (icônes seules, état persistant via `localStorage`),
tiroir mobile, barre de chargement de navigation. `landing.html` et
`base_auth.html` (pages publiques / connexion) ont leur propre CSS autonome
avec les mêmes tokens de palette, mêmes noms `--primary`/`--primary-strong`/
`--primary-dark`/`--primary-light`/`--primary-accent`/`--primary-soft` que
`base.html` (unifié après coup dans `base_auth.html`, qui utilisait au
départ ses propres noms `--vert`/`--vert-fort`/`--vert-fonce`) ; ne
dépendent pas de `base.html`.
Logo/marque "Croix-Pouls" : croix médicale à angles arrondis (deux
rectangles perpendiculaires) traversée en son centre par un tracé de pouls
terracotta (`--accent: #e0824f`, toujours cette teinte quel que soit le
fond). Source unique du mark : tag `{% logo_marque taille=N fond="clair|sombre" %}`
(`templatetags/icones.py`, `{% load icones %}`) — utilisé dans `base.html`
(sidebar), `landing.html` (en-tête, mockup téléphone, pied de page),
`mon_profil_assure.html`/`dashboard_assure.html` (composant "carte de prise
en charge"). Deux variantes selon le fond : sur fond clair, croix pleine
`--primary-dark`/`--ink` (`#0b2027`) ; sur fond sombre uni (sidebar, pied de
page), croix pleine quasi-blanc (`#EFF4F3`). `base_auth.html` (panneau de
marque à fond dégradé) reste une exception volontaire : mark inline (pas le
tag), croix blanche translucide (`rgba(255,255,255,0.9)`) pour rester
cohérent avec le dégradé — cas non couvert par les deux variantes du tag.
La favicon (variante pleine : croix `--primary` `#0e7c86` + pouls
terracotta) est dupliquée en data URI SVG dans chaque `<head>` (`base.html`,
`landing.html`, `base_auth.html`, `404.html`, `500.html`) — pas de fichier
statique, cohérent avec le fait qu'il n'existe pas de dossier `static/`
utilisé dans ce projet (tout le CSS/SVG est inline dans les templates).
Logo secondaire (empilé), icône d'application et version monochrome existent
dans la spec d'origine mais ne sont pas implémentés (aucun usage actif dans
le projet à ce jour) — ne pas les recréer sans un besoin concret identifié.
**Page Paramètres (`parametres` / `parametres_section`).** Découpée en
sections ayant chacune leur URL : cliquer dans le menu **ouvre la page**, pas un
ancrage. `SECTIONS_PARAMETRES` (views.py) pilote à la fois le menu et le
contrôle d accès — une section réservée renvoie **404** à un non-admin, elle
n est pas seulement masquée (mécanisme conservé et testé sur un registre
substitué, même si **aucune section n est réservée aujourd hui**). La section
« Général » n affiche plus que la configuration plateforme (langue, fuseau,
format de date) en **lecture seule**, lue dans `settings.py`.

**Quatre sections : Général, Apparence, Sécurité, Avancé.** Deux ont été
supprimées et ne doivent pas revenir sans un contenu qui soit vraiment un
réglage :

- *Notifications* — aucun modèle de préférences n existe.
- *Données* — ses 6 entrées (2 imports, 3 exports) étaient toutes des actions
  métier **déjà présentes sur leur propre page**. Pire, ses exports ignoraient
  les filtres alors que son sous-titre affirmait le contraire. Vidée de ses
  doublons, la section n avait plus de contenu.

La carte « Mon compte » a également quitté « Général » : elle est personnelle,
donc elle vit dans le menu du compte, où son écran d édition se trouvait déjà.
**Règle de contenu : n afficher que des réglages adossés à du code réel.** Ont
été écartés pour cette raison — ne pas les réintroduire sans les implémenter :
2FA, sessions actives, journal de sécurité, sauvegardes, intégrations
configurables, couleur principale, densité d interface, et les interrupteurs de
notification par type d événement (aucun modèle de préférences n existe ; les
notifications sont des messages rédigés par un admin, pas des événements).
Trois valeurs sont volontairement en lecture seule plutôt que masquées (rôle,
durée de session lue dans `SESSION_COOKIE_AGE`, limitation des tentatives) :
l administrateur doit savoir que ces protections existent. La section Avancé ne
règle rien, elle rend compte des services externes réels et signale l absence
de backend e-mail.

`deconnecter_partout` ferme toutes les sessions du compte, celle en cours
comprise. Django n a pas de primitive : on parcourt les sessions non expirées et
on supprime celles dont `_auth_user_id` correspond — cela suppose le backend de
sessions **en base** (celui par défaut).

**Thème sombre.** Posé par `data-theme="sombre"` sur `<html>`, écrit par un
script **inline dans le `<head>`** (avant la feuille, sinon la page clignote en
clair) ; choix conservé dans `localStorage` (`theme-santesn` : `clair` /
`sombre` / `systeme`). Seuls les jetons changent, aucune règle de mise en page
n'est dupliquée. Portée : `base.html` (les 4 rôles connectés) ; `landing.html`
et `base_auth.html` restent clairs.

**Règle à ne jamais enfreindre : un jeton, un rôle.** `--primary-dark` est une
couleur de **surface** (menu, bandeau, boutons pleins) et reste navy dans les
deux thèmes ; `--titre` porte la couleur de **texte** des titres. Les avoir
confondus a produit une traînée blanche en travers du bandeau et des boutons
illisibles au premier essai. Même logique pour `--topbar-bg`, `--fiche-bg`,
`--btn-a`/`--btn-b` et les paires `--ok-*` / `--attente-*` / `--refus-*` /
`--neutre-*` (pastilles). Faire porter à un jeton un rôle de fond **et** un
rôle de texte est indolore en thème unique, fatal dès qu'un second thème
existe.

**Direction « Relief » (dashboard admin).** La matière fait partie du design
system : ombres en **deux couches** (contact proche + diffusion large) sur
`.panel`/`.kpi`, halo ambiant sur `body` (deux `radial-gradient` fixes),
bandeau `.file-attente` en pièce sculptée (dégradé + lueur `::before`), tuiles
en verre dépoli, montant principal en dégradé navy→turquoise sous `@supports
(background-clip: text)` — sans cette garde le texte serait invisible.
Deux jetons sont réservés au texte posé **sur** les tuiles de verre :
`--sur-verre-teal` (#6fd0c6) et `--sur-verre-accent` (#f7c4a3). Le verre
éclaircit le fond, où `--primary-light` (4.44:1) et `--accent` (3.04:1)
tombent sous WCAG AA ; ces variantes remontent à 5.8 et 5.4:1. **Ne jamais
les utiliser sur fond clair.**

Classes CSS existantes à réutiliser (ne pas dupliquer) : `.page-title`,
`.panel`, `.grid`/`.stat` (obsolètes sur les 4 pages d'accueil par rôle,
remplacées par `.dash-grid`/`.dash-stat`/`.dash-pill`), `.badge` (+
`.validee`/`.refusee`/`.en_attente`), `.button` (+
`.primary`/`.btn`/`.btn-sm`/`.btn-danger`), `.actions` (boutons de ligne de
tableau — ne pas confondre avec `.action-tiles`/`.action-tile`, les tuiles
d'actions principales des dashboards par rôle), `.erreurs`/`.erreurs-formulaire`
(erreurs de formulaire, par champ / globales), `.filtres` (barre de filtres
GET), `.action-ligne` (formulaire POST invisible dans une ligne de tableau),
`.details-tableau` (tableau de données replié sous un graphique, voir
`rapports.html`).

Anneau de focus clavier (`:focus-visible`, même teinte turquoise que les
champs de formulaire), barre de défilement et surlignage de sélection de
texte teintés : dupliqués dans les 3 feuilles de style autonomes
(`base.html`, `landing.html`, `base_auth.html` — même token de couleur, nom
de variable propre à chaque fichier). `theme-color` + `color-scheme: light`
dans les 3 `<head>` ; balises Open Graph/Twitter Card en plus sur
`landing.html` (seule page destinée à être partagée).

Aucun émoji nulle part dans l'application (sidebar, landing, écrans de
connexion) : toutes les icônes viennent de `templatetags/icones.py`
(`{% load icones %}` + `{% icone "nom" %}`, SVG trait fin 24×24,
`stroke="currentColor"` — hérite automatiquement la couleur du conteneur).
Toujours réutiliser une icône existante du dict `_ICONES` avant d'en ajouter
une nouvelle.

**Une icône doit être reconnue, pas seulement décrite.** `settings` a d'abord
été dessinée comme « un engrenage en segments » : un cercle entouré de huit
rayons droits et diagonaux. Sur le papier, un engrenage stylisé ; à l'écran,
**un soleil**. Elle a été remplacée par une vraie roue dentée (contour fermé).
Le test qui la couvrait cherchait un `<circle>` — que le soleil possédait
aussi : il ne pouvait pas voir l'erreur. Il teste désormais ce qui **sépare**
les deux formes (un contour qui se referme, `z`). Vérifier une icône au rendu,
pas à l'intention.

**Un nom d'icône erroné ne lève rien.** `_ICONES.get(nom, "")` rend un SVG
**vide** : pas d'erreur, pas de dessin, rien à l'écran qui le signale (même
famille que la table de couleurs de `rapports.html` indexée par libellé). Un
test vérifie que chaque icône de `SECTIONS_PARAMETRES` existe.

## Comptes de démonstration

Les comptes de démonstration en masse ont été supprimés de la base : un seul
admin réel (`admin@santesn.local`) est conservé, et des comptes réels
Assuré/Médecin/Pharmacien ont été créés directement via Gestion des
utilisateurs pour permettre de tester chaque tableau de bord. La commande
`seed_demo_users` (peuplement en masse de comptes de démo) a été retirée du
projet : redondante avec la création de comptes via Gestion des utilisateurs
et sans utilité une fois les comptes réels en place — ne pas la recréer sans
raison concrète. `DEMO_USERS.md` n'existe pas (voir phase 15, "Documentation
/ finalisation") — si une documentation utilisateur finale est un jour
rédigée, ne pas la nommer ainsi sans vérifier qu'elle est à jour.

## Espacements

**Trois classes, pas de padding en ligne.** Les panneaux de contenu utilisent
`.panel-form` (padding 22/24 + largeur 720), `.panel-bloc` (padding 22/24) ou
`.panel-form-etroit` (largeur 480). Les panneaux de **liste** gardent un padding
nul : leur tableau touche les bords de la carte.

Avant cette règle, 56 déclarations `style="padding…"` réparties sur 40 gabarits
avaient dérivé en **13 valeurs distinctes** (20px, 22/24, 24, 18/22, 20/24…),
d'où des espacements irréguliers d'une page à l'autre. Ne pas réintroduire de
padding en ligne sur un `.panel`.

**`scrollbar-gutter: stable` sur `html`.** Sans cette règle, une page courte
(sans barre de défilement) et une page longue (avec barre) n'ont pas la même
largeur utile : tout le contenu se décale d'environ 10 px d'une page à l'autre.
Mesuré sur 20 pages admin — bord droit à 1398 ou 1408 selon la page ; désormais
1398 partout.

**Vérifier par la mesure, pas à l'œil.** Un décalage de 10 px se voit à la
navigation mais pas sur une capture isolée. Relever `getBoundingClientRect()`
de `main`, `.page-title` et du premier bloc sur plusieurs pages est le moyen
fiable de détecter ces écarts.

## Blocage temporaire des comptes

`TentativeConnexion` (models.py) est **la seule** source : 5 échecs → 5 minutes
de blocage, remise à zéro à la connexion réussie. Il **remplace** l'ancienne clé
de cache `tentatives_connexion:{email}` — ne pas réintroduire un compteur en
cache à côté.

**Pourquoi la base et pas le cache** : l'API de cache de Django ne permet ni
d'énumérer les clés ni de lire le temps restant, donc aucune interface
d'administration n'était possible. Et sans `CACHES` configuré, `LocMemCache`
donnait un compteur **par processus** — 5 tentatives par worker en production.

La clé est l'**adresse saisie**, pas un compte : freiner aussi les adresses
inexistantes évite d'offrir un oracle révélant quelles adresses sont
enregistrées. `comptes_bloques()` n'expose que les lignes appariées à un `User`.

Gestion dans **Paramètres → Sécurité** (admin seul) : recherche, filtre par
rôle, durée restante, déblocage **individuel** avec confirmation. Pas de
« débloquer tout » : un blocage massif signale souvent une attaque, tout
relâcher d'un clic annulerait la protection au pire moment.

**Code mort constaté, conservé volontairement** : la branche
`if not self.user.is_active` de `LoginForm` est inatteignable — `ModelBackend`
rejette déjà les comptes inactifs, donc `authenticate()` a renvoyé `None`. Le
message générique qui en résulte est le bon comportement : il ne confirme pas
qu'une adresse existe.

## Confirmations

**Une confirmation seulement sur ce qui est destructif ou irréversible.** Trop
de confirmations tue la confirmation : rechercher, filtrer, exporter, consulter
et naviguer n'en portent aucune (un test le vérifie).

Le mécanisme existe et ne doit pas être doublé : poser
`data-confirmation="message"` sur un `<form>` suffit — la modale de marque
(`#modale-confirmation`, `role="alertdialog"`, Échap, clic sur le fond,
`requestSubmit`) l'intercepte. `data-confirmation-action="Oui, …"` nomme
l'action sur le bouton ; sans lui le bouton affiche « Confirmer ».

Les 8 suppressions passent par un écran dédié (`confirmer_suppression.html`).
La désactivation d'un compte n'est confirmée que **dans le sens destructif** :
réactiver n'a rien d'irréversible.

## Où placer une fonctionnalité


Une fonctionnalité a **un** emplacement logique. Règles appliquées :

- **Menu latéral** = modules métier. Une action métier fréquente y reste
  (Notifications : envoyer un message est une action, pas un réglage).
- **Paramètres** = réglages **uniquement**. Pas un hub, pas un fourre-tout. Si
  une entrée est une *action* qu'on fait dans son travail, elle n'y a pas sa
  place. Test : « est-ce que je règle quelque chose, ou est-ce que je fais
  quelque chose ? »
- **Menu du compte** (barre du haut, `<details>` natif, sans JS) = ce qui est
  personnel : Mon compte, Mot de passe, Déconnexion. La déconnexion n'est plus
  dans le menu latéral.
- **Un import ou un export vit à UN seul endroit : sa page métier.** Importer
  des utilisateurs → Utilisateurs. Importer des règlements → Paiements.
  Exporter → la liste qu'on regarde, filtres compris. Jamais dans Paramètres
  (la section Données a été supprimée pour cette raison), jamais dans les
  actions rapides du tableau de bord — une opération en masse ponctuelle n'y a
  pas sa place. Trois tests verrouillent ces absences.
- **Un raccourci n'est légitime que s'il ne duplique pas la fonctionnalité.**
  L'alerte « N comptes bloqués » du tableau de bord est un simple lien vers
  Paramètres → Sécurité : elle n'y débloque rien. C'est le bon modèle.

**Paiements : on n'importe pas des paiements, on importe des règlements.**
`Paiement` est en 1-1 avec `Consultation` et tous ses montants sont dérivés de
`calculer_pour`. L'import met à jour `statut`, `mode_reglement` et
`date_reglement` de paiements existants, identifiés par la colonne
**Référence** (= `paiement.pk`, ajoutée à l'export CSV pour l'aller-retour).
Tout ou rien : sur des écritures financières, un import partiel laisserait une
caisse impossible à rapprocher. La date conservée est celle du **relevé**, pas
celle de l'import.

## Barre latérale

`position: sticky; top: 0; align-self: start; height: 100vh; overflow-y: auto`.
**`align-self: start` est indispensable** : un élément de grille étiré (le
défaut) ne peut pas coller. Sans cela la barre défilait hors de l'écran alors
que la barre du haut restait. Pas de `position: fixed` sur desktop — le tiroir
mobile (< 981 px) applique déjà le sien.

## Filtres des listes

Le tri par colonne (`_trier`) sert les **listes admin uniquement** — un
référentiel de plusieurs centaines de lignes se classe ; un agenda est
chronologique et un assuré a trois ordonnances. Ne pas ajouter d'en-têtes
triables aux écrans Médecin/Assuré/Pharmacien.

Côté non-admin, seuls quatre écrans portent un filtre, chacun répondant à une
question réelle : `agenda_medecin` et `mes_rendez_vous_assure` (statut +
période), `mes_ordonnances_assure` (à retirer / déjà retirées),
`historique_delivrances` (recherche + date).

`_filtrer_rendez_vous` est **partagée** par les deux écrans de rendez-vous.
**Le tri suit la période** : « à venir » ordonne du plus **proche** au plus
lointain, tout le reste du plus récent au plus ancien. En tri unique
`-date_heure`, demander « à venir » affichait le rendez-vous le plus lointain
en tête — l'inverse de ce qu'on vient chercher.

**`mes_patients` n'a volontairement aucune barre de filtres** : la page porte
déjà une recherche (combobox JS sur `rechercher_patients_medecin`) qui ouvre
la fiche du patient. Un second champ serait un doublon. Un test le verrouille.

## Tableaux sur petit écran

**Sous 900 px, les listes admin masquent leurs colonnes secondaires**
(`.col-optionnelle`, posée sur le `<th>` *et* sur les `<td>` correspondants ;
`entete_tri` accepte un 4ᵉ argument pour ça).

**La colonne Actions n'est jamais optionnelle** — c'est précisément elle qui
disparaissait. Mesure avant correctif : un tableau de 9 colonnes faisait
**1063 px dans une carte de 356 px**, et on ne pouvait plus ni modifier ni
désactiver un compte depuis un téléphone. À 820 px, 5 listes débordaient déjà.
Mesure après : **aucun débordement sur 12 pages × 3 largeurs**.

Les listes gardent leur **forme tabulaire** — c'est ce qu'on vient y chercher,
comparer des lignes. Le mode carte (`.tableau-carte`) reste réservé aux écrans
Assuré : sur un référentiel de 9 colonnes il produirait des cartes
interminables. Trois tests verrouillent l'invariant.

S'ajoutent sous 900 px : `.actions` en colonne (trois boutons côte à côte
suffisaient à repousser la colonne hors écran) et `table-layout: fixed` (une
cellule longue retendait le tableau malgré les colonnes masquées).

## Pagination


Toutes les listes paginent via `_paginer` (`TAILLE_PAGE_LISTE = 20`), y compris
dans les espaces Assuré, Médecin et Pharmacien. Seule exception assumée :
`liste_ayants_droit` (un conjoint et des enfants ne paginent pas).

**Un queryset paginé doit être ordonné.** Sans `order_by`, la répartition entre
pages est instable — un élément peut apparaître deux fois ou disparaître. Deux
vues en manquaient (`mes_rendez_vous_assure`, `agenda_medecin`) ; un test le
couvre désormais.

## Tests

`python manage.py test Plateform_medicale`. Chaque nouvelle fonctionnalité doit
être testée (permissions, redirections, garde-fous) avant d'être considérée
terminée.
