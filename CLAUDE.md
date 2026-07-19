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
├── management/commands/ # seed_demo_users
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
   couverture, notifications.
6. ✅ Dashboard Assuré — profil, ayants droit, rendez-vous, ordonnances et
   historique.
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
15. ⏳ Documentation / finalisation — `DEMO_USERS.md` obsolète (décrit des
    comptes de démonstration supprimés depuis, voir section "Comptes de
    démonstration") ; pas de documentation utilisateur finale rédigée.

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

## Rapports (livré)

Vue `rapports` (Dashboard Admin) : comptages (utilisateurs par rôle, assurés
par type, rendez-vous par statut, prises en charge par statut, consultations/
ordonnances/délivrances/prestataires partenaires) et agrégat
`_consultations_par_mois` (6 derniers mois, mois courant inclus). Graphiques
Chart.js (CDN jsdelivr avec intégrité SRI) rendus côté client à partir de
`json_script`, en plus des tableaux existants (pas de remplacement). Deux
exports dédiés, tous deux `@admin_required` et construits à partir de la même
fonction `_donnees_rapports()` que la vue (pas de duplication de requêtes) :
`exporter_rapports_excel` (openpyxl, un onglet par tableau) et
`exporter_rapports_pdf` (reportlab, nouvelle dépendance — tableaux mis en
forme, un par section). Ne pas confondre avec `exporter_utilisateurs_excel`
qui ne couvre que la liste des utilisateurs (Dashboard Admin → Utilisateurs).

## Design system

Un seul shell de dashboard (sidebar) dans `base.html`, réutilisé par les 4
rôles (nav conditionnelle selon `current_role`). Palette verte SantéSN
(`--primary: #12885a`, `--primary-dark: #0b5d3b`, `--primary-accent: #16a34a`),
police Plus Jakarta Sans. `landing.html` et `base_auth.html` (pages publiques /
connexion) ont leur propre CSS autonome, ne dépendent pas de `base.html`.
Classes CSS existantes à réutiliser (ne pas dupliquer) : `.page-title`,
`.panel`, `.grid`/`.stat`, `.badge` (+ `.validee`/`.refusee`/`.en_attente`),
`.button` (+ `.primary`/`.btn`/`.btn-sm`/`.btn-danger`), `.actions` (boutons de
ligne de tableau — ne pas confondre avec `.action-tiles`/`.action-tile`, les
tuiles d'actions principales des dashboards par rôle).

Aucun émoji nulle part dans l'application (sidebar, landing, écrans de
connexion) : toutes les icônes viennent de `templatetags/icones.py`
(`{% load icones %}` + `{% icone "nom" %}`, SVG trait fin 24×24,
`stroke="currentColor"` — hérite automatiquement la couleur du conteneur).
Toujours réutiliser une icône existante du dict `_ICONES` avant d'en ajouter
une nouvelle.

## Comptes de démonstration

Les comptes de démonstration en masse (`seed_demo_users`) ont été supprimés de
la base : un seul admin réel (`admin@santesn.local`) est conservé, et des
comptes réels Assuré/Médecin/Pharmacien ont été créés directement via
Gestion des utilisateurs pour permettre de tester chaque tableau de bord.
`DEMO_USERS.md` décrit encore l'ancien peuplement en masse et est obsolète
(voir phase 15, "Documentation / finalisation") — le mettre à jour ou le
supprimer avant la finalisation. La commande `seed_demo_users --count N`
reste disponible si un nouveau jeu de données de démo est nécessaire (refuse
de s'exécuter si `DEBUG=False`).

## Tests

`python manage.py test Plateform_medicale`. Chaque nouvelle fonctionnalité doit
être testée (permissions, redirections, garde-fous) avant d'être considérée
terminée.
