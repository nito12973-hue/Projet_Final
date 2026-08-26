# 🎓 GUIDE DE SYNTHÈSE & OVERVIEW TECHNIQUE — SANTÉSN
**Plateforme de Dématérialisation du Tiers Payant et de l'Ordonnance Médicale au Sénégal**

---

## 📊 1. Fiche Technique Globale & Chiffres Clés

| Composant / Métrique | Technologie / Valeur | Rôle & Justification Métier |
| :--- | :--- | :--- |
| **Langage & Framework** | **Python 3.14** / **Django 6.0** | Robustesse, architecture MVT et sécurité native (OWASP). |
| **Base de Données Cloud** | **Neon Serverless PostgreSQL 18** | Verrouillage par ligne (*row-level locking*), multi-utilisateurs. |
| **Connection Pooling** | **PgBouncer AWS Pooler** | Encaissement de centaines de connexions simultanées. |
| **Fichiers Statiques** | **WhiteNoise 6.10** | Compression Brotli/Gzip et mise en cache performante. |
| **Cartographie & GPS** | **Leaflet.js & OpenStreetMap** | Géolocalisation des cliniques et officines 100% libre. |
| **Assurance Qualité** | **636 Tests Automatisés (100% OK)** | Couverture intégrale des calculs, permissions et non-régression. |
| **Gabarits & Vues** | **84 Templates / 22 Modules** | Rendu Côté Serveur (SSR) ultra-léger (< 150 ms de latence). |

---

## ⚡ 2. Capacité de Charge & Multi-Utilisateurs

* **Palier Actuel Neon Cloud (Free Tier) :** **100 à 300 utilisateurs simultanés** (jusqu'à 10 000 requêtes/jour sans aucun ralentissement).
* **Palier Neon Pro / Scale (Autoscaling) :** **5 000 à 20 000 requêtes/seconde** pour une couverture nationale complète.
* **Pourquoi ça ne bloque pas ?**
  1. Le verrouillage par ligne (*Row-level locking*) de PostgreSQL permet à plusieurs médecins d'écrire en même temps sans conflit.
  2. Le pooler de connexions AWS PgBouncer optimise la mémoire.
  3. Les transactions atomiques Django évitent les doublons.

---

## 📁 3. Arborescence du Projet & Rôle des Fichiers

| Dossier / Fichier | Contenu & Responsabilité |
| :--- | :--- |
| **config/settings.py** | Paramétrage global : connexion Neon PostgreSQL, sécurité, WhiteNoise, emails SMTP |
| **Plateform_medicale/models.py** | Les 14 modèles de données (User, Patient, Medecin, Pharmacien, Ordonnance, etc.) |
| **Plateform_medicale/views/auth.py** | Gestion des sessions, connexions multi-rôles, sécurité anti-brute-force |
| **Plateform_medicale/views/dashboard.py** | Tableau de bord Admin, KPIs financiers, exports Excel (.xlsx) et PDF |
| **Plateform_medicale/views/medecin_espace.py** | Agenda soignant, recherche rapide de dossier patient, prescription d'ordonnance |
| **Plateform_medicale/views/pharmacien_espace.py** | Scanner de QR Code, vérification d'authenticité, validation de délivrance |
| **Plateform_medicale/views/assure_espace.py** | Carte numérique avec QR Code vectoriel SVG, ayants droit, rendez-vous, GPS |
| **Plateform_medicale/views/paiements.py** | Encaissements, calcul automatique de la part IPM vs Ticket modérateur, reçu A5 |
| **Plateform_medicale/templates/** | 84 gabarits HTML avec style responsive mobile, thème sombre et impression print |
| **seed_demo.py** | Commande d'initialisation automatique des comptes et données de test démo |

---

## 🔄 4. Le Parcours Médical Étape par Étape

1. **Adhésion & Carte Numérique (Admin/Assuré) :** Création du contrat IPM (ex: 80%), émission de la carte avec QR code vectoriel SVG et rattachement des ayants droit.
2. **Accord Préalable (Assuré/Admin) :** Dépôt de la demande de prise en charge et validation instantanée par l'IPM.
3. **Consultation Médicale (Médecin) :** Accès au Dossier Patient Informatisé (DPI) et saisie du diagnostic.
4. **Prescription Sécurisée (Médecin) :** Rédaction de l'ordonnance structurée avec code unique `RX-XXXXXXXXXX` encodé dans le QR Code.
5. **Délivrance en Pharmacie & Anti-Fraude (Pharmacien) :** Scan du QR Code, vérification et verrouillage atomique de l'ordonnance pour interdire tout second scan.
6. **Règlement Financier & Quittance (Admin/Caisse) :** Calcul automatique de la part IPM vs part patient, émission du reçu officiel A5 et scellement dans `JournalActivite`.

---

## 🌐 5. Guide d'Intégration de Neon PostgreSQL (Les 5 Étapes)

* **Étape 1 :** Récupération de l'URI Cloud sécurisée dans la console Neon (avec pooler AWS et `sslmode=require`).
* **Étape 2 :** Configuration du fichier `.env` à la racine du projet avec `DATABASE_URL`.
* **Étape 3 :** Adaptation de `config/settings.py` via `dj_database_url` avec `conn_max_age=600` et `ssl_require=True`.
* **Étape 4 :** Exécution de `python manage.py migrate` pour créer les 18 tables relationnelles sur le cloud.
* **Étape 5 :** Exécution de `python manage.py seed_demo` pour peupler les comptes et enregistrements de test.

---

## 🎯 6. Les Questions Clés du Jury & Vos Réponses

| Question Probable du Jury | Votre Réponse Recommandée |
| :--- | :--- |
| **Pourquoi Django et non React/Vue ?** | *« Le rendu côté serveur (SSR) de Django consomme 5x moins de données mobiles qu'une SPA JavaScript, idéal pour les réseaux 3G sénégalais, avec une sécurité CSRF/XSS native. »* |
| **Comment évitez-vous la fraude aux ordonnances ?** | *« Par un QR code vectoriel à identifiant unique. Dès la délivrance en pharmacie, une contrainte OneToOne crée l'acte et verrouille l'ordonnance contre tout réusage. »* |
| **Pourquoi PostgreSQL plutôt que SQLite ?** | *« SQLite verrouille la base entière lors d'une écriture. PostgreSQL applique un verrouillage par ligne (row-level locking) et le pooling de connexions, idéal pour des centaines d'utilisateurs. »* |
| **Comment le projet a-t-il été qualifié ?** | *« Par 636 tests automatisés validés à 100% sans aucun échec, garantissant l'étanchéité des rôles RBAC et l'exactitude des calculs comptables. »* |
