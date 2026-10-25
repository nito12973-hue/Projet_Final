# CHAPITRE 4 : RÉALISATION, TESTS ET RÉSULTATS

---

## 4.1. Mise en œuvre et environnement de travail

### 4.1.1. Environnement de développement et outillage
La réalisation de la plateforme **SantéSN** s'est déroulée dans un environnement logiciel rigoureusement standardisé, garantissant la reproductibilité des builds entre les machines de développement et les serveurs de production :

* **Système d'exploitation :** Postes de travail sous Windows 11 Professionnel et environnements de déploiement conteneurisés Linux Ubuntu 22.04 LTS (Alpine Linux pour les conteneurs Docker légers).
* **Interpréteur et environnement virtuel :** Python 3.12 et Python 3.14 avec gestionnaire d'environnement isolé (`venv`) et verrouillage strict des dépendances dans `requirements.txt`.
* **Gestionnaire de code source :** Git 2.45+ avec intégration de conventions de commits sémantiques (*Conventional Commits* : `feat:`, `fix:`, `test:`, `docs:`) et téléversement sur le dépôt distant GitHub.
* **Serveur de base de données :** Instance cloud PostgreSQL managée sur **Neon Serverless PostgreSQL**, offrant un pooler de connexions optimisé et des sauvegardes transactionnelles instantanées.
* **Environnement d'exécution Cloud :** Déploiement PaaS automatisé sur **Vercel** via l'adaptateur `@vercel/python` et configuration de secours sur **Render Cloud** avec `gunicorn` et proxy inverse `nginx`.

### 4.1.2. Organisation modulaire du projet Django
Le projet est architecturé selon les meilleures pratiques Django pour les applications d'entreprise d'envergure. Le code source est structuré de façon claire et modulaire :

```
Projet_Final/
├── config/                      # Configuration centrale du projet
│   ├── settings/
│   │   ├── base.py              # Configuration commune (apps, middlewares, templates)
│   │   ├── dev.py               # Paramètres de développement local (SQLite/PostgreSQL)
│   │   └── prod.py              # Paramètres de durcissement production (HTTPS, HSTS, Logs)
│   ├── urls.py                  # Routage maître des URL de l'application
│   └── wsgi.py                  # Point d'entrée WSGI pour le serveur d'application
├── Plateform_medicale/          # Cœur applicatif SantéSN
│   ├── models.py                # Modèles de données relationnels (20+ entités métier)
│   ├── views/                   # Contrôleurs métier découplés par domaine
│   │   ├── auth.py              # Authentification, gestion de session et contrôle RBAC
│   │   ├── assure_espace.py     # Espace patient, carte dématérialisée, ayants droit
│   │   ├── medecin.py           # Consultations médicales et ordonnances électroniques
│   │   ├── pharmacien.py        # Scanner optique caméra et validation atomique
│   │   ├── prestataires.py      # Référentiel national, recherche tolérante et SIG Leaflet
│   │   └── paiements.py         # Moteur de tiers payant, liquidations et télétransmission
│   ├── templates/               # Gabarits HTML5 accessibles et sémantiques
│   │   ├── gabarits/base.html   # Squelette principal avec tokens de thèmes clair/sombre
│   │   └── commun/              # Vues écrans (carte, dashboard, formulaires, scanner)
│   ├── tests.py                 # Suite de validation automatisée (196+ tests)
│   └── management/commands/     # Commandes CLI (seed_demo.py pour provisionner la démo)
├── static/                      # Ressources statiques (icônes vectorielles SVG, JS PWA)
├── vercel.json                  # Descripteur de déploiement Cloud serverless
└── requirements.txt             # Dépendances Python auditées
```

---

## 4.2. Présentation de la solution

La plateforme SantéSN propose une expérience utilisateur soignée, ergonomique et adaptée à la diversité des terminaux utilisés au Sénégal (smartphones, tablettes, postes fixes). Les cinq espaces utilisateurs majeurs sont décrits ci-dessous :

### 4.2.1. L'Espace Assuré (Patient et Ayants Droit)
L'espace assuré a été pensé pour offrir une autonomie totale au patient :
1. **La Carte Dématérialisée de Tiers Payant (Format ISO 7810 ID-1) :**
   * Présente une reproduction fidèle d'une carte de crédit physique haut de gamme, ornée d'une micro-puce dorée réaliste, du numéro d'immatriculation unique national (ex: `SN-12345`), des dates de validité et du logo officiel de l'IPM de rattachement.
   * Affiche un **QR Code dynamique vectoriel** recalculé pour chaque assuré, intégrant une signature cryptographique permettant au pharmacien de certifier la validité des droits en une fraction de seconde.
