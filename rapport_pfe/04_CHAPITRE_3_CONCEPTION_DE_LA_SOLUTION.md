# CHAPITRE 3 : CONCEPTION DE LA SOLUTION

---

## 3.1. Démarche et méthode de conception

### 3.1.1. L'approche orientée objet et le langage UML
Pour traduire avec fidélité les règles de gestion complexes du tiers payant médical en une architecture logicielle robuste et maintenable, nous avons adopté une **démarche de conception orientée objet basée sur le standard UML (Unified Modeling Language)**. 

Le langage UML nous a permis de modéliser le système sous deux perspectives complémentaires :
1. **La perspective structurelle (statique) :** Définir la structure interne du système, les entités métier fondamentales, leurs attributs et les relations qui les unissent (Diagramme de classes, Modèle Conceptuel et Logique de Données).
2. **La perspective comportementale (dynamique) :** Représenter les interactions temporelles entre les acteurs et la plateforme lors de transactions sensibles, telles que la validation d'une ordonnance en pharmacie ou l'instruction d'un remboursement (Diagrammes de cas d'utilisation, Diagrammes de séquence).

### 3.1.2. Les patrons de conception architecturaux retenus
La conception de SantéSN s'appuie sur des patrons de conception (*Design Patterns*) reconnus de l'ingénierie logicielle :
* **Le patron MVT (Modèle - Vue - Template) :** Déclinaison élégante du patron MVC adaptée au cadriciel Django. Le **Modèle** gère la persistance et l'intégrité des données ; le **Template** gère le rendu visuel HTML/CSS/JS ; la **Vue** orchestre la logique métier, contrôle les permissions et fait le pont entre modèles et templates.
* **Le patron Scoped QuerySet (Multi-Tenant Isolation) :** Patron d'isolation garantissant que chaque requête en base de données filtre automatiquement les enregistrements en fonction de l'organisme d'appartenance de l'utilisateur connecté (*Fail-Closed Tenant Partitioning*).
* **Le patron Service Layer (Couche de Services) :** Encapsulation de la logique algorithmique complexe (génération d'empreintes HMAC, calcul de l'écrêtement de plafond annuel, calcul de quote-part) dans des modules d'aide autonomes et réutilisables.

---

## 3.2. Architecture générale de la solution

### 3.2.1. Vue d'ensemble de l'architecture applicative
L'architecture globale de SantéSN est conçue selon un modèle multicouche moderne en environnement Cloud :

