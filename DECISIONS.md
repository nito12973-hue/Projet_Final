# Registre des Décisions Architecturales et Métier (SantéSN)

Ce document consigne de façon claire et sans jargon chaque décision d'architecture, les options considérées et les justifications techniques et métier, afin de pouvoir défendre chaque choix lors de la soutenance et garantir la pérennité du produit.

---

## [2026-10-16] Initialisation du Registre & Principes Directeurs
- **Décision :** Adopter une approche produit centrée sur l'utilisateur final (salarié assuré, gestionnaire IPM, médecin, pharmacien, admin IT) avec isolation multi-tenant stricte dès l'ORM, contrôle strict des flux médias sensibles et respect de la législation sénégalaise (Loi 2008-12 sur les données à caractère personnel - CDP).
- **Options considérées :** 
  1. Laisser les fichiers médias publics sous `/media/` (Standard Django par défaut). -> *Rejeté : Violation grave du secret médical.*
  2. Gestion des praticiens par chaque IPM. -> *Rejeté : Une officine ou un médecin collabore avec plusieurs IPM par convention.*
- **Justification :** Sécurité par défaut ("Fail-closed"), respect strict de la réalité opérationnelle des IPM au Sénégal.

---

## [2026-10-16] Synthèse de Recherche Phase 1 (Documentation, Design & Métier Sénégalais)

### 1. Documentation & Code (Django & SaaS Réels)
- **Django Security & Private Media :** Django déconseille formellement de servir des fichiers confidentiels directement via le serveur web statique. La bonne pratique SaaS est d'utiliser une vue d'autorisation avec `X-Accel-Redirect` (Nginx) ou `FileResponse` protégée.
- **Fail-Closed ORM Manager :** Inspiré des modèles multi-tenant éprouvés, un QuerySet ne doit jamais renvoyer `.all()` par défaut si l'organisme est absent, mais `.none()` sauf bypass administrateur explicite.
- **Settings 12-Factor :** Découpage de `config/settings/` en `base.py`, `dev.py`, et `prod.py` (aucun secret en dur, debug conditionnel).

### 2. Design & Ergonomie (Inspiration Doctolib / Alan)
- **1 écran = 1 tâche claire :** Les formulaires doivent avoir un champ par ligne, des placeholders compréhensibles, des validations d'erreur immédiates et explicites.
- **Mobile First :** Au Sénégal, les salariés consultent leurs droits principalement sur smartphone avec des connexions 3G/4G instables. La carte numérique QR doit être accessible hors ligne et lisible en un clic.

### 3. Réalité Métier Assurance Santé au Sénégal
- **Cadre légal vérifié :** Loi 2008-12 (CDP) et Décret 2012-827 réglementant les IPM (Institutions de Prévoyance Maladie).
- **Double circuit :** 
  1. Circuit conventionné (Tiers Payant) : Accord préalable de prise en charge pour actes lourds, ordonnance sécurisée pour la pharmacie conventionnée avec dispense d'avance des frais.
  2. Circuit hors réseau : Avance intégrale par le salarié et remboursement par virement Mobile Money (Wave / Orange Money) après instruction par le gestionnaire et contrôle du plafond annuel restant du foyer.
## [2026-10-16] Isolation Multi-Organismes & Protection Absolue des Médias Médicaux
- **Décision :** Supprimer tout accès direct au répertoire `/media/` et router l'intégralité des téléchargements de documents médicaux confidentiels (justificatifs de remboursement, pièces d'état-civil, devis de prise en charge) via des contrôleurs Django dédiés.
- **Matrice des Droits (Principe du Secret Médical & Cloisonnement) :**
  1. *Assuré titulaire / ayant droit concerné :* AUTORISÉ (200).
  2. *Gestionnaire de l'organisme rattaché au dossier :* AUTORISÉ (200).
  3. *Gestionnaire d'une autre IPM / tiers non concerné :* REFUSÉ (404 Not Found, pour interdire l'énumération par ID direct).
  4. *Autre assuré de la même IPM :* REFUSÉ (404/403).
  5. *Administrateur IT de la plateforme :* REFUSÉ (403 Forbidden, secret médical garanti : l'admin gère l'infrastructure, pas les dossiers médicaux des salariés).
  6. *Visiteur anonyme :* REFUSÉ (302/401).
- **Architecture de diffusion :**
  - *Production (Docker/Nginx) :* Nginx configuré avec `location /protected_media/ { internal; }`. Django valide l'authentification et les droits, puis transmet le header `X-Accel-Redirect` pour que Nginx délivre le fichier en mémoire vive à pleine vitesse sans bloquer le thread Python.
  - *Développement local :* Streaming protégé via `FileResponse(open(..., 'rb'))`.
  - *Serverless Cloud (Vercel) :* Repli automatique sur les octets persistés en base de données PostgreSQL (`FichierMedia`).
  - *URLs publiques dans les templates :* Remplacement systématique de toutes les occurrences directes `{{ document.url }}` par les balises `{% url 'telecharger_...' %}`.