2. **Le Suivi du Plafond Annuel Familial :**
   * Une jauge interactive affiche en temps réel le montant total alloué pour l'année, le montant consommé par l'ensemble du foyer et le reliquat disponible (ex: *« Reste disponible : 1 125 000 FCFA sur un plafond de 1 500 000 FCFA »*).
3. **Le Mode Hors-Ligne (PWA) :**
   * Grâce au Service Worker enregistré en tâche de fond, si un assuré se présente dans une clinique située dans une zone de Dakar où la connexion 4G est temporairement indisponible, la carte de santé et le QR code restent affichés à l'écran sans interruption.

---

### 4.2.2. L'Espace Médecin Traitant
L'espace médecin simplifie la prise en charge clinique et supprime la lourdeur des carnets papier :
1. **Recherche et Identification du Patient :** Le praticien tape le numéro de carte ou le nom du patient pour afficher instantanément sa fiche administrative et médicale.
2. **Consultation et Prescription Numérique :** Le médecin sélectionne les médicaments prescrits à partir d'une nomenclature actualisée (forme galénique, dosage, posologie journalière et durée du traitement).
3. **Signature et Sceau d'Intégrité HMAC-SHA256 :** Lors de la validation, le serveur SantéSN génère un tampon officiel certifié comportant le numéro d'ordre des médecins du praticien et calcule une empreinte cryptographique unique qui garantit qu'aucune ligne de l'ordonnance ne pourra être altérée ultérieurement.
4. **Génération PDF A4 Officielle :** L'ordonnance peut être visualisée en ligne, imprimée en format A4 avec en-tête institutionnel ou partagée au patient.

---

### 4.2.3. L'Espace Pharmacien d'Officine
L'espace pharmacien est conçu pour la rapidité au comptoir et la sécurité anti-fraude :
1. **Scanner Optique par Caméra (`jsQR`) :** Le pharmacien clique sur « Activer la caméra ». En approchant le smartphone du patient ou l'ordonnance imprimée, le scanner décode instantanément le QR Code sans nécessiter l'achat d'une douchette laser coûteuse.
2. **Vérification en Temps Réel :** Le système contrôle immédiatement trois points clés :
   * L'authenticité du sceau cryptographique HMAC ;
   * La convention active entre l'IPM de l'assuré et la pharmacie ;
   * Le statut de l'ordonnance (qui doit impérativement être « Active »).
3. **Calcul Automatique de la Quote-Part :** L'écran affiche clairement la part prise en charge par l'IPM (ex: 80 % = 16 000 FCFA) et le reste à charge que le patient doit régler sur place (ex: 20 % = 4 000 FCFA).
4. **Délivrance Transactionnelle Atomique :** Dès que le pharmacien clique sur « Valider la délivrance », une transaction SQL verrouille la ligne (`select_for_update`) et bascule l'ordonnance à l'état `Délivrée`. Même si l'assuré tente de présenter la même ordonnance dans une autre pharmacie 30 secondes plus tard, l'écran de la seconde officine indiquera en rouge : *« Alerte : Ordonnance déjà délivrée le 25/10/2026 à la Grande Pharmacie Dakaroise »*.

---

### 4.2.4. L'Espace Gestionnaire d'IPM
Véritable tour de contrôle financière et médicale, l'espace gestionnaire permet de :
1. **Suivre les KPI et Indicateurs de Sinistralité :** Visualiser les dépenses globales engagées, la répartition par type d'actes (pharmacie, biologie, hospitalisation, optique) et l'évolution mensuelle des remboursements.
2. **Gérer les Conventions Prestataires :** Établir ou suspendre des conventions avec les cliniques, hôpitaux et pharmacies partenaires au Sénégal, avec gestion des numéros de convention officiels.
3. **Cartographie Sanitaire et Géolocalisation (SIG / Leaflet) :**
   * Visualiser l'ensemble du maillage des structures partenaires sur une carte interactive Leaflet ;
   * Permuter entre les calques **Google Maps Plan Urbain**, **Google Satellite Hybride** et **Esri World Imagery HD** ;
   * Bénéficier d'une parfaite lisibilité quel que soit le thème sélectionné (mode jour clair ou mode nuit sombre avec boutons de contrôle adaptés).
4. **Instruction des Remboursements Hors Réseau :** Examiner les factures téléversées par les assurés pour des soins d'urgence reçus hors réseau conventionné, valider le montant remboursable et ordonnancer le règlement.
5. **Télétransmission des Bordereaux Comptables :** Exporter les relevés de liquidation mensuels certifiés pour transmission aux services financiers et émission des virements aux officines.

