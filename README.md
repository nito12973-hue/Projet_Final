# 🏥 SantéSN — Plateforme Intégrée de Gestion du Tiers Payant & Dématérialisation du Parcours de Soins

[![CI SantéSN - Tests & Validation](https://github.com/nito12973-hue/Projet_Final/actions/workflows/ci.yml/badge.svg)](https://github.com/nito12973-hue/Projet_Final/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://docs.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

SantéSN est une solution web médicale et assurantielle moderne conçue pour le contexte des **Institutions de Prévoyance Maladie (IPM)**, des mutuelles de santé et des régimes d'assurance au Sénégal. Elle élimine la fraude au papier, automatise le calcul en temps réel du tiers payant et interconnecte l'ensemble des acteurs du système de santé.

---

## 🚀 Déploiement en 1 Clic (Mode Cloud & Test Hors-Local)

Pour tester l'application directement en ligne sur Internet sans configuration locale, cliquez sur le bouton ci-dessous :

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/nito12973-hue/Projet_Final)

> **Note :** Le déploiement initialise automatiquement la base de données et les comptes de démonstration. L'application est immédiatement opérationnelle en HTTPS.

---

## 🔑 Comptes de Démonstration (Mot de passe unique : `Password123`)

| Rôle | Identifiant (Email) | Mot de passe | Espace & Fonctionnalités Clés |
| :--- | :--- | :--- | :--- |
| 🛡️ **Administrateur IPM** | `admin@santesn.sn` | `Password123` | Dashboard financier, plans de couverture, liquidations, exports PDF/Excel |
| 👤 **Assuré (Patient)** | `assure@santesn.sn` | `Password123` | Carte dématérialisée (QR Code / ISO), suivi du plafond annuel, ayants droit, RDV |
| 🩺 **Médecin Traitant** | `medecin@santesn.sn` | `Password123` | Agenda des consultations, dossiers patients, ordonnance sécurisée A4 certifiée |
| 💊 **Pharmacien d'Officine** | `pharmacien@santesn.sn` | `Password123` | Scanner d'ordonnance par caméra, validation atomique anti-double délivrance |

---

## ✨ Fonctionnalités Majeures

1. **Carte de Prise en Charge Dématérialisée :** Format physique ISO 7810 ID-1 avec micro-puce dorée et QR Code dynamique vectoriel.
2. **Ordonnance Sécurisée Anti-Fraude :** Tampon officiel SantéSN certifié et verrouillage transactionnel lors de la délivrance en pharmacie.
3. **Gestion Intelligente des Plafonds Annuels :** Écrêtement automatique de la part assurance en fonction du reliquat budgétaire annuel familial restant.
4. **Scanner Optique Pharmacien :** Reconnaissance instantanée par webcam (`html5-qrcode`) et mode de saisie manuelle sécurisée.
5. **Cartographie Sanitaire Intégrée (GIS) :** Géolocalisation des prestataires partenaires (Hôpitaux, Pharmacies, Cliniques) avec calcul d'itinéraire.
6. **Contrôle d'Accès Strict (RBAC) :** Isolation hermétique des 4 rôles et protection contre les attaques CSRF et IDOR.
7. **Politique Zéro-Emoji :** Respect scrupuleux des chartes institutionnelles avec 100% d'icônes vectorielles SVG intégrées.

---

## 💻 Installation et Lancement en Local

```bash
# 1. Cloner le dépôt
git clone https://github.com/nito12973-hue/Projet_Final.git
cd Projet_Final

# 2. Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Linux/macOS
.env\Scripts\Activate   # Sur Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations et charger les données de démo
python manage.py migrate
python manage.py seed_demo

# 5. Démarrer le serveur de développement
python manage.py runserver
```

L'application est accessible à l'adresse : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧪 Tests Automatisés

Le projet inclut une suite de **107 tests unitaires et de sécurité** exécutés automatiquement via GitHub Actions :

```bash
python manage.py test
```

---

## 📚 Documentation Technique

* 📘 [`GUIDE_UTILISATEUR.md`](GUIDE_UTILISATEUR.md) : Manuel d'utilisation détaillé pas-à-pas pour chaque profil.
* ⚙️ [`FONCTIONNEMENT.txt`](FONCTIONNEMENT.txt) : Spécifications détaillées de l'architecture et des règles métier.
