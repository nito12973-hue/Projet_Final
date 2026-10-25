# INTRODUCTION GÉNÉRALE

---

## 1. Contexte général du projet

Le système de santé au Sénégal traverse une phase charnière de son histoire, caractérisée par la volonté affirmée de l'État et des partenaires sociaux de garantir une protection sociale équitable, pérenne et accessible à toutes les couches de la population. Au cœur de ce dispositif de couverture du secteur formel et parapublic se trouvent les **Institutions de Prévoyance Maladie (IPM)**, régies par la loi n° 75-50 du 3 avril 1975 et ses décrets d'application. Ces structures paritaires, financées conjointement par les cotisations des employeurs et des salariés, ont pour mission fondamentale de solvabiliser les dépenses médicales des travailleurs et de leurs ayants droit (conjoints et enfants) à travers le mécanisme du **tiers payant**.

Le tiers payant constitue une avancée sociale majeure : il permet à l'assuré souffrant de consulter un médecin, de subir des examens de biologie médicale ou de retirer des médicaments d'urgence en pharmacie sans avoir à avancer la totalité des frais médicaux. L'assuré ne s'acquitte immédiatement que de sa « quote-part » (souvent comprise entre 10 % et 30 % selon le plan d'assurance), tandis que l'établissement de santé conventionné (hôpital, clinique, officine pharmaceutique) se fait rembourser directement la part restante par l'IPM ou la mutuelle émettrice.

Cependant, alors que les technologies numériques (téléphonie mobile, Internet haut débit, monnaie électronique avec Wave et Orange Money) ont profondément transformé le quotidien des citoyens sénégalais et le commerce local, la gestion quotidienne du tiers payant est restée, dans son écrasante majorité, **ancrée dans des processus archaïques sur support papier**. Entre le bon de prise en charge physique délivré au siège de l'entreprise, le carnet de santé cartonné de l'assuré, l'ordonnance manuscrite du praticien et la facture pro-forma envoyée en fin de mois pour paiement par chèque bancaire, la chaîne de transmission médicale souffre d'une rupture technologique critique.

C'est dans ce contexte socio-économique et technique que s'inscrit le présent projet de fin d'études mené au sein de l'**Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Traware de Diamniadio**, dans le département Technologies de l'Information et de la Communication (TIC), spécialité Analyste Programmeur Développeur (APD). Le projet **SantéSN** propose une refonte numérique complète, souveraine et inclusive de la relation tripartite Assuré – Prestataire de Santé – Organisme Gestionnaire.

---

## 2. Problématique

L'observation minutieuse des pratiques courantes dans les IPM et structures sanitaires de la région de Dakar et de l'intérieur du pays met en exergue des dysfonctionnements structurels qui compromettent la viabilité économique des régimes d'assurance et la qualité de la prise en charge des patients :

1. **La prolifération de la fraude et de l'usurpation d'identité :** 
   Les cartes d'assurés physiques (simples cartons plastifiés avec photo agrafée) ne disposent d'aucun mécanisme cryptographique d'authentification. Il est fréquent qu'un travailleur prête sa carte à un membre de sa famille élargie ou à un voisin non ayant droit. De même, la circulation de fausses ordonnances, d'ordonnances dupliquées ou de tampons médicaux falsifiés cause un préjudice financier chiffré à plusieurs centaines de millions de FCFA par an pour les IPM sénégalaises.

2. **La double délivrance et le manque de traçabilité en pharmacie :**
   Dans le schéma classique, une ordonnance papier délivrée pour un mois de traitement peut être photocopiée ou présentée successivement dans deux pharmacies différentes conventionnées avec la même IPM avant que les factures de fin de mois n'atteignent le gestionnaire. Lorsque l'IPM découvre l'anomalie 60 jours plus tard, les médicaments ont déjà été consommés et le litige financier s'avère insoluble.

3. **La complexité et la lenteur des circuits d'approbation :**
   Pour les actes médicaux spécialisés, les hospitalisations ou les scanners, le patient ou son parent doit physiquement se déplacer au siège de l'IPM pour faire viser un « bon de prise en charge » par le médecin-conseil. En cas d'urgence la nuit ou durant les week-ends, ce goulet d'étranglement bureaucratique retarde des soins critiques.

4. **Le dépassement incontrôlé des plafonds annuels de couverture :**
   Les IPM fixent contractuellement un plafond annuel maximal de remboursement par famille (par exemple 1 500 000 FCFA par an). Faute d'un système informatique centralisé en temps réel, un assuré peut atteindre son plafond dès le mois de juin et continuer à bénéficier indûment du tiers payant jusqu'en décembre sans que les pharmaciens ou médecins ne soient alertés.

5. **Les délais de paiement exorbitants pour les prestataires :**
   Les officines et cliniques doivent constituer manuellement des liasses volumineuses de bordereaux physiques, trier les bons par IPM, les déposer physiquement et attendre entre trois et six mois le règlement des factures, provoquant de sévères tensions de trésorerie pour les officines de santé.

Face à ce constat alarmant, la question centrale qui guide notre démarche de recherche et de développement est la suivante :

> **« Comment concevoir et déployer une plateforme logicielle intégrée, hautement disponible et sécurisée, capable d'automatiser en temps réel le tiers payant médical, d'éradiquer la fraude documentaire et d'assurer une traçabilité totale entre assurés, soignants et gestionnaires d'IPM au Sénégal, tout en respectant les contraintes strictes de confidentialité des données de santé et les spécificités de connectivité locale ? »**

---

## 3. Objectif général et objectifs spécifiques

### 3.1. Objectif général
L'objectif fondamental de ce projet de fin de formation consiste à concevoir, modéliser, réaliser et valider une solution numérique complète baptisée **SantéSN**. Cette plateforme web et mobile (PWA) vise à dématérialiser intégralement les processus d'affiliation, de consultation médicale, d'émission d'ordonnances sécurisées, de délivrance officinale et de liquidation comptable au sein des organismes d'assurance maladie du Sénégal.

### 3.2. Objectifs spécifiques
Pour atteindre cet objectif général, le projet se décline en plusieurs objectifs opérationnels précis :

1. **Dématérialiser l'identification de l'assuré :** Concevoir une carte d'assuré numérique au format international ISO 7810 ID-1, intégrant une puce virtuelle et un **QR Code dynamique vectoriel** infalsifiable permettant l'authentification instantanée du patient et de ses ayants droit.
2. **Sécuriser la prescription et interdire la fraude d'ordonnance :** Mettre en place un module de consultation médicale permettant au médecin traitant d'émettre des ordonnances électroniques munies d'un **tampon officiel numérique et d'un sceau d'intégrité cryptographique HMAC-SHA256**.
3. **Automatiser le contrôle de délivrance en pharmacie :** Développer un scanner optique par caméra directement intégré au navigateur pour lire le QR Code de l'ordonnance, vérifier son authenticité en direct et réaliser une **validation transactionnelle atomique (ACID)** empêchant toute double délivrance sur le territoire national.
4. **Calculer dynamiquement le tiers payant et le reste à charge :** Implémenter un moteur de tarification calculant en temps réel la quote-part de l'assuré et la part prise en charge par l'IPM, avec gestion automatique de **l'écrêtement budgétaire** dès lors que le plafond annuel familial est approché ou dépassé.
5. **Fluidifier les remboursements hors réseau :** Développer un portail libre-service permettant aux assurés de soumettre leurs reçus numérisés lorsqu'ils consultent une structure non conventionnée, et aux gestionnaires d'instruire ces dossiers et d'émettre des règlements instantanés (par virement bancaire ou mobile money Wave/Orange Money).
6. **Cartographier le réseau sanitaire sénégalais :** Intégrer un système d'information géographique (SIG / Leaflet) interactif permettant à l'assuré de repérer les cliniques, hôpitaux et pharmacies conventionnés les plus proches de sa position avec guidage routier.
7. **Assurer la conformité légale et la résilience hors-ligne :** Garantir une conformité exemplaire avec les exigences de la **Loi sénégalaise n° 2008-12 sur la protection des données personnelles (CDP)** et implémenter un cache applicatif PWA (Service Worker) permettant aux assurés de présenter leur carte même en cas de panne de connexion Internet.

---

## 4. Méthodologie adoptée

Pour mener à bien ce projet d'envergure dans les délais impartis, nous avons adopté une **démarche Agile inspirée du cadre Scrum**, combinée aux standards de modélisation du **Génie Logiciel (UML)** :

* **Phase de cadrage et immersion terrain :** Collecte des besoins réels auprès d'IPM sénégalaises, analyse documentaire des grilles de cotation d'actes et identification des cas d'usage nominaux et d'exception.
* **Phase d'analyse et modélisation formelle :** Élaboration des diagrammes de cas d'utilisation, des diagrammes d'activités, des diagrammes de séquence et du Modèle Conceptuel de Données (MCD) à l'aide d'UML.
* **Phase de développement itératif par sprints :**
  * *Sprint 1 :* Socle architectural, gestion multi-organismes hermétique (Multi-Tenant) et système d'authentification RBAC (5 rôles).
  * *Sprint 2 :* Gestion des assurés, cartes dématérialisées ISO 7810, ayants droit et algorithmes de plafonnement.
  * *Sprint 3 :* Espace médical, dossier patient, prescriptions et génération PDF certifiée avec sceau HMAC.
  * *Sprint 4 :* Espace pharmacien, scanner optique caméra `jsQR`, délivrance atomique et calcul du tiers payant.
  * *Sprint 5 :* Conventions tarifaires, géolocalisation Leaflet, télétransmission des bordereaux et remboursements hors réseau.
  * *Sprint 6 :* Mode hors-ligne PWA, durcissement de la sécurité, tests automatisés exhaustifs et déploiement continu Cloud (CI/CD).
* **Phase de validation et d'assurance qualité :** Conception et exécution d'un banc de **196 tests automatisés** (tests unitaires, tests de non-régression, tests de permissions transversales IDOR et tests d'intégrité de bout en bout).

---

## 5. Annonce du plan

Le présent rapport s'articule autour de quatre chapitres complémentaires :

* **Le Chapitre 1 (Présentation du cadre du projet)** expose l'environnement institutionnel de l'ISEP de Diamniadio, la genèse de l'initiative SantéSN, le périmètre d'action ainsi que la structure organisationnelle de l'équipe de développement.
* **Le Chapitre 2 (Analyse de l’existant et cadrage)** dresse un état des lieux critique des processus traditionnels de prise en charge au Sénégal, explicite le cahier des charges fonctionnel et technique, étudie les solutions alternatives et présente la planification détaillée du projet.
* **Le Chapitre 3 (Conception de la solution)** détaille les choix architecturaux (patron MVT, API REST, base de données relationnelle), présente la modélisation UML détaillée (cas d'utilisation, séquences transactionnelles, diagramme de classes) et justifie la pile technologique retenue.
* **Le Chapitre 4 (Réalisation, tests et résultats)** illustre concrètement la mise en œuvre de la plateforme à travers ses interfaces utilisateurs majeures, expose les résultats de la stratégie de tests automatisés, évalue les coûts d'exploitation et analyse les défis techniques rencontrés ainsi que les solutions apportées.

Une **conclusion générale** fera le bilan des résultats obtenus au regard des objectifs initiaux et dégagera les perspectives futures d'extension du système à l'échelle de la Couverture Maladie Universelle (CMU) du Sénégal.