---

### 4.2.5. L'Espace Administrateur Système (IT)
Dédié à la sécurité et à la conformité institutionnelle :
1. **Contrôle d'Accès Basé sur les Rôles (RBAC) :** Cloisonnement strict empêchant un médecin d'accéder aux données comptables de l'IPM ou un gestionnaire de modifier un diagnostic médical.
2. **Journal d'Audit Immuable (*Audit Trail*) :** Enregistrement de chaque action sensible (date, heure, adresse IP, utilisateur, ressource consultée ou modifiée) assurant la traçabilité exigée par la CDP.
3. **Surveillance Technique :** Suivi de la disponibilité de la base de données PostgreSQL Neon et des métriques de temps de réponse.

---

## 4.3. Tests et validation

### 4.3.1. Stratégie de tests et assurance qualité
Pour garantir une fiabilité de niveau industriel à une application manipulant des données médicales et financières sensibles, nous avons élaboré une stratégie de test rigoureuse à plusieurs niveaux :

1. **Tests unitaires :** Vérification unitaire de chaque méthode de calcul (écrêtement de plafond, calcul de quote-part, hachage HMAC, normalisation des recherches textuelles).
2. **Tests d'intégration et de permissions (RBAC) :** Validation que les décorateurs de sécurité bloquent systématiquement les utilisateurs non autorisés (tentative d'accès d'un assuré à l'espace pharmacie, tentative d'un médecin d'accéder aux liquidations de l'IPM).
3. **Tests de résistance aux failles IDOR (Insecure Direct Object Reference) :** Vérification qu'un assuré ne peut en aucun cas consulter l'ordonnance ou la carte d'un autre assuré en modifiant l'identifiant dans l'URL.
4. **Tests de non-régression et d'isolation des fixtures :** Garantir que les jeux d'essais automatisés s'exécutent dans une base isolée sans modifier les données réelles de démonstration.

### 4.3.2. Résultats d'exécution du banc de tests
La suite de tests automatisés développée dans `Plateform_medicale/tests.py` comprend **196 tests complets** exécutés avec succès :

```
----------------------------------------------------------------------
Ran 196 tests in 18.420s

OK
Destroying test database for alias 'default'...
System check identified no issues (0 silenced).
```

| Famille de Tests | Nombre de Tests | Statut | Risques Couverts |
| :--- | :---: | :---: | :--- |
| **Authentification & Sécurité RBAC** | 32 tests | **100 % Succès** | Usurpation de rôle, force brute sur mots de passe, sessions compromises. |
| **Espace Assuré & Cartes ISO 7810** | 35 tests | **100 % Succès** | Génération QR Code, calcul jauge plafond, affichage ayants droit. |
| **Espace Pharmacie & Scanner Optique** | 46 tests | **100 % Succès** | Détection double délivrance, verrouillage transactionnel ACID, calcul tiers payant. |
| **Espace Médecin & Ordonnances HMAC** | 43 tests | **100 % Succès** | Intégrité des prescriptions, signature électronique, génération PDF A4. |
| **Gestionnaire & Multi-Tenancy** | 22 tests | **100 % Succès** | Isolation stricte IPM SantéSN vs Sonatel, conventions, liquidations. |
| **PWA, Mode Hors-Ligne & Légal CDP** | 18 tests | **100 % Succès** | Service Worker, conformité loi 2008-12, mentions légales CGU. |
| **TOTAL GÉNÉRAL** | **196 tests** | **100 % Succès** | **Zéro régression, fiabilité éprouvée.** |

---

## 4.4. Évaluation des coûts

Un projet informatique professionnel doit justifier sa rentabilité économique. L'évaluation financière ci-dessous démontre que le modèle cloud serverless retenu permet d'exploiter SantéSN à un coût dérisoire comparé aux dépenses actuelles en papeterie des IPM :

### 4.4.1. Budget prévisionnel d'exploitation annuelle (Infrastructure Cloud)

