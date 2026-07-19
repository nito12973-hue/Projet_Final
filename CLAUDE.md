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
12. ⏳ Prise en charge et paiements — le modèle `PriseEnCharge` et le calcul
    part assurance / part patient existent déjà ; pas encore de module dédié
    "paiements" (suivi de règlement, historique de paiement).
13. ⏳ Rapports / statistiques — vue `rapports` basique existante ; pas encore
    de graphiques ni d'export PDF/Excel dédiés aux rapports (l'export Excel
    actuel ne couvre que la liste des utilisateurs).
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
