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
- **Décision Praticiens :** L'IPM ne crée pas les médecins/pharmaciens, elle conventionne des établissements de soins. L'administration centrale référence les structures et praticiens, l'IPM gère ses conventions.