```
                        ARCHITECTURE GLOBALE EN COUCHES DE SANTÉSN
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │ 1. COUCHE CLIENT (FRONTEND PWA RESPONSIVE)                                      │
  │    Navigateurs Desktop & Mobile (Chrome, Safari, Firefox, Edge)                  │
  │    • Interface HTML5 sémantique / CSS Tokens / JavaScript Vanilla                │
  │    • PWA Service Worker (Cache hors-ligne des cartes d'assurés)                  │
  │    • Moteur de scan optique par caméra en temps réel (jsQR)                      │
  │    • Cartographie interactive SIG Leaflet (Tuiles Google Maps & Esri)            │
  └────────────────────────────────────────┬─────────────────────────────────────────┘
                                           │ Requêtes HTTPS chiffrées (TLS 1.3)
                                           ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │ 2. COUCHE ACCÈS, SÉCURITÉ & PROXY (GATEWAY CLOUD)                                │
  │    Vercel Edge Network / Reverse Proxy Nginx                                     │
  │    • Terminaison SSL/TLS, Pare-feu applicatif (WAF)                              │
  │    • Protection Anti-DDoS, Routage dynamique, Compression Brotzi / Gzip          │
  └────────────────────────────────────────┬─────────────────────────────────────────┘
                                           │ Interface WSGI (Web Server Gateway)
                                           ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │ 3. COUCHE MÉTIER & APPLICATION (BACKEND DJANGO 5.2 / PYTHON 3.12+)               │
  │    • Middlewares de Sécurité (CSRF, Clickjacking, SecurityHeaders)               │
  │    • Moteur d'Authentification & Contrôle d'Accès RBAC (5 rôles hermétiques)     │
  │    • Gestionnaire de Tiers Payant & Algorithme d'écrêtement des plafonds         │
  │    • Module Cryptographique HMAC-SHA256 (Sceau d'intégrité ordonnances)          │
  │    • Générateur de documents certifiés PDF A4 (Tampon SantéSN)                   │
  │    • Connecteur Passerelle WhatsApp Meta Cloud API v21.0                         │
  └────────────────────────────────────────┬─────────────────────────────────────────┘
                                           │ Pilote psycopg3 / Pool de connexions
                                           ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │ 4. COUCHE PERSISTANCE DE DONNÉES (DATABASE CLOUD)                                │
  │    Base de Données Relationnelle PostgreSQL (Cluster Cloud Neon Serverless)      │
  │    • Transactions ACID intégrales avec verrouillage pessimiste (`select_for_update`)│
  │    • Indexation B-Tree & Recherche textuelle normalisée                          │
  │    • Réplication synchrone et sauvegardes automatisées chiffrées au repos        │
  └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3.3. Modélisation détaillée

### 3.3.1. Diagramme de cas d'utilisation global
Le diagramme de cas d'utilisation synthétise les fonctionnalités majeures offertes par la plateforme à chaque profil d'acteur :

```
                        DIAGRAMME DE CAS D'UTILISATION GLOBAL
  ┌─────────────────┐
  │     ASSURÉ      │ ───> Consulter sa carte dématérialisée avec QR Code
  │    (PATIENT)    │ ───> Suivre la consommation du plafond annuel familial
  │                 │ ───> Géolocaliser les prestataires partenaires (Leaflet)
  │                 │ ───> Soumettre une demande de remboursement hors réseau
  │                 │ ───> Déclarer un ayant droit avec justificatif
  └─────────────────┘
  ┌─────────────────┐
  │     MÉDECIN     │ ───> Authentifier un patient (matricule ou scan QR)
  │   TRAITANT      │ ───> Consulter le dossier médical et historique
  │                 │ ───> Rédiger une ordonnance électronique
  │                 │ ───> Signer avec sceau d'intégrité HMAC-SHA256
  │                 │ ───> Exporter l'ordonnance A4 officielle en PDF
  └─────────────────┘
  ┌─────────────────┐
  │   PHARMACIEN    │ ───> Scanner le QR Code ordonnance par caméra
  │   D'OFFICINE    │ ───> Valider l'authenticité et statut de la prescription
  │                 │ ───> Calculer automatiquement la quote-part et tiers payant
  │                 │ ───> Délivrer les médicaments (verrouillage atomique ACID)
  │                 │ ───> Télétransmettre les créances à l'IPM
  └─────────────────┘
  ┌─────────────────┐
  │  GESTIONNAIRE   │ ───> Piloter le tableau de bord financier de l'IPM
  │     D'IPM       │ ───> Paramétrer les conventions tarifaires prestataires
  │                 │ ───> Configurer les plans de couverture et plafonds
  │                 │ ───> Instruire les demandes de remboursement hors réseau
  │                 │ ───> Générer les bordereaux mensuels de liquidation
  └─────────────────┘
  ┌─────────────────┐
  │  ADMINISTRATEUR │ ───> Gérer les comptes et attributions de rôles (RBAC)
  │     SYSTÈME     │ ───> Consulter le journal d'audit immuable (Audit Trail)
  │                 │ ───> Superviser les métriques techniques et la conformité CDP
  └─────────────────┘
```

---

### 3.3.2. Diagrammes de séquence des scénarios critiques

#### A. Scénario 1 : Délivrance sécurisée d'une ordonnance en pharmacie
Ce diagramme détaille les échanges garantissant qu'aucune ordonnance ne puisse être délivrée deux fois :

```
         DIAGRAMME DE SÉQUENCE : VALIDATION ET DÉLIVRANCE ATOMIQUE EN PHARMACIE
  Assuré         Pharmacien              SantéSN Web/PWA            Base PostgreSQL
    │                 │                         │                         │
    │ Présente QR code│                         │                         │
    │────────────────>│ Active la caméra        │                         │
    │                 │────────────────────────>│                         │
    │                 │ Vise le QR Code         │ Capture frame vidéo     │
    │                 │                         │ Décode avec jsQR        │
    │                 │                         │ Extrait ID & Signature  │
    │                 │                         │────────────────────────>│
    │                 │                         │                         │ SELECT FOR UPDATE
    │                 │                         │                         │ (Verrou pessimiste)
    │                 │                         │<────────────────────────│
    │                 │                         │ Vérifie Statut==ACTIVE  │
    │                 │                         │ Vérifie Sceau HMAC      │
    │                 │ Affiche écran contrôle  │                         │
    │                 │<────────────────────────│                         │
    │                 │                         │                         │
    │                 │ Clique sur "Confirmer   │                         │
    │                 │  la délivrance"         │                         │
    │                 │────────────────────────>│ TRANSACTION ATOMIQUE :  │
    │                 │                         │ 1. Statut = DELIVREE    │
    │                 │                         │ 2. Date/Heure délivrance│
    │                 │                         │ 3. Débit plafond assuré │
    │                 │                         │ 4. Création créance IPM │
    │                 │                         │────────────────────────>│
    │                 │                         │                         │ COMMIT Transaction
    │                 │                         │<────────────────────────│
    │ Délivre médica- │ Reçu de dispensation    │                         │
    │ ments & quote-  │<────────────────────────│                         │
    │ part restante   │                         │                         │
    │<────────────────│                         │                         │
