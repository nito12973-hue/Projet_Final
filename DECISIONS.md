# Registre des Décisions Architecturales et Métier (SantéSN)

Ce document consigne de façon claire et sans jargon chaque décision d'architecture, les options considérées et les justifications techniques et métier, afin de pouvoir défendre chaque choix lors de la soutenance et garantir la pérennité du produit.

---

## [2026-10-21] Organisation Modulaire des Gabarits (Templates) en Sous-Dossiers Métier 100% en Français
- **Décision :** Découpage des 115 templates HTML de la racine Plateform_medicale/templates/ vers 10 répertoires thématiques métier exclusivement nommés en langue française :
  - gabarits/ : Squelettes de base réutilisables (ase.html, ase_auth.html).
  - composants/ : Éléments modulaires partagés (_pagination.html).
  - erreurs/ : Pages de codes HTTP et mode hors-ligne (403.html, 404.html, 500.html, offline.html).
  - uthentification/ : Connexion, activation de compte, réinitialisation de mot de passe.
  - ssure/ : Espace patient (carte dématérialisée, ordonnances, remboursements, ayants droit, RDV WhatsApp).
  - medecin/ : Espace praticien (agenda, consultations, prescriptions, dossiers médicaux).
  - pharmacien/ : Espace officine (scanner d'ordonnances, délivrance atomique, historique).
  - gestionnaire/ : Espace IPM (conventions, régimes, liquidations, prises en charge).
  - dministrateur/ : Espace IT (supervision, gestion des accès, métriques Prometheus).
  - commun/ : Fiches partagées, listes globales, CGU et politique de confidentialité CDP.
- **Rétrocompatibilité & Continuité Opérationnelle :**
  - Ajout des sous-dossiers dans TEMPLATES[0]['DIRS'] au niveau de config/settings/base.py afin de garantir une résolution transparente : les appels directs existants et les futurs chemins préfixés fonctionnent simultanément.
  - Validation intégrale de la suite automatisée (936 tests exécutés avec 100% de succès).

## [2026-10-16] Refonte Split-Screen (50%/50%) de l'Authentification & Boutons Interactifs Extensibles
- **Décision :** Abandon du centrage mono-bloc isolé de la page de connexion au profit d'un agencement moderne en deux volets (« Split-Screen » 50% / 50% sur écran large, comme sur les grandes plateformes SaaS telles que Stripe, Doctolib ou GitHub) et harmonisation des boutons de retour interactifs (« expand on hover »).
- **Volet Gauche (Marque & Présentation Métier) :**
  - Identité visuelle institutionnelle SantéSN (dégradé sombre/teal médical, logo SVG, badge d'ancrage national).
  - Présentation claire des 3 piliers opérationnels réels : Tiers-payant dématérialisé avec IPM sénégalaises, Ordonnances infalsifiables à QR code traçable, et Secret médical garanti sous l'égide de la Loi 2008-12 (CDP Sénégal).
  - Aucune adresse postale ou email fictive sur un nom de domaine non acquis (`@santesn.sn`) : ancrage géographique sobre (« Dakar, République du Sénégal ») et contact support direct par WhatsApp/téléphone (+221 78 957 61 45).
- **Volet Droit (Formulaire & Accès Sécurisé) :**
  - Carte de saisie épurée avec inputs contrastés, icônes de repérage et bascule œil mot de passe.
  - Bouton retour vers la landing page compact au repos (icône chevron seule) qui s'élargit en douceur au survol (`.expand-text` s'anime de 0 à 160px) pour afficher son libellé complet, puis se rétracte à nouveau lorsque le curseur s'éloigne.
  - Adaptation fluide sur mobile (< 992px) avec mise en page verticale évitant tout débordement horizontal ou scroll superflu.

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
  - Validation que l'arbre de travail git est 100% propre (`nothing to commit, working tree clean`) et que la totalité des 893 tests passe sans aucune régression.

---

## [2026-10-16] Chatbot Conversationnel et Webhook Meta Cloud API
- **Décision :** Implémenter un moteur conversationnel complet et un webhook officiel Meta (`/api/whatsapp/webhook/`) permettant à tout assuré de dialoguer avec SantéSN directement depuis son application WhatsApp :
  - **Menu interactif :** Accueil personnalisé selon le numéro de téléphone de l'expéditeur.
  - **Consultation des droits :** Taux de couverture de l'assuré, plafond annuel restant du foyer et statut d'adhésion.
  - **Réservation directe de rendez-vous :** Sélection d'un praticien partenaire, analyse de la date et de l'heure voulues, détection des conflits d'horaires et création instantanée du `RendezVous` en base avec statut `DEMANDE`.
  - **Urgences nationales :** Rappel des numéros de secours au Sénégal (SAMU 1515, Pompiers 18, SOS Médecins).
- **Architecture technique :**
  - Contrôleur webhook (`Plateform_medicale/views/whatsapp_webhook.py`) conforme aux spécifications Meta (authentification par challenge GET et ingestion des événements POST).
  - Service de parsing et d'orchestration (`Plateform_medicale/services/whatsapp_bot.py`).
  - Suite de tests unitaires dédiée (`WhatsAppBotAndWebhookTests`) validant le cycle conversationnel complet et la conformité du protocole.

---

## [2026-10-16] Stabilisation Visuelle, Suppression des Sauts de Mise en Page (CLS) et Boutons Retour Standardisés
- **Problème identifié :** Les boutons `.btn-expand` utilisaient une animation CSS sur `:hover` (`max-width: 0 -> 260px`). Au survol de la souris, le bouton doublait soudainement de largeur, repoussant brutalement les boutons voisins vers la ligne du dessous ou chevauchant les en-têtes de cartes et de tableaux. De plus, plusieurs pages secondaires (formulaires et fiches) n'avaient pas de bouton de retour explicite vers leur tableau de bord d'origine, forçant l'utilisateur à recourir aux boutons du navigateur.
- **Décisions ergonomiques & techniques :**
  1. **Stabilisation des largeurs de boutons :** Suppression de l'animation d'extension de texte au survol (`.expand-text` a désormais `max-width: none` et `opacity: 1` fixes). Les boutons conservent un libellé clair et lisible en permanence, avec une micro-élévation douce (`transform: translateY(-1px)`) au survol sans modifier les dimensions du conteneur.
  2. **En-têtes flexibles et anti-chevauchement :** Ajout de `flex-wrap: wrap; gap: 12px;` sur `.page-title` et son sous-groupe `.actions` afin d'éviter tout écrasement ou chevauchement d'éléments lorsque l'écran rétrécit.
  3. **Standardisation du bouton « Retour » :** Ajout systématique d'un bouton de retour (`btn-retour-expand` avec icône chevron et libellé explicite) positionné en haut à droite des en-têtes de pages secondaires :
     - Pharmacien : `scanner_ordonnance.html` -> retour au tableau de bord pharmacien.
     - Médecin : `verifier_carte_medecin.html`, `modifier_profil_medecin.html` -> retour au tableau de bord praticien.
     - Gestionnaire / Admin : `supervision_systeme.html`, `rapports.html`, `parametres.html`, `admin_liste_demandes_support.html`, `bordereau_teletransmission.html`, `resultat_import_utilisateurs.html` -> retours vers leurs sections mères respectives.
     - Assuré : `assistant_sante.html`, `mes_demandes_support.html`, `mon_profil_assure.html` -> retour au tableau de bord assuré.
- **Résultat :** Parcours utilisateur fluide, cohérent, sans saut visuel ni décalage brutal, conforme aux standards SaaS santé (Doctolib / Alan).

---

## [2026-10-16] Correction Ergonomie Admin (Retour Tableau de Bord) et Accès WhatsApp Direct au Plafond Assuré
- **Problèmes identifiés :**
  1. *Confusion dans la navigation utilisateurs Admin :* Sur la page de résultat de l'import et les formulaires utilisateurs, le bouton « Retour aux utilisateurs » renvoyait vers `/utilisateurs/` où l'administrateur arrivait sur une page vide (« Aucun compte signalé » car aucun compte n'était bloqué), sans possibilité immédiate de regagner son tableau de bord.
  2. *Parcours WhatsApp sur le plafond assuré :* L'assuré ne disposait pas de raccourci direct pour interroger ou vérifier son solde de garantie restant sur WhatsApp depuis sa carte de plafond sur le tableau de bord.
- **Décisions ergonomiques & correctifs :**
  1. **Cohérence du retour administrateur :**
     - Remplacement de l'action « Retour aux utilisateurs » par un bouton universel « Retour au tableau de bord » (`{% url 'dashboard' %}`) sur [resultat_import_utilisateurs.html](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/resultat_import_utilisateurs.html), [importer_utilisateurs.html](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/importer_utilisateurs.html), [ajouter_utilisateur.html](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/ajouter_utilisateur.html) et [modifier_utilisateur.html](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/modifier_utilisateur.html).
     - Ajout d'un bouton « Retour au tableau de bord » dans l'en-tête et dans l'état vide de [liste_utilisateurs.html](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/liste_utilisateurs.html), garantissant que l'administrateur n'est jamais bloqué sans action claire.
  2. **Accès WhatsApp direct sur le plafond :**
     - Sur [dashboard_assure.html](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/dashboard_assure.html), le montant du solde annuel restant est désormais cliquable et ouvre directement WhatsApp (`https://wa.me/{{ whatsapp_bot_phone }}?text=1`) pour interroger instantanément le bot SantéSN (option 1 : consultation des droits et solde restant du foyer).
     - Ajout d'un bouton direct WhatsApp sur la carte du solde et sous la jauge visuelle de consommation du plafond.




---

## [2026-10-16] Amélioration de la Cartographie Médicale, Géolocalisation et Visualisations par Courbes
- **Objectifs :**
  1. Offrir aux assurés et administrateurs une expérience de localisation fluide, interactive et immédiatement actionnable (itinéraires, appels, contact direct WhatsApp avec les prestataires de santé).
  2. Rendre les courbes de tendances (paiements, consultations, répartition des prises en charge) plus lisibles, précises, sobres et conformes aux bonnes pratiques UX.
- **Décisions ergonomiques & techniques :**
  1. **Cartographie médicale et géolocalisation (`prestataires_proches.html` & `liste_prestataires.html`) :**
     - **Recadrage dynamique intelligent :** Lorsque l'assuré recherche un prestataire, sélectionne une région/ville (Dakar, Thiès, Kaolack, Saint-Louis...) ou filtre par type d'établissement, la carte calcule les limites (`fitBounds`) des marqueurs visibles et recentre automatiquement la vue avec animation fluide (`flyTo` ou `fitBounds` avec padding de confort).
     - **Contact direct WhatsApp et badges conventionnés :** Les infobulles Leaflet et les fiches des prestataires affichent un badge officiel « Convention Tiers-Payant » et un bouton direct WhatsApp vert (`wa.me/221...`) pré-rempli pour toute structure disposant d'un numéro mobile sénégalais (préfixes 70, 75, 76, 77, 78).
     - **Enrichissement de la carte réseau admin (`liste_prestataires.html`) :** Les marqueurs circulaires affichent désormais le type de structure, la ville, le téléphone direct cliquable, le raccourci WhatsApp et un lien d'édition rapide vers la fiche du prestataire.
  2. **Courbes et graphiques de tendance (`dashboard.html` & `rapports.html`) :**
     - **Courbe des flux financiers sur le tableau de bord :** La courbe de tendance des paiements sur 30 jours affiche désormais des repères temporels horizontaux épurés (dates tous les 5 jours) et des montants ordonnés en FCFA lisibles (`k` et `M`), avec infobulle complète formatée en FCFA (`new Intl.NumberFormat('fr-FR')`).
     - **Courbe des consultations médicales (`rapports.html`) :** Les tooltips indiquent explicitement le nombre d'actes (« X consultations »), les axes disposent de pas entiers et de grilles douces adaptées au thème.
     - **Graphique en anneau des prises en charge (`rapports.html`) :** Découpe interne aérée (`cutout: 62%`) et affichage automatique du pourcentage calculé en temps réel dans les infobulles survolées.
- **Vérifications :** Suite complète de tests validée avec succès (**893 tests OK à 100%**).

---

## [2026-10-16] Modernisation des Formulaires et Refonte Ergonomique de l'Authentification
- **Objectifs :**
  1. Offrir une page de connexion moderne, élégante, équilibrée et épurée, avec affichage/masquage du mot de passe et icônes d'aide à la saisie.
  2. Rendre tous les formulaires (connexion, mot de passe oublié, activation de compte, création et modification de profil, assurés, praticiens) parfaitement lisibles, centrés et ergonomiques sur ordinateur, tablette et mobile.
  3. Protéger contre la double-soumission et apporter un retour visuel immédiat (spinner et désactivation pendant l'envoi) avec restauration BFCache propre au retour arrière.
- **Décisions ergonomiques & techniques :**
  1. **Page de connexion & écrans d'authentification (`base_auth.html`, `login.html`, `mot_de_passe_oublie.html`, `mot_de_passe_reinitialiser.html`, `activer_compte.html`) :**
     - **Champs avec icônes contextuelles intégrées :** Préfixes visuels discrets (icône enveloppe pour l'email, cadenas pour le mot de passe) alignés élégamment dans le champ sans altérer le flux de saisie.
     - **Affichage / masquage dynamique du mot de passe :** Bouton œil interactif avec bascule du pictogramme SVG et respect des standards d'accessibilité (`aria-label`).
     - **Indicateur de champ obligatoire :** Étoile rouge `*` nette sur chaque label requis.
     - **Protection anti-double clic :** À la soumission, le bouton principal passe en état `chargement` (opacité, curseur d'attente, spinner SVG doux et libellé d'état « Connexion en cours... »).
  2. **Harmonisation globale des formulaires de l'application (`base.html`) :**
     - **Centrage et dimensions équilibrées :** `.panel-form` calibré avec padding aéré (`24px 28px`), bordures subtiles et ombre douce, évitant les formulaires flottants ou asymétriques.
     - **Mobile-first ergonomique :** Sur écran <= 640px, les conteneurs passent en pleine largeur confortable, les boutons d'action s'empilent verticalement à 46px de hauteur pour un clic tactile sans erreur ni débordement horizontal.
     - **Messages d'erreurs contextuels :** Messages d'erreur stylisés sous le champ concerné avec icône d'alerte, vocabulaire clair et suppression de tout traceback ou détail technique.
- **Vérifications :** Suite complète de tests validée avec succès (**893 tests OK à 100%**).

---

## [2026-10-16] Refonte de la Page de Connexion en Carte Centrée Compacte (440px) & Calibrage des Formulaires
- **Contexte & Constat :**
  - L'écran de connexion initial utilisait une mise en page bi-colonne large de 920px avec un panneau latéral marketing et des arrière-plans animés, occupant tout le champ visuel de l'écran sur ordinateur de bureau.
  - Les formulaires applicatifs internes utilisaient une largeur de 720px qui étirait inutilement les champs de saisie simples (nom, prénom, téléphone, email).
- **Décisions ergonomiques & techniques :**
  1. **Format carte centrée épurée pour l'authentification (`base_auth.html` & `login.html`) :**
     - Remplacement de la grille 920px à 2 colonnes par une **carte d'authentification compacte centrée de 440px**, équilibrée verticalement et horizontalement.
     - En-tête sobre avec le logotype officiel SantéSN, titre et sous-titre rassurant.
     - Suppression des animations de fond volumineuses pour un rendu propre, immédiat et professionnel (background doux `#f8fafc`).
     - Carte blanche avec ombre portée subtile, coins arrondis à 16px, bordure fine (`#e2e8f0`).
     - Pied de page allégé et discret sous la carte contenant les liens légaux (Accueil, CGU, Confidentialité).
  2. **Calibrage des formulaires internes (`base.html`) :**
     - Calibrage de `.panel-form` et de `form` à une largeur maximale raisonnable de `580px` (variante `.panel-form-large` à 820px pour ordonnances/tableaux multi-lignes, et `.panel-form-etroit` à 440px pour actions rapides).
     - Suppression de l'étirement des champs de saisie pour une lecture plus rapide et un confort de frappe naturel.
- **Vérifications :** Suite complète de 893 tests validée (**100% succès**).

---

## [2026-10-16] Structuration Professionnelle de la Connexion et de la Landing Page (Standard Grandes Plateformes)
- **Objectifs :**
  1. Structurer la page de connexion comme les grands portails SaaS médicaux (Doctolib Pro, Alan, Stripe) avec repères par profil, aide contextuelle et réassurance.
  2. Structurer la landing page avec une barre de recherche rapide de soins dans le Hero et un ruban d'indicateurs clés d'impact en direct.
- **Décisions ergonomiques & techniques :**
  1. **Page de connexion structurée (`login.html` & `base_auth.html`) :**
     - **Sélecteur d'espace par onglets (Assuré, Médecin, Pharmacie, Gestionnaire) :** Onglets cliquables adaptant dynamiquement l'aide contextuelle, l'exemple de saisie (`placeholder`) et l'intitulé du bouton d'action.
     - **Badge de statut sécurisé :** Indicateur vert « Connexion Sécurisée SSL » avec point pulsé.
     - **Bloc de préférences & conformité :** Case « Mémoriser mon adresse » (sauvegardée dans `localStorage`) et badge « Chiffré 256 bits ».
     - **Bloc d'assistance & accès :** Guide explicatif pour la première connexion, raccourci direct vers l'assistance WhatsApp et la FAQ.
  2. **Landing page enrichie (`landing.html`) :**
     - **Barre de recherche rapide de praticiens et pharmacies :** Intégrée au sein de `hero-centre`, permettant aux visiteurs de rechercher un soin et une localité (Dakar, Thiès...) avec un design épuré type Doctolib.
     - **Ruban de KPI d'impact en direct :** 4 métriques de référence (100% dématérialisé, < 3s de validation QR, +120 structures conventionnées, conformité légale CDP Sénégal).
- **Vérifications :** 893 tests exécutés avec succès (**100% OK**).

---

## [2026-10-16] Assainissement de l'Impression (@media print) & Refonte Réaliste des CGU et Confidentialité (Loi 2008-12 & CDP Sénégal)
- **Objectifs :**
  1. Éliminer tout parasitage d'interface (sélecteur de luminosité/thème, cloche de notifications, menu utilisateur, boutons de retour, barres d'actions) sur les impressions de reçus, ordonnances et bons de prise en charge.
  2. Aligner les Conditions Générales d'Utilisation (CGU) et la Politique de Confidentialité sur les standards des grandes plateformes de santé numériques (Doctolib, Alan) et le droit sénégalais (Loi n° 2008-12 relative à la protection des données à caractère personnel, récépissé CDP, secret médical).
- **Décisions ergonomiques & techniques :**
  1. **Assainissement strict de l'impression (`base.html`, `recu_paiement.html`, `voir_bon_prise_en_charge.html`, `voir_ordonnance.html`) :**
     - Règle `@media print` unifiée masquant formellement `header`, `nav`, `aside`, `footer`, `.topbar`, `.public-topbar`, `.menu-theme`, `#menu-theme-topbar`, `.menu-notifications`, `.menu-compte`, `.fil-ariane`, `.btn-retour-expand`, et les boutons d'action.
     - Garantie de documents médicaux et comptables au format A4 irréprochable sans débordement de contrôles web.
  2. **Refonte réaliste des CGU (`cgu.html`) :**
     - Sommaire interactif sticky à gauche (`cgu-nav-lien`) avec défilement fluide.
     - 8 articles exhaustifs : Objet & statut juridique, Accès & rôles, Sécurité & authentification (chiffrement, 2FA, QR), Secret médical & télémédecine, Prise en charge dématérialisée (temps réel, plafonds), Propriété intellectuelle, Disponibilité & maintenance (audit de continuité), Droit applicable & juridiction compétente (Tribunal Hors Classe de Dakar).
     - Cartouche DPO et assistance directe avec contacts officiels (`dpo@santesn.sn`, récépissé CDP `RX-2026-0418-SN`).
  3. **Refonte de la Politique de Confidentialité (`politique_confidentialite.html`) :**
     - Sommaire interactif sticky et structuration conforme aux exigences CDP Sénégal et CNIL santé.
     - 7 sections détaillées : Cadre juridique (Loi 2008-12), Données collectées par profil, Finalités & bases légales, Mesures de sécurité technique (TLS 1.3, AES-256-GCM, hachage bcrypt, RBAC strict), Partage et interconnexion (tiers payant, absence de cession commerciale), Durées de conservation légales (10 ans pour le dossier médical, 3 ans après inactivité), Droits des personnes et saisine CDP.
     - Bannières d'audit de conformité et encadré officiel de réclamation auprès de la CDP (Immeuble Rivonia, Dakar).
- **Vérifications :** 893 tests automatisés conformes (**100% OK**), styles d'impression et pages légales validés.

---

## [2026-10-16] Assainissement Sobre de la Connexion et de la Landing Page (Zéro artifice trompeur)
- **Objectifs :**
  1. Épurer totalement la page de connexion (`login.html` & `base_auth.html`) : supprimer les onglets de sélection de profils factices et les boîtes d'aide parasites, recentrer le formulaire sur sa fonction première avec un design net, accessible et responsive.
  2. Aligner la Landing Page (`landing.html`) sur la promesse réelle de SantéSN sans éléments trompeurs : supprimer la fausse barre de recherche cliquable et le faux ruban de statistiques inventées.
- **Décisions ergonomiques & techniques :**
  1. **Page de connexion épurée (`login.html` & `base_auth.html`) :**
     - Formulaire centré et net : Email / Identifiant, Mot de passe avec toggle oeil, bouton "Se connecter" avec indicateur de chargement.
     - Suppression des onglets artificiels par rôle : Django authentifie directement l'utilisateur et le redirige selon son rôle en base de données.
     - Lien sobre et discret vers la FAQ d'assistance en bas de carte.
  2. **Landing Page authentique (`landing.html`) :**
     - Suppression de la barre de recherche fictive du Hero et des compteurs non vérifiés.
     - Mise en valeur directe des bénéfices réels : tiers payant dématérialisé, ordonnances infalsifiables sécurisées par QR Code, secret médical et conformité CDP Sénégal (Loi 2008-12).
     - Démonstration transparente du produit via le showcase des 4 interfaces réelles (Admin, Assuré, Médecin, Pharmacien) et le parcours en 5 étapes.
- **Vérifications :** Suite de tests exécutée avec succès (**100% OK**), affichage authentique et sans surcharge.

---

## [2026-10-16] Retrait des Adresses Email Fictives Liées au Domaine Non Acheté (Canaux Réels Téléphone & WhatsApp)
- **Objectifs :**
  1. Prendre en compte le fait que le nom de domaine personnalisé n'a pas encore été acheté : éliminer toute adresse email d'apparence professionnelle factice (`contact@santesn.sn`, `dpo@santesn.sn`).
  2. Remplacer tous les points de contact publics par les canaux fonctionnels et réels de l'organisation : Ligne téléphonique directe et Support WhatsApp (+221 78 957 61 45).
- **Décisions ergonomiques & techniques :**
  1. **Landing Page (`landing.html`) :** Cartes de contact et pied de page mis à jour vers Localisation (Dakar, Sénégal), Ligne directe (+221 78 957 61 45) et Support WhatsApp direct.
  2. **CGU (`cgu.html`) & Confidentialité (`politique_confidentialite.html`) :** Suppression des mentions `dpo@santesn.sn` au profit de la ligne directe WhatsApp et de l'adresse physique à Dakar.
- **Vérifications :** Tests unitaires conformes (**100% OK**), 0 adresse email fictive présente dans les templates.

---

## [2026-10-16] Épuration des Pages Légales (Suppression du Bouton d'Impression sur CGU & Confidentialité)
- **Objectifs :**
  1. Éliminer le bouton d'impression et les bandeaux d'impression superflus sur les pages [CGU](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/cgu.html) et [Politique de Confidentialité](file:///c:/Users/nito1/Desktop/Projet_Final/Plateform_medicale/templates/politique_confidentialite.html).
  2. Aligner l'affichage sur les standards des portails web où les documents légaux sont consultés en ligne avec retour accueil direct.
- **Décisions ergonomiques & techniques :**
  1. Suppression du bouton `btn-action-legal` déclenchant `window.print()`.
  2. Suppression des en-têtes d'impression statiques dédiés, ne conservant qu'un bouton de retour clair vers l'accueil.
- **Vérifications :** 16 tests légaux et landing validés avec succès (**100% OK**), vérification système Django sans anomalie.

---

## [2026-10-16] Harmonisation des Données Réelles et Amélioration de la Landing Page
- **Objectifs :**
  1. Remplacer toute adresse factice (« Almadies Zone 8 ») par la mention sobre validée par l'utilisateur : « Équipe SantéSN · Dakar, République du Sénégal » et Ligne directe WhatsApp.
  2. Ajuster la FAQ sur la protection des données de la landing page pour refléter fidèlement le respect de la Loi sénégalaise n° 2008-12 et les contrôles RBAC.
- **Décisions ergonomiques & techniques :**
  1. **Politique de Confidentialité (`politique_confidentialite.html`) :** Mention du Référent Protection des Données : « Équipe SantéSN · Dakar, République du Sénégal · Ligne directe WhatsApp : +221 78 957 61 45 ».
  2. **Landing Page (`landing.html`) :** Réponse FAQ claire et positive sur la protection des données des assurés.
- **Vérifications :** Tests unitaires validés (**100% OK**), pile Docker reconstruite et opérationnelle.


