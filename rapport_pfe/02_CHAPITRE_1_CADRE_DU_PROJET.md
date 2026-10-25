# CHAPITRE 1 : PRÉSENTATION DU CADRE DU PROJET

---

## 1.1. Présentation de la structure d’accueil ou du commanditaire

### 1.1.1. L'Institut Supérieur d'Enseignement Professionnel (ISEP) de Diamniadio
Créé dans le cadre de la mise en œuvre de la concertation nationale sur l'avenir de l'enseignement supérieur (CNAES) et de la loi n° 2015-05 du 23 avril 2015, l'**Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Traware de Diamniadio** est un établissement public d'enseignement supérieur professionnel à vocation professionnalisante. Situé au cœur du pôle urbain émergent de Diamniadio, carrefour stratégique d'innovation industrielle et technologique du Sénégal, l'ISEP a pour mission fondamentale de former des techniciens supérieurs hautement qualifiés et immédiatement opérationnels, capables de répondre avec acuité aux exigences du marché de l'emploi et aux enjeux de développement socio-économique national.

L'institut propose des formations professionnelles diplômantes sanctionnées par le **Diplôme de l'Institut Supérieur d'Enseignement Professionnel (DISEP)**, d'un niveau équivalent au Baccalauréat plus deux années d'études supérieures spécialisées (Bac+2 / Niveau 3 du cadre national des certifications).

### 1.1.2. Le Département TIC et la filière Analyste Programmeur Développeur (APD)
Au sein de l'ISEP Diamniadio, le département **Technologies de l'Information et de la Communication (TIC)** occupe une place centrale. Il forme les futurs acteurs de la souveraineté numérique sénégalaise à travers des programmes axés sur la pratique intensive, les ateliers de codage en situation réelle et l'approche par compétences (APC).

La filière **Analyste Programmeur Développeur (APD)** forme des professionnels de l'ingénierie logicielle capables de :
* Analyser rigoureusement les besoins fonctionnels et métiers d'organisations complexes ;
* Concevoir des architectures logicielles pérennes, modulaires et évolutives selon les standards du génie logiciel ;
* Modéliser des bases de données relationnelles conformes aux formes normales et en assurer l'optimisation ;
* Maîtriser les paradigmes modernes de programmation web, mobile et backend (Python, JavaScript, bases de données SQL, cadriciels modernes) ;
* Intégrer les exigences de cybersécurité dès la conception (*Security by Design*) et respecter les réglementations nationales sur les données numériques.

Le **Projet de Fin de Formation (PFF)** représente l'aboutissement de ce cursus d'excellence. Il met les apprenants en situation d'ingénieurs juniors chargés de résoudre une problématique sociétale ou industrielle réelle en livrant une solution logicielle testée, documentée et prête à être mise en exploitation.

---

## 1.2. Présentation du projet : origine, bénéficiaires, périmètre