```

---

#### B. Scénario 2 : Calcul dynamique de l'écrêtement du plafond annuel
Lorsqu'un médecin prescrit un acte ou qu'un pharmacien délivre un médicament, le moteur tarifaire de SantéSN évalue instantanément le reliquat du plafond annuel de la famille de l'assuré :

```
                      ALGORITHME D'ÉCRÊTEMENT DU TIERS PAYANT
                          
                         Montant Total Dépense (M)
                                    │
                                    ▼
                     Taux conventionnel de l'IPM (ex: 80%)
                      Part Théorique Assurance = M * 80%
                      Part Théorique Assuré    = M * 20%
                                    │
                                    ▼
                    Plafond Annuel Restant de la Famille (R)
                                    │
                   ┌────────────────┴────────────────┐
                   ▼                                 ▼
             Si Part Théo <= R                 Si Part Théo > R
           (Plafond Suffisant)               (Dépassement de Plafond)
                   │                                 │
                   ▼                                 ▼
         Part IPM Réelle = Part Théo       Part IPM Réelle = R (écrêtée)
         Quote-part Assuré = Part Théo     Quote-part Assuré = M - R
                   │                                 │
                   └────────────────┬────────────────┘
                                    ▼
                         Enregistrement Transaction
                         Notification instantanée