---

## [2026-10-16] Conception et Implémentation du QuerySet Fail-Closed (Multi-Tenant)
- **Décision :** Création de `OrganismeScopedQuerySet` et `OrganismeScopedManager` dans `Plateform_medicale/managers.py` fonctionnant en mode strict "fail-closed".
- **Comportement garanti :**
  - `qs.for_organisme(None)` renvoie `.none()` (aucun enregistrement visible par défaut).
  - Si un modèle n'a pas de chemin d'isolation explicitement répertorié, le système lève `NotImplementedError` plutôt que de renvoyer le catalogue complet.
  - `qs.for_user(user)` restreint automatiquement un gestionnaire aux données de son IPM (`user.organisme`), autorise l'administrateur système pour la maintenance globale (`self.all()`), et verrouille à vide pour tout autre utilisateur non habilité.

---

## [2026-10-16] Conditionnement du Tiers-Payant Pharmacie aux Conventions Actives
- **Décision :** Une pharmacie ne peut appliquer le tiers payant IPM sur une ordonnance que si elle dispose d'une convention active (`statut=ACTIF` et `tiers_payant_actif=True`) avec l'organisme spécifique de l'assuré.
- **Justification métier :** Au Sénégal, une officine conventionnée avec l'IPM de la Sonatel ne peut pas imputer la dispense d'avance des frais à l'IPM de la Senelec sans accord conventionnel bilatéral. Si aucune convention n'existe, la délivrance est enregistrée mais la prise en charge assurance est fixée à 0 FCFA (l'assuré règle 100% à la caisse et se fait rembourser sur présentation de sa facture acquittée).

---

## [2026-10-16] Découpage Modulaire des Paramètres (`config/settings/`)
- **Décision :** Découper le fichier monolithique `config/settings.py` en un package structuré :
  - `config/settings/base.py` : Socle commun, déclarations des applications, middleware, validation de sécurité, règles métier IPM et fuseau horaire sénégalais (`Africa/Dakar`).
  - `config/settings/dev.py` : Mode développement avec `DEBUG=True`, base SQLite en mémoire pour les tests unitaires instantanés, journalisation console.
  - `config/settings/prod.py` : Mode production durci (`DEBUG=False`), validation stricte de `SECRET_KEY`, en-têtes HTTPS stricts (`SECURE_*`, HSTS), base de données PostgreSQL via `dj_database_url`, masquage des données sensibles avant envoi Sentry, et offloading Nginx `X-Accel-Redirect`.
  - `config/settings/__init__.py` : Sélecteur automatique transparent assurant une compatibilité 100% avec les configurations existantes (Docker, `manage.py`, Vercel).

---

## [2026-10-16] Prise de Rendez-vous Directe par WhatsApp pour les Assurés
- **Décision :** Offrir à chaque assuré la possibilité de contacter et de convenir d'un rendez-vous directement via WhatsApp avec le praticien (médecin de famille, spécialiste ou centre de santé).
- **Justification métier & Contexte Sénégalais :**
  - Au Sénégal, WhatsApp est l'application la plus universellement installée et consultée sur smartphone, fonctionnant avec une consommation de données minimale sur les réseaux mobiles 3G/4G/Orange/Free.
  - La prise de rendez-vous en ligne via des calendriers complexes pose souvent des difficultés aux assurés ayant une faible aisance numérique ou lors de coupures réseau.
  - Un bouton direct WhatsApp avec message pré-formaté (Nom de l'assuré, numéro de police/matricule IPM, objet de la consultation) simplifie drastiquement le parcours : en un clic, le patient initie l'échange avec le cabinet médical sans ressaisie.
- **Points d'intégration :**
  - *Fiche praticien (`fiche_medecin_assure.html`) :* Bouton vert standardisé avec lien direct `https://wa.me/...`.
  - *Formulaire de rendez-vous (`ajouter_rendez_vous_assure.html`) :* Encadré dynamique de contact direct dès la sélection d'un médecin.
  - *Liste des rendez-vous (`mes_rendez_vous.html`) :* Bouton de confirmation/relance rapide par WhatsApp sur chaque ligne de rendez-vous.

---

## [2026-10-16] Nettoyage Intégral et Hygiène du Répertoire de Travail
- **Décision :** Supprimer tous les artefacts obsolètes, fichiers de cache temporaires et templates orphelins :
  - Suppression de `Plateform_medicale/templates/mot_de_passe_genere.html` (orphelin, le mot de passe est désormais transmis de manière sécurisée par canal dédié).
  - Suppression des caches `.pytest_cache` et `.kilo/`.
  - Configuration de `.gitignore` pour ignorer systématiquement les fichiers temporaires de tests générés localement (`media/justificatifs_remboursements/*.pdf`, `backups/*.json`).
  - Validation que l'arbre de travail git est 100% propre (`nothing to commit, working tree clean`) et que la totalité des 884 tests passe sans aucune régression.