### 1.2.1. Origine et genèse de SantéSN
L'initiative **SantéSN** est née d'un constat empirique partagé lors de nos interactions avec le secteur de la santé au Sénégal. De nombreuses familles de travailleurs affiliés à des Institutions de Prévoyance Maladie (IPM d'entreprises, IPM corporatistes comme celle de la Sonatel, de la Senelec, de la CSS ou de banques de la place) se heurtent quotidiennement à des blocages administratifs lors de leurs parcours de soins.

En 2024, alors que le Sénégal accélère son programme de transformation numérique « Sénégal Digital 2025 » et que le Ministère de la Santé et de l'Action Sociale promeut l'informatisation des structures sanitaires, la couverture maladie d'entreprise demeure enclavée dans un modèle papier :
* Les bons de consultation doivent être retirés aux heures d'ouverture des bureaux administratifs, pénalisant les urgences nocturnes ;
* Les ordonnances papier sont sujettes à des pertes, des ratures, ou des contrefaçons ;
* Les pharmaciens et cliniciens expriment leur exaspération face aux rejets de factures tardifs lors des liquidations comptables trimestrielles des IPM.

Face à cette rupture d'efficacité, l'idée de SantéSN a émergé comme un projet fédérateur : **bâtir une plateforme unifiée capable d'offrir une expérience numérique de niveau bancaire à la santé publique sénégalaise**.

### 1.2.2. Bénéficiaires du projet
Le projet SantéSN répond aux besoins de quatre grandes catégories de bénéficiaires :

1. **Les Assurés et leurs Ayants Droit (Patients) :**
   * *Bénéfice :* Suppression des déplacements physiques pour obtenir un bon de prise en charge ; accès instantané à une carte dématérialisée avec QR Code sur smartphone ; transparence totale sur la consommation du plafond annuel de la famille ; notification instantanée de chaque acte médical par SMS / WhatsApp.
2. **Les Prestataires de Santé (Médecins, Pharmaciens, Cliniques, Hôpitaux) :**
   * *Bénéfice :* Garantie immédiate de solvabilité de l'assuré avant administration des soins ; éradication des contestations de factures ; télétransmission instantanée des feuilles de soins électroniques ; raccourcissement drastique des délais de règlement financier.
3. **Les Institutions de Prévoyance Maladie (IPM) et Mutuelles de Santé :**
   * *Bénéfice :* Suppression intégrale des coûts d'impression des carnets papier et formulaires autocopiants ; détection proactive de la fraude en amont ; contrôle en temps réel des engagements budgétaires ; automatisation de la liquidation et des statistiques épidémiologiques.
4. **L'État et les Autorités Sanitaires (SEN-CSU, Ministère de la Santé) :**
   * *Bénéfice :* Disponibilité d'un modèle d'interopérabilité souverain réplicable pour la Couverture Sanitaire Universelle ; collecte de données fiables pour le pilotage sanitaire national.

### 1.2.3. Périmètre fonctionnel et limites du système
Afin de préserver la faisabilité technique et la haute qualité de finition dans le calendrier imparti pour le PFF, le périmètre a été scrupuleusement circonscrit :

```
                                 PÉRIMÈTRE DE SANTÉSN
  ┌───────────────────────────────────────────────────────────────────────────────────┐
  │                                                                                   │
  │   [ INCLUS DANS LE PROJET ]                                                       │
  │   ─────────────────────────                                                       │
  │   1. Gestion Multi-Tenant hermétique (IPM SantéSN, IPM Sonatel, mutuelles)        │
  │   2. Carte dématérialisée ISO 7810 ID-1 avec QR Code dynamique vectoriel          │
  │   3. Espace Médecin : prescription électronique avec sceau HMAC-SHA256            │
  │   4. Espace Pharmacien : scanner optique caméra et validation atomique anti-fraude │
  │   5. Espace Gestionnaire : paramétrage de conventions, liquidations & remboursements│
  │   6. Système d'Information Géographique (SIG / Leaflet) avec tuiles Google/Esri   │
  │   7. Application Web Progressive (PWA) avec Service Worker et cache hors-ligne    │
  │   8. Passerelle WhatsApp Cloud API pour alertes instantanées                      │
  │                                                                                   │
  │   [ EXCLUS DU PÉRIMÈTRE ACTUEL (PERSPECTIVES) ]                                   │
  │   ─────────────────────────────────────────────                                   │
  │   1. Télémédecine / Vidéoconsultation en direct                                   │
  │   2. Connexion directe aux automates de laboratoire d'analyses                    │
  │   3. Gestion complète de la paie des entreprises affiliées                        │
  │                                                                                   │
  └───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.3. Organisation du groupe : rôles et outils de travail collaboratif

### 1.3.1. Répartition des rôles et responsabilités
Pour maximiser l'efficacité du travail et reproduire fidèlement les conditions d'un département de développement logiciel en entreprise, les responsabilités ont été articulées selon une organisation matricielle claire :

* **Responsable Architecture & Backend (Lead Développeur Django) :**
  * Modélisation de la base de données relationnelle (modèles Django, migrations, intégrité référentielle) ;
  * Implémentation de la logique métier critique (calcul de quote-part, détection des dépassements de plafonds, transactions atomiques ACID) ;
  * Sécurité backend, contrôle d'accès basé sur les rôles (RBAC) et chiffrement HMAC des ordonnances.
* **Responsable Frontend & Expérience Utilisateur (Développeur Web / PWA) :**
  * Conception des interfaces utilisateur réactives (UI / UX sans dépendance lourde, CSS moderne basé sur des variables de design tokens) ;
  * Intégration de la cartographie Leaflet et gestion dynamique des modes sombre et clair ;
  * Implémentation du scanner optique caméra en JavaScript pur (`jsQR`) et configuration du Service Worker PWA pour le mode hors-ligne.
* **Responsable Assurance Qualité, DevOps & Documentation :**
  * Écriture et maintenance de la suite de tests automatisés (196 tests unitaires et fonctionnels) ;
  * Configuration du pipeline d'intégration continue GitHub Actions et des environnements de déploiement Cloud (Vercel, Neon PostgreSQL) ;
  * Veille réglementaire sur la conformité de la Commission de Protection des Données Personnelles (CDP) et rédaction du présent mémoire.

### 1.3.2. Méthode de travail et rituels agiles
Le projet a été rythmé par la méthodologie **Scrum**, articulée en sprints de deux semaines :
* **Sprint Planning :** Définition des objectifs du sprint et sélection des récits utilisateurs (*User Stories*) prioritaires dans le backlog produit ;
* **Points de synchronisation réguliers :** Échanges courts pour identifier les blocages techniques (notamment sur l'optimisation des requêtes SQL et la compatibilité des navigateurs mobiles pour la caméra) ;
* **Sprint Review & Rétrospective :** Démonstration des fonctionnalités développées sur l'environnement de pré-production et ajustement des priorités du sprint suivant.

### 1.3.3. Outils de travail collaboratif et chaîne logicielle
L'ensemble des activités de développement et de gestion de projet s'est appuyé sur une suite d'outils professionnels modernes :

| Outil / Plateforme | Usage et Rôle dans le Projet |
| :--- | :--- |
| **GitHub** | Dépôt central de code source Git, gestion des versions, revues de code (*Pull Requests*) et traçabilité des commits. |
| **GitHub Actions** | Serveur d'intégration continue (CI) automatisant l'exécution des tests Django à chaque push sur la branche `main`. |
| **Visual Studio Code / Antigravity IDE** | Environnement de développement intégré (IDE), débogage pas à pas, extensions Python et SQL. |
| **Trello / GitHub Projects** | Tableau Kanban de suivi des tâches découpées en *À faire*, *En cours*, *En revue* et *Terminé*. |
| **Discord & WhatsApp** | Canaux de communication instantanée de l'équipe pour les alertes de build et l'échange rapide d'informations. |
| **Vercel PaaS & Neon Cloud DB** | Plateformes d'hébergement serveur et base de données PostgreSQL serverless en haute disponibilité. |
| **Draw.io / PlantUML** | Outils de conception graphique et d'ingénierie logicielle pour la modélisation des diagrammes UML. |