```

---

### 3.3.3. Modèle Conceptuel et Logique de Données (MCD / MLD)

La base de données relationnelle de SantéSN est structurée autour d'entités normalisées respectant la troisième forme normale (3FN) :

```
                  MODÈLE RELATIONNEL DES ENTITÉS FONDAMENTALES
  ┌─────────────────────────────────┐           ┌─────────────────────────────────┐
  │           ORGANISME             │           │         PLAN_COUVERTURE         │
  ├─────────────────────────────────┤           ├─────────────────────────────────┤
  │ PK id                           │ 1       * │ PK id                           │
  │    code (ex: IPM-SONATEL)       │───────────│ FK organisme_id                 │
  │    nom                          │           │    nom (ex: Formule Cadres)     │
  │    type (IPM, Mutuelle, Assur)  │           │    taux_pharmacie (ex: 80%)     │
  │    telephone, email             │           │    taux_consultation (ex: 90%)  │
  └─────────────────────────────────┘           │    plafond_annuel_global        │
                   │                            └─────────────────────────────────┘
                   │ 1                                           │ 1
                   │                                             │
                   │ *                                           │ *
  ┌─────────────────────────────────┐           ┌─────────────────────────────────┐
  │          UTILISATEUR            │           │             PATIENT             │
  ├─────────────────────────────────┤           ├─────────────────────────────────┤
  │ PK id                           │ 1       1 │ PK id                           │
  │ FK organisme_id (optionnel)     │───────────│ FK user_id                      │
  │    email, password_hash         │           │ FK plan_couverture_id           │
  │    first_name, last_name        │           │    numero_carte (ex: SN-12345)  │
  │    role (ADMIN, GES, MED, PHA)  │           │    plafond_annuel_consomme      │
  │    phone_number                 │           │    est_ayant_droit (bool)       │
  └─────────────────────────────────┘           │ FK ouvrant_droit_id (parent)    │
                   │                            └─────────────────────────────────┘
                   │                                             │ 1
                   │                                             │
                   │                                             │ *
  ┌─────────────────────────────────┐           ┌─────────────────────────────────┐
  │           PRESTATAIRE           │           │           ORDONNANCE            │
  ├─────────────────────────────────┤           ├─────────────────────────────────┤
  │ PK id                           │ 1       * │ PK id                           │
  │    nom (ex: Clinique de l'Océan)│───────────│ FK patient_id                   │
  │    type (HOPITAL, CLINIQUE, PHA)│           │ FK medecin_id                   │
  │    ville, adresse, telephone    │           │ FK pharmacie_delivrance_id      │
  │    partenaire (bool)            │           │    code_qr (UUID dynamique)     │
  │    latitude, longitude (GPS)    │           │    sceau_hmac (Signature SHA256)│
  └─────────────────────────────────┘           │    statut (ACTIVE, DELIVREE)    │
                   │                            │    date_prescription            │
                   │ 1                          │    date_delivrance              │
                   │                            └─────────────────────────────────┘
                   │ *                                           │ 1
  ┌─────────────────────────────────┐                            │
  │      CONVENTION_PRESTATAIRE     │                            │ *
  ├─────────────────────────────────┤           ┌─────────────────────────────────┐
  │ PK id                           │           │        LIGNE_ORDONNANCE         │
  │ FK organisme_id                 │           ├─────────────────────────────────┤
  │ FK prestataire_id               │           │ PK id                           │
  │    numero_convention            │           │ FK ordonnance_id                │
  │    statut (ACTIF, SUSPENDU)     │           │    nom_medicament (DCI)         │
  │    tiers_payant_actif (bool)    │           │    dosage, forme, quantite      │
  └─────────────────────────────────┘           │    posologie                    │
                                                └─────────────────────────────────┘
```

---

## 3.4. Choix des outils, technologies et matériels

### 3.4.1. Justification technologique approfondie
Le tableau suivant expose la cohérence des choix techniques opérés lors de la conception :

| Composant | Technologie Retenue | Justification Technique et Métier |
| :--- | :--- | :--- |
| **Langage Backend** | **Python 3.12+** | Syntaxe expressive et lisible, typage moderne, écosystème de librairies cryptographiques et mathématiques éprouvées. |
| **Cadriciel Web** | **Django 5.2 LTS** | Framework de référence pour les systèmes bancaires et de santé. Sécurité intégrée par défaut (*Anti-CSRF, Anti-XSS, Protection IDOR*), ORM performant. |
| **Base de Données** | **PostgreSQL (Neon)** | Cluster cloud serverless garantissant la conformité transactionnelle ACID, le support des contraintes d'intégrité relationnelle et les extensions SIG. |
| **Cartographie SIG** | **Leaflet 1.9.4** | Bibliothèque cartographique légère, compatible mobile, intégrant les tuiles Google Maps (Plan et Satellite) et Esri World Imagery sans dépendance API payante. |
| **Scanner Optique** | **jsQR 1.4.0** | Décodeur de QR Code 100 % JavaScript s'exécutant directement dans le navigateur du pharmacien via les flux de l'API HTML5 `MediaDevices.getUserMedia()`. |
| **Documents PDF** | **ReportLab & XHTML2PDF** | Génération serveur de fiches de soins et d'ordonnances A4 certifiées avec tampons vectoriels et QR codes dynamiques. |
| **Frontend & UX** | **CSS Modern Tokens & PWA** | Feuilles de style fondées sur des variables CSS natives pour une gestion instantanée du mode sombre sans surcharge réseau ni dépendance NPM lourde. |
| **Passerelle Tiers** | **WhatsApp Cloud API** | Envoi de notifications d'actes et d'alertes de plafond directement sur l'application de messagerie la plus utilisée au Sénégal. |

### 3.4.2. Environnement matériel cible
L'application SantéSN a été conçue pour fonctionner avec une frugalité matérielle maximale :
* **Côté Assuré :** N'importe quel smartphone Android (dès Android 7.0) ou iOS équipé d'un navigateur moderne (Chrome, Safari, Firefox).
* **Côté Professionnel de Santé :** Ordinateur de comptoir d'officine ou tablette dotée d'une simple webcam standard (720p ou 1080p) pour le scan optique instantané des ordonnances.
* **Côté Infrastructure Serveur :** Déploiement serverless conteneurisé consommant moins de 256 Mo de mémoire vive par instance de calcul.
