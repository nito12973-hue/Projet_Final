# Guide utilisateur — SantéSN

[![Documentation Technique Mintlify](https://img.shields.io/badge/Documentation%20Technique-Mintlify-0E7C86?style=for-the-badge&logo=gitbook&logoColor=white)](https://documentation-santesn.mintlify.app/docs/introduction)
[![Statut Tests](https://img.shields.io/badge/Tests-946%20valid%C3%A9s-success?style=for-the-badge&logo=checkmarx&logoColor=white)](Plateform_medicale/tests.py)

Ce guide explique comment utiliser la plateforme SantéSN au quotidien, écran par
écran, pour l'ensemble des 5 rôles : **Administrateur IT**, **Gestionnaire IPM**,
**Assuré**, **Médecin** et **Pharmacien**. Il complète `FONCTIONNEMENT.txt` (spécifications techniques) et
`DECISIONS.md` (registre d'architecture) sans les remplacer.

---

> ### 🌐 Documentation Technique Officielle en Ligne (Mintlify)
> Pour consulter l'ensemble des spécifications d'ingénierie, diagrammes d'architecture, guides de déploiement et intégrations d'API (WhatsApp, Prometheus, Neon Postgres), reportez-vous au portail en ligne officiel :
>
> 👉 **[Ouvrir le portail de documentation technique SantéSN sur Mintlify](https://documentation-santesn.mintlify.app/docs/introduction)**
>
> **Accès direct aux modules clés :**
> - 🏗️ **[Architecture & Sécurité](https://documentation-santesn.mintlify.app/docs/architecture)** : Architecture logicielle, modèle relationnel, multi-tenant et conformité CDP Sénégal.
> - 🏢 **[Espace Gestionnaire IPM](https://documentation-santesn.mintlify.app/docs/fonctionnalites/espace-gestionnaire)** : Pilotage des organismes, régimes, conventions prestataires et liquidations.
> - 💬 **[Passerelle WhatsApp](https://documentation-santesn.mintlify.app/docs/fonctionnalites/notifications-whatsapp)** : Notifications automatiques, webhook sécurisé HMAC-SHA256 et bot interactif.
> - 🚀 **[DevOps & Exploitation](https://documentation-santesn.mintlify.app/docs/technique/devops-exploitation)** : CI/CD GitHub Actions, conteneurisation Docker, métriques Prometheus et déploiement.

---

## Sommaire

- [Documentation technique Mintlify](#documentation-technique-mintlify)
- [Se connecter](#se-connecter)
- [Comptes de démonstration & tests locaux](#comptes-de-démonstration--tests-locaux)
- [Fonctions communes à tous les rôles](#fonctions-communes-à-tous-les-rôles)
- [Administrateur IT](#administrateur-it)
- [Gestionnaire (IPM & Mutuelles)](#gestionnaire-ipm--mutuelles)
- [Assuré (Patient)](#assuré-patient)
- [Médecin Traitant](#médecin-traitant)
- [Pharmacien d'Officine](#pharmacien-dofficine)
- [Passerelle WhatsApp & Notifications](#passerelle-whatsapp--notifications)
- [Questions fréquentes](#questions-fréquentes)

---

## Documentation technique Mintlify

La documentation technique de référence est centralisée et synchronisée en continu sur Mintlify. Elle permet aux équipes de développement, aux auditeurs de sécurité et aux administrateurs systèmes de retrouver les schémas d'architecture et les règles métier détaillées :

| Module | Contenu & Objectif | Badge & Lien |
| :--- | :--- | :--- |
| 🏗️ **Architecture Système** | Modèle relationnel, multi-tenant hermétique par organisme, politique Zero-Trust, protection des données personnelles (CDP Sénégal - Loi 2008-12). | [![Architecture](https://img.shields.io/badge/Architecture-Mintlify-0E7C86?style=flat&logo=diagram-next&logoColor=white)](https://documentation-santesn.mintlify.app/docs/architecture)<br />[Consulter l'architecture](https://documentation-santesn.mintlify.app/docs/architecture) |
| 🏢 **Espace Gestionnaire** | Conventions prestataires, barèmes de tiers payant, plafonds annuels, gestion des liquidations et instruction des remboursements. | [![Gestionnaire](https://img.shields.io/badge/Espace%20Gestionnaire-Mintlify-0E7C86?style=flat&logo=shield&logoColor=white)](https://documentation-santesn.mintlify.app/docs/fonctionnalites/espace-gestionnaire)<br />[Consulter l'espace gestionnaire](https://documentation-santesn.mintlify.app/docs/fonctionnalites/espace-gestionnaire) |
| 💬 **WhatsApp & Webhook** | Meta Cloud API v21.0, validation cryptographique des signatures HMAC-SHA256, menus conversationnels et alertes temps réel. | [![WhatsApp](https://img.shields.io/badge/WhatsApp-Mintlify-25D366?style=flat&logo=whatsapp&logoColor=white)](https://documentation-santesn.mintlify.app/docs/fonctionnalites/notifications-whatsapp)<br />[Consulter la section WhatsApp](https://documentation-santesn.mintlify.app/docs/fonctionnalites/notifications-whatsapp) |
| 🚀 **DevOps & Exploitation** | Pipeline GitHub Actions (946 tests automatisés), images Docker multi-stage, supervision Prometheus `/metrics/` et WhiteNoise. | [![DevOps](https://img.shields.io/badge/DevOps-Mintlify-095059?style=flat&logo=docker&logoColor=white)](https://documentation-santesn.mintlify.app/docs/technique/devops-exploitation)<br />[Consulter le guide DevOps](https://documentation-santesn.mintlify.app/docs/technique/devops-exploitation) |

---

## Se connecter

SantéSN n'a pas d'inscription libre : **seul un administrateur peut créer un
compte**. Si vous n'avez pas encore d'identifiants, contactez votre
administrateur.

1. Ouvrez la page de connexion (`/connexion/`).
2. Saisissez votre **email** et votre **mot de passe** (pas de nom
   d'utilisateur séparé — l'email sert d'identifiant).
3. Vous êtes automatiquement redirigé vers le tableau de bord correspondant à
   votre rôle : vous n'avez jamais à choisir un rôle vous-même, il est
   déterminé par votre compte.

Si l'application vient d'être installée et qu'aucun administrateur n'existe
encore, un assistant de configuration guide la création du tout premier
compte admin — cet écran ne réapparaît plus une fois un admin créé.

---

## Comptes de démonstration & tests locaux

Pour tester immédiatement les espaces ou préparer une soutenance, une commande dédiée initialise les comptes et jeux d'essai :

```bash
python manage.py seed_demo
```

Tous les comptes de démonstration utilisent le mot de passe unifié : `Passer123!` (ou `Password123`)

| Rôle | Email | Mot de passe | Description de l'espace & données incluses |
| :--- | :--- | :--- | :--- |
| **Administrateur IT** | `admin@santesn.sn` | `Passer123!` | Superuser complet : IAM, métriques Prometheus, journal d'audit de sécurité, passerelles. |
| **Gestionnaire IPM** | `gestionnaire@santesn.sn` | `Passer123!` | Direction IPM : conventions prestataires, plans de couverture, liquidations, remboursements. |
| **Médecin** | `medecin@santesn.sn` | `Passer123!` | Dr. Ibrahima Ndiaye (Cardiologue, Hôpital Principal) : agenda, DPI, prescriptions QR Code. |
| **Pharmacien** | `pharmacien@santesn.sn` | `Passer123!` | Awa Sow (Grande Pharmacie Dakaroise) : scanner QR Code ordonnance, délivrance atomique. |
| **Assuré** | `assure@santesn.sn` | `Passer123!` | Moussa Diop (Plan IPM 80%) : carte numérique QR SVG, ayants droit, RDV, géolocalisation. |

---

## Fonctions communes à tous les rôles

Ces trois éléments sont accessibles depuis le menu latéral, quel que soit
votre rôle :

- **Notifications** (icône cloche) : messages envoyés par la plateforme ou un gestionnaire,
  individuellement ou à tout un rôle. Un badge indique le nombre de
  notifications non lues ; ouvrez-en une pour la marquer comme lue.
- **Mot de passe** : changez votre mot de passe à tout moment sans perdre
  votre session en cours.
- **Réduire le menu** (desktop uniquement, chevron en haut du menu) : bascule
  le menu latéral en mode icônes seules pour gagner de la place à l'écran ;
  votre préférence est mémorisée d'une visite à l'autre. Sur mobile, le menu
  s'ouvre en tiroir via l'icône de menu (hamburger).

---

## Administrateur IT

> 💡 **Documentation technique détaillée :** Retrouvez le guide complet de l'infrastructure et de la sécurité sur [Mintlify — Sécurité](https://documentation-santesn.mintlify.app/docs/technique/securite).

### Ce que vous voyez en arrivant

Le tableau de bord Admin ouvre sur **la supervision informatique et l'infrastructure**. Il permet de piloter la sécurité globale de la plateforme :
- **Supervision Système** : statut de la base de données (PostgreSQL Neon / SQLite), utilisation disque, métriques de performance et passerelles externes.
- **Métriques Prometheus** : exposition `/metrics/` protégée pour la surveillance industrielle (temps de réponse, requêtes par minute, taux d'erreurs).
- **Journal d'audit** : traçabilité infalsifiable des accès et des actions sensibles.
- **Comptes bloqués & anti-bruteforce** : déblocage immédiat après échecs répétés.

Rappel du principe de moindre privilège : l'administrateur technique gère l'infrastructure et les accès IAM, mais **ne consulte jamais les dossiers médicaux détaillés**, ne saisit pas de diagnostic et n'émet pas d'ordonnance afin de respecter le secret médical garanti par la loi 2008-12 (CDP Sénégal).

### Gestion des utilisateurs (IAM)

- **Créer un utilisateur** : renseignez nom, email, rôle (Admin, Gestionnaire, Assuré, Médecin ou Pharmacien). Le mot de passe est généré automatiquement et affiché **une seule fois** à l'écran — notez-le ou transmettez-le de façon sécurisée.
- **Importer en masse depuis Excel** : téléchargez le modèle, remplissez une ligne par compte à créer. L'import est atomique (*tout ou rien*).
- **Modifier / activer / désactiver / supprimer** un compte, ou **réinitialiser son mot de passe**.
- **Export Excel** de la liste filtrée des utilisateurs.
- Par sécurité, un administrateur **ne peut pas** changer son propre rôle, se désactiver ou se supprimer lui-même.

### Journal d'activité & Sécurité

Le journal enregistre de manière immuable :
- Création, modification, activation, désactivation et suppression de comptes.
- Tentatives d'authentification suspectes et blocages temporaires.
- Événements système critiques et exports en masse.
- Le journal n'est modifiable par personne, pas même par un administrateur.

---

## Gestionnaire (IPM & Mutuelles)

> 💡 **Documentation technique détaillée :** Retrouvez le guide complet de l'Espace Gestionnaire sur [Mintlify — Espace Gestionnaire](https://documentation-santesn.mintlify.app/docs/fonctionnalites/espace-gestionnaire).

Le Gestionnaire est le cœur opérationnel de l'Institution de Prévoyance Maladie (IPM) ou de la Mutuelle.

### Tableau de bord financier & opérationnel

Le tableau de bord Gestionnaire ouvre sur les actions prioritaires :
- **Prises en charge à instruire** : dossiers en attente avec calcul automatique du reste à charge et vérification du plafond annuel familial.
- **Demandes de remboursement** : factures directes déposées par les assurés pour des soins hors conventionnement direct.
- **Paiements en attente de liquidation** : validation des règlements aux prestataires de santé partenaires.
- **Indicateurs financiers** : montants engagés, consommations par plan de couverture et solde global de l'organisme.

### Organismes & Multi-tenant

- Création et gestion des structures d'assurance (IPM d'entreprises, mutuelles professionnelles).
- Rattachement des assurés principaux à leur organisme de tutelle.
- Isolation stricte des données financières entre chaque organisme.

### Conventions Prestataires

- Conventionnement des établissements de santé (hôpitaux, cliniques, pharmacies, cabinets).
- Négociation des taux de prise en charge et des remises applicables par prestataire.
- Suivi des dates de validité et des coordonnées GPS pour la cartographie des soins.

### Plans de couverture & Gestion des Plafonds

- Paramétrage des taux de couverture (ex: 80%, 100%) et des plafonds annuels en FCFA.
- Le système calcule en temps réel le reliquat budgétaire annuel disponible pour chaque famille : en cas de dépassement, la part assurance est automatiquement écrêtée pour préserver l'équilibre financier de l'IPM.

### Liquidations & Télétransmission

- Génération des bordereaux officiels de télétransmission en PDF paysage certifié.
- Export des états de paiement pour rapprochement bancaire (CSV / Excel).
- Marquage sécurisé des paiements acquittés avec numéro de virement ou chèque.

---

## Assuré (Patient)

### Premier accès

À la première connexion, complétez votre profil (nom, prénom, date de naissance, téléphone, adresse) : cela crée votre fiche d'assuré **principal** et votre numéro de carte de prise en charge (généré automatiquement).

Le tableau de bord affiche votre carte dématérialisée, votre reliquat budgétaire annuel, vos ayants droit, vos ordonnances et vos prochains rendez-vous.

### Carte de prise en charge dématérialisée

- Format physique standard ISO 7810 ID-1 avec micro-puce dorée et QR Code dynamique vectoriel SVG.
- Présentez votre carte directement sur votre smartphone lors de vos consultations et passages en pharmacie.

### Mes ayants droit

Ajoutez votre conjoint et vos enfants comme bénéficiaires de votre couverture : chacun reçoit son propre numéro de carte et hérite automatiquement de votre plan de couverture. **Un ayant droit n'a jamais de compte de connexion propre** — vous gérez tout pour lui depuis votre espace.

### Prestataires proches & Géolocalisation

Autorisez la géolocalisation de votre navigateur pour voir sur une carte interactive les structures partenaires les plus proches (Hôpitaux, Pharmacies, Cliniques), avec calcul d'itinéraire et temps de trajet estimé.

### Mes prises en charge & Demandes de remboursement

- Suivez l'état de vos demandes de prise en charge (*En attente*, *Validée*, *Refusée*, *Terminée*).
- Déposez vos demandes de remboursement direct avec justificatifs et devis numérisés.
- Suivez en temps réel la part prise en charge et la part patient restant à votre charge.

---

## Médecin Traitant

### Agenda & Dossiers Patients

- Visualisation claire des consultations prévues de la journée, avec filtres par statut (*À venir*, *Terminé*, *Annulé*).
- Fiches dossiers patients (DPI) reprenant l'historique complet des consultations et ordonnances émises.

### Enregistrer une consultation

Sélectionnez le patient, renseignez les motifs, le diagnostic et le protocole thérapeutique. Si une prise en charge validée est rattachée, la part assurance et le reste à charge patient sont calculés automatiquement sans saisie manuelle de calcul.

### Ordonnances sécurisées infalsifiables

- Génération automatique de l'ordonnance médicale au format A4 certifié.
- Tampon officiel SantéSN avec **sceau d'intégrité cryptographique HMAC** et **QR Code de délivrance**.
- Le patient retrouve instantanément son ordonnance dans son espace personnel ou via son compte WhatsApp.

---

## Pharmacien d'Officine

### Scanner d'ordonnance par caméra

- Reconnaissance optique ultra-rapide par webcam ou caméra mobile (`jsQR@1.4.0`).
- Mode de saisie manuelle sécurisée en cas d'écran endommagé ou d'impression altérée.

### Validation atomique anti-double délivrance

- Contrôle transactionnel en base de données : une ordonnance délivrée est verrouillée immédiatement.
- Toute tentative de seconde présentation est instantanément bloquée avec alerte d'antériorité.
- Historique complet et exportable des médicaments remis au comptoir.

---

## Passerelle WhatsApp & Notifications

> 💡 **Documentation technique détaillée :** Retrouvez l'architecture complète de la passerelle WhatsApp sur [Mintlify — Notifications WhatsApp](https://documentation-santesn.mintlify.app/docs/fonctionnalites/notifications-whatsapp).

La plateforme SantéSN intègre une passerelle bidirectionnelle avec l'API **Meta Cloud API (WhatsApp Business)** :

1. **Alertes automatiques :**
   - Notification instantanée de l'assuré dès qu'une prise en charge est validée par l'IPM.
   - Envoi du lien sécurisé de consultation d'ordonnance après une visite chez le médecin.
   - Rappels de rendez-vous médicaux pour limiter le taux de non-présentation (*no-show*).
2. **Assistant conversationnel WhatsApp :**
   - Les assurés peuvent envoyer un message au numéro officiel pour consulter leur numéro de carte, le solde de leur plafond annuel restant ou trouver la pharmacie de garde conventionnée la plus proche.
3. **Sécurité & Webhook :**
   - Webhook d'écoute sécurisé avec vérification cryptographique de la signature `X-Hub-Signature-256`.
   - Politique *Fail-Closed* : rejet automatique des requêtes non signées ou non authentifiées.

---

## Questions fréquentes

**J'ai oublié mon mot de passe, comment le récupérer ?**  
Contactez votre administrateur ou gestionnaire d'organisme depuis *Gestion des utilisateurs* — un mot de passe temporaire vous sera attribué, à changer ensuite depuis le menu *Mot de passe*.

**Je suis assuré, puis-je créer un compte pour mon conjoint ou mon enfant ?**  
Non, et ce n'est pas nécessaire : ajoutez-les comme *ayants droit* depuis votre espace, ils sont automatiquement couverts sous votre plan de couverture.

**Une prise en charge en attente couvre-t-elle déjà mes consultations ?**  
Non. Tant qu'elle n'est pas au statut *validée*, vous réglez 100 % du montant de la consultation ; le tiers payant ne s'applique qu'après validation formelle de l'IPM.

**Comment les données médicales sont-elles protégées ?**  
Conformément à la Loi 2008-12 sur la protection des données personnelles (CDP Sénégal), les dossiers médicaux ne sont accessibles qu'au médecin traitant et au patient. Ni l'administrateur technique ni le gestionnaire financier n'ont accès aux diagnostics confidentiels.
