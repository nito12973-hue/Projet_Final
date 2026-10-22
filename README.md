# SantéSN — Plateforme Pour la prise en charge médicale dans une structure

[![CI SantéSN - Tests & Validation](https://github.com/nito12973-hue/Projet_Final/actions/workflows/ci.yml/badge.svg)](https://github.com/nito12973-hue/Projet_Final/actions/workflows/ci.yml)
[![Documentation Mintlify](https://img.shields.io/badge/Documentation%20Mintlify-En%20Ligne-0E7C86?style=flat&logo=gitbook&logoColor=white)](https://https-projet-final-bice-vercel-app.mintlify.site/introduction)
[![Tests Automatisés](https://img.shields.io/badge/Tests-946%20valid%C3%A9s%20%E2%9C%94-success.svg)](Plateform_medicale/tests.py)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://docs.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

SantéSN est une solution web médicale et assurantielle moderne conçue pour le contexte des **Institutions de Prévoyance Maladie (IPM)**, des mutuelles de santé et des régimes d'assurance au Sénégal. Elle élimine la fraude au papier, automatise le calcul en temps réel du tiers payant et interconnecte l'ensemble des acteurs du système de santé sous le contrôle des règles strictes de la Commission de Protection des Données Personnelles (**CDP** - Loi 2008-12).

---

## 📚 Documentation Technique Officielle (Mintlify)

La documentation technique exhaustive, interactive et vivante de la plateforme SantéSN est hébergée et déployée sur **Mintlify** :

👉 **[Accéder à la Documentation Technique SantéSN sur Mintlify](https://https-projet-final-bice-vercel-app.mintlify.site/introduction)**

[![Portail Documentation Mintlify](https://img.shields.io/badge/Portail%20Documentation-Mintlify%20Live-0E7C86?style=for-the-badge&logo=gitbook&logoColor=white)](https://https-projet-final-bice-vercel-app.mintlify.site/introduction)

### 🔗 Accès Direct aux Sections Clés

| Section Clé | Thématiques & Contenu Technique | Accès Direct & Badge |
| :--- | :--- | :--- |
| 🏗️ **Architecture & Modèles** | Architecture applicative, modèle relationnel, isolation multi-tenant stricte, Zero-Trust et conformité CDP Sénégal. | [![Architecture](https://img.shields.io/badge/Architecture-Consulter-0E7C86?style=flat&logo=diagram-next&logoColor=white)](https://https-projet-final-bice-vercel-app.mintlify.site/architecture)<br />[Consulter la section Architecture](https://https-projet-final-bice-vercel-app.mintlify.site/architecture) |
| 🏢 **Espace Gestionnaire** | Pilotage métier IPM, conventions prestataires, régimes de couverture, validation des prises en charge, remboursements et liquidations. | [![Espace Gestionnaire](https://img.shields.io/badge/Espace%20Gestionnaire-Consulter-0E7C86?style=flat&logo=shield&logoColor=white)](https://https-projet-final-bice-vercel-app.mintlify.site/fonctionnalites/espace-gestionnaire)<br />[Consulter l'Espace Gestionnaire](https://https-projet-final-bice-vercel-app.mintlify.site/fonctionnalites/espace-gestionnaire) |
| 💬 **Passerelle WhatsApp** | Intégration Meta Cloud API v21.0, webhook cryptographique HMAC-SHA256 fail-closed, bot interactif patient et rappels de rendez-vous. | [![WhatsApp](https://img.shields.io/badge/WhatsApp-Consulter-25D366?style=flat&logo=whatsapp&logoColor=white)](https://https-projet-final-bice-vercel-app.mintlify.site/fonctionnalites/notifications-whatsapp)<br />[Consulter l'intégration WhatsApp](https://https-projet-final-bice-vercel-app.mintlify.site/fonctionnalites/notifications-whatsapp) |
| 🚀 **DevOps & Exploitation** | Pipeline GitHub Actions CI/CD, conteneurs Docker multi-stage, supervision Prometheus, WhiteNoise et déploiements Vercel / Render. | [![DevOps](https://img.shields.io/badge/DevOps%20%26%20Ops-Consulter-095059?style=flat&logo=docker&logoColor=white)](https://https-projet-final-bice-vercel-app.mintlify.site/technique/devops-exploitation)<br />[Consulter la section DevOps](https://https-projet-final-bice-vercel-app.mintlify.site/technique/devops-exploitation) |

---

## ⚡ Déploiement en 1 Clic (Mode Cloud & Test Hors-Local)

Pour tester l'application directement en ligne sur Internet sans configuration locale, cliquez sur le bouton ci-dessous :

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/nito12973-hue/Projet_Final)

> **Note :** Le déploiement initialise automatiquement la base de données et les comptes de démonstration. L'application est immédiatement opérationnelle en HTTPS.

---

## 👥 Comptes de Démonstration (Mot de passe unique : `Password123`)

| Rôle | Identifiant (Email) | Mot de passe | Espace & Fonctionnalités Clés |
| :--- | :--- | :--- | :--- |
| ⚙️ **Administrateur IT** | `admin@santesn.sn` | `Password123` | Supervision technique, métriques Prometheus, journal d'audit, IAM |
| 🏢 **Gestionnaire IPM** | `gestionnaire@santesn.sn` | `Password123` | Dashboard financier, conventions, plans de couverture, liquidations, exports PDF/Excel |
| 🧑‍⚕️ **Médecin Traitant** | `medecin@santesn.sn` | `Password123` | Agenda des consultations, dossiers patients, ordonnance sécurisée A4 certifiée |
| 💊 **Pharmacien d'Officine** | `pharmacien@santesn.sn` | `Password123` | Scanner d'ordonnance par caméra, validation atomique anti-double délivrance |
| 👤 **Assuré (Patient)** | `assure@santesn.sn` | `Password123` | Carte dématérialisée (QR Code / ISO), suivi du plafond annuel, ayants droit, RDV |

---

## 🌟 Fonctionnalités Majeures

1. **Carte de Prise en Charge Dématérialisée :** Format physique ISO 7810 ID-1 avec micro-puce dorée et QR Code dynamique vectoriel.
2. **Ordonnance Sécurisée Anti-Fraude :** Tampon officiel SantéSN certifié, sceau d'intégrité HMAC et verrouillage transactionnel lors de la délivrance en pharmacie.
3. **Gestion Intelligente des Plafonds Annuels :** Écrêtement automatique de la part assurance en fonction du reliquat budgétaire annuel familial restant.
4. **Scanner Optique Pharmacien :** Reconnaissance instantanée par webcam (`jsQR@1.4.0`) et mode de saisie manuelle sécurisée.
5. **Cartographie Sanitaire Intégrée (GIS) :** Géolocalisation des prestataires partenaires (Hôpitaux, Pharmacies, Cliniques) avec calcul d'itinéraire.
6. **Passerelle WhatsApp Meta Cloud API :** Notifications instantanées des assurés et assistant conversationnel WhatsApp pour la consultation des droits.
7. **Contrôle d'Accès Strict (RBAC & Multi-tenant) :** Isolation hermétique des 5 rôles et protection contre les attaques CSRF et IDOR.
8. **Politique Zéro-Emoji dans le Core Métier :** Respect scrupuleux des chartes institutionnelles avec 100% d'icônes vectorielles SVG intégrées.

---

## 🛠️ Installation et Lancement en Local

```bash
# 1. Cloner le dépôt
git clone https://github.com/nito12973-hue/Projet_Final.git
cd Projet_Final

# 2. Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Linux/macOS
. env\Scripts\Activate   # Sur Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations et charger les données de démo
python manage.py migrate
python manage.py seed_demo

# 5. Démarrer le serveur de développement
python manage.py runserver

```

---

## 🧪 Tests Automatisés

Le projet inclut une suite robuste de **946 tests unitaires, d'intégration et de sécurité** exécutés automatiquement via GitHub Actions (100% de succès) :

```bash
python manage.py test Plateform_medicale
```

---

## 📖 Documentation & Références du Projet

* 🌐 **[Documentation Technique Mintlify](https://https-projet-final-bice-vercel-app.mintlify.site/introduction)** : Guide technique exhaustif interactif hébergé sur Mintlify.
* 📘 [`GUIDE_UTILISATEUR.md`](GUIDE_UTILISATEUR.md) : Manuel d'utilisation détaillé pas-à-pas pour chacun des rôles.
* 📋 [`DECISIONS.md`](DECISIONS.md) : Registre des décisions architecturales et choix d'implémentation (ADR).
* ⚙️ [`FONCTIONNEMENT.txt`](FONCTIONNEMENT.txt) : Spécifications détaillées de l'architecture, modèles de données et règles métier internes.