| Poste de Dépense | Fournisseur / Solution | Coût Mensuel Estimatif | Coût Annuel Estimatif |
| :--- | :--- | :---: | :---: |
| **Hébergement Application Web & API** | Vercel Pro PaaS (Haute Disponibilité) | 20 $ (~12 000 FCFA) | 144 000 FCFA |
| **Base de Données Managée Cloud** | Neon Serverless PostgreSQL (Tier Business) | 19 $ (~11 500 FCFA) | 138 000 FCFA |
| **Nom de Domaine National (.sn)** | NIC Sénégal / Registrar agréé | — | 25 000 FCFA |
| **Certificat SSL / TLS & Pare-feu WAF** | Cloudflare / Let's Encrypt (Inclus) | Gratuit | 0 FCFA |
| **Passerelle Notifications WhatsApp** | Meta Cloud API (1 000 conv. gratuites/mois) | ~15 $ (~9 000 FCFA) | 108 000 FCFA |
| **Provision Maintenance & Support IT** | Équipe technique locale d'ingénierie | ~50 000 FCFA | 600 000 FCFA |
| **TOTAL ANNUEL D'EXPLOITATION** | | | **1 015 000 FCFA / an** |

### 4.4.2. Retour sur investissement (ROI) pour une IPM moyenne
Une IPM sénégalaise gérant environ **5 000 assurés** dépense actuellement en moyenne :
* Impression de carnets d'assurés et cartes plastifiées : ~2 500 000 FCFA / an ;
* Impression de liasses de bons autocopiants et formulaires : ~1 800 000 FCFA / an ;
* Pertes financières estimées dues aux fraudes et doubles délivrances : ~8 000 000 FCFA / an.

*Total des coûts de l'ancien modèle papier :* **~12 300 000 FCFA par an**.

Avec SantéSN, pour un coût d'exploitation d'environ **1 015 000 FCFA par an**, l'organisme réalise une **économie nette annuelle supérieure à 11 millions de FCFA**, soit un retour sur investissement amorti en moins de deux mois d'exploitation.

---

## 4.5. Difficultés rencontrées et solutions apportées

Tout au long du développement, plusieurs défis techniques complexes ont été surmontés avec succès :

### 1. La gestion de la double délivrance en temps réel (Concurrence d'accès)
* **Problème :** Si deux pharmacies scannent la même ordonnance à deux secondes d'intervalle, une lecture simultanée du statut en base de données pouvait autoriser la délivrance dans les deux officines avant que le statut ne bascule à `Délivrée`.
* **Solution apportée :** Utilisation d'un verrouillage pessimiste au niveau du moteur PostgreSQL via l'instruction Django ORM `select_for_update()`, encapsulée dans un bloc transactionnel atomique `transaction.atomic()`. La première transaction acquiert un verrou exclusif sur la ligne de l'ordonnance, forçant la seconde requête à attendre et à constater immédiatement le statut délivré.

### 2. La recherche tolérante aux accents, aux apostrophes et multi-champs
* **Problème :** Dans le répertoire national des prestataires de santé au Sénégal, un utilisateur tapait par exemple `"CLINIQUE DE L'OCEAN DAKAR"`. La recherche SQL standard échouait car `"Clinique de l'Océan"` est stocké dans le nom et `"Dakar"` dans la ville, et PostgreSQL `ILIKE` ne traite pas le caractère `E` comme équivalent à `É`.
* **Solution apportée :** Conception d'un algorithme de normalisation textuelle utilisant la décomposition Unicode NFD (`unicodedata.normalize`) pour retirer les marques diacritiques (accents), unifier les apostrophes courbes/droites (`l'océan` = `locean` = `ocean`), et découper la requête en mots-clés indépendants analysés à travers un corpus unifié (nom + ville + adresse + téléphone).

### 3. La lisibilité du sélecteur de calques cartographiques en mode sombre
* **Problème :** Par défaut, la boîte de sélection des calques de la carte Leaflet injecte un fond blanc codé en dur (`#fff`). Lors du passage en mode sombre (`data-theme="sombre"`), les libellés de texte devenaient blancs cassés, produisant un affichage blanc sur blanc illisible.
* **Solution apportée :** Refonte des styles CSS avec priorité forcée (`!important`) liant le fond (`var(--surface)`), le texte (`var(--text)`), les boutons radio et l'icône de calque aux tokens de design dynamiques de SantéSN. Le sélecteur s'adapte désormais instantanément au thème actif avec un contraste optimal.

### 4. L'accès à la caméra sur smartphone pour le scanner optique
* **Problème :** Les navigateurs mobiles modernes (Chrome Android, Safari iOS) bloquent strictement l'accès à la caméra via `navigator.mediaDevices.getUserMedia` dès lors que la page n'est pas servie sous un protocole sécurisé HTTPS.
* **Solution apportée :** Déploiement systématique de certificats SSL/TLS valides avec redirection HTTPS obligatoire et mise en place d'un mode de saisie manuelle de secours avec auto-complétion instantanée en cas de refus d'autorisation de la caméra par l'utilisateur.
