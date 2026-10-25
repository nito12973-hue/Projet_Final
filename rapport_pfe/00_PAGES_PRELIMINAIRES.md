# PAGES PRÉLIMINAIRES

---

## PAGE DE GARDE OFFICIELLE

```
                       RÉPUBLIQUE DU SÉNÉGAL
                    Un Peuple – Un But – Une Foi
    MINISTÈRE DE L’ENSEIGNEMENT SUPÉRIEUR, DE LA RECHERCHE ET DE L’INNOVATION
    
       INSTITUT SUPÉRIEUR D’ENSEIGNEMENT PROFESSIONNEL (ISEP)
                    AMADOU TRAWARE DE DIAMNIADIO

                       DÉPARTEMENT : TIC
         MÉTIER : ANALYSTE PROGRAMMEUR DÉVELOPPEUR (APD)
```

### RAPPORT DE PROJET DE FIN DE FORMATION
**En vue de l’obtention du Diplôme de l’ISEP (DISEP)**

---

### THÈME :
# « CONCEPTION ET RÉALISATION D’UNE PLATEFORME WEB ET MOBILE DE DÉMATÉRIALISATION DU TIERS PAYANT ET DE LA PRISE EN CHARGE MÉDICALE AU SÉNÉGAL : SANTÉSN »

---

**Présenté par :**
* **M. [Prénom NOM de l'Étudiant 1]** — Étudiant en APD
* *(Optionnel / Binôme) : M./Mme [Prénom NOM de l'Étudiant 2]*

**Sous l’encadrement de :**
* **M./Mme [Prénom NOM de l'Encadreur]**, Enseignant-Chercheur / Encadreur Pédagogique (ISEP Diamniadio)
* **M./Mme [Prénom NOM de l'Encadreur Professionnel]**, Encadreur Professionnel *(le cas échéant)*

```
                   Année académique : 2025 – 2026
```

---

## DÉDICACES

> *À mes chers parents, pour leurs sacrifices inestimables, leurs prières constantes et leur soutien indéfectible tout au long de mon parcours académique et personnel.*
> 
> *À mes frères, sœurs et proches, pour leur présence rassurante, leurs encouragements dans les moments de doute et leur foi inébranlable en ma réussite.*
> 
> *À mes camarades de promotion du département TIC / Métier APD de l’ISEP Diamniadio, avec qui j'ai partagé des nuits blanches de code, des résolutions de bugs mémorables et une solidarité fraternelle exemplaire.*
> 
> *À tous ceux qui luttent quotidiennement pour la modernisation du système sanitaire sénégalais et l'accès universel à des soins de qualité.*

---

## REMERCIEMENTS

Au terme de ce projet de fin de formation, nous tenons à exprimer notre profonde gratitude à toutes les personnes qui ont contribué, de près ou de loin, à l'aboutissement de ce travail :

* **À la Direction Générale et au corps professoral de l’ISEP Amadou Traware de Diamniadio**, pour la qualité de la formation professionnelle dispensée, l'environnement d'apprentissage stimulant et les valeurs de rigueur et d'éthique inculquées tout au long de notre cursus.
* **À notre encadreur pédagogique**, pour sa disponibilité, ses conseils méthodologiques avisés, son sens critique constructif et ses orientations techniques précieuses qui ont grandement enrichi ce mémoire.
* **À l'équipe pédagogique du département TIC (Filière Analyste Programmeur Développeur)**, pour nous avoir transmis les fondamentaux solides du génie logiciel, de l'architecture logicielle, de l'administration de bases de données et de la sécurité des systèmes d'information.
* **Aux professionnels de santé et gestionnaires d'Institutions de Prévoyance Maladie (IPM)** de Dakar et des régions que nous avons consultés lors de notre étude de l'existant, pour le temps accordé, la sincérité de leurs retours d'expérience et la précision des données terrain partagées.

---

## RÉSUMÉ

Au Sénégal, la gestion de la couverture maladie et du tiers payant par les Institutions de Prévoyance Maladie (IPM), les mutuelles de santé et les assurances d’entreprise repose encore largement sur des procédures manuelles et des supports papier (bons de prise en charge volants, lettres de garantie manuscrites, carnets physiques d'assurés et facturations différées). Cette organisation engendre des lenteurs administratives considérables, un risque aigu de fraude (cartes d’assurés prêtées à des tiers, falsification d'ordonnances, surfacturations), des délais d'attente pénibles pour les patients et un recouvrement comptable laborieux pour les prestataires de santé (pharmacies, cliniques, hôpitaux).

Le projet **SantéSN** apporte une réponse technologique innovante, robuste et inclusive à cette problématique nationale. Conçue comme une application web progressive (PWA) développée avec le cadriciel Django et adossée à une base de données cloud PostgreSQL (Neon), SantéSN dématérialise l'ensemble de la chaîne de valeur du tiers payant médical. La plateforme interconnecte en temps réel cinq profils d'utilisateurs distincts : l'Assuré (muni d'une carte digitale sécurisée par QR code dynamique ISO 7810 et d'une jauge de suivi du plafond annuel familial), le Médecin prescripteur (qui génère des ordonnances électroniques certifiées par sceau cryptographique HMAC anti-altération), le Pharmacien (qui valide les ordonnances via un scanner optique par caméra avec verrouillage atomique de délivrance), le Gestionnaire d'IPM (qui paramètre les conventions tarifaires, instruit les demandes de remboursement hors réseau et télétransmet les bordereaux comptables de liquidation) et l'Administrateur système (qui pilote la conformité réglementaire CDP et la supervision technique).

Intégrant un mode hors-ligne résilient (Service Worker), une cartographie interactive Leaflet géolocalisant les structures sanitaires partenaires du Sénégal et une passerelle de notification WhatsApp, SantéSN garantit une gouvernance médicale transparente, zéro-papier, conforme à la loi sénégalaise n° 2008-12 sur la protection des données à caractère personnel.

**Mots-clés :** SantéSN, Tiers Payant, IPM Sénégal, Django, PWA, Sécurité HMAC, Dématérialisation médicale, Conformité CDP.

---

## ABSTRACT

In Senegal, health insurance and third-party payment management across Health Insurance Institutions (IPMs), community-based mutual health schemes, and corporate insurers still relies heavily on manual workflows and physical paperwork (paper vouchers, handwritten guarantee letters, physical beneficiary booklets, and deferred billing). This legacy model leads to severe administrative bottlenecks, widespread fraud risks (insurance card lending, altered medical prescriptions, phantom billings), lengthy queues for patients, and cumbersome accounting reconciliations for healthcare providers (pharmacies, hospitals, clinics).

The **SantéSN** project provides a robust, state-of-the-art, and inclusive technological solution tailored to this sub-Saharan healthcare ecosystem. Built as a Progressive Web Application (PWA) powered by the Django framework and a high-availability cloud PostgreSQL database (Neon), SantéSN digitizes the complete healthcare coverage and third-party settlement lifecycle. The system seamlessly interconnects five distinct stakeholder roles: Insured Patients (featuring an ISO 7810-compliant digital card with dynamic anti-fraud QR codes and real-time family spending cap monitoring), Prescribing Physicians (generating digitally signed prescriptions backed by HMAC cryptographic integrity seals), Pharmacists (dispensing medications through a browser-based optical camera scanner with atomic database locking to prevent duplicate claims), IPM Managers (configuring fee schedules, settling out-of-network claims, and generating accounting liquidation summaries), and IT Administrators (overseeing audit logs and regulatory data privacy compliance).

With offline caching resilience, integrated interactive GIS mapping of Senegalese medical centers, and automated WhatsApp notifications, SantéSN establishes an auditable, paperless, and real-time healthcare ecosystem fully aligned with Senegalese Data Protection Law No. 2008-12.

**Keywords:** SantéSN, Third-Party Payment, Health Insurance, Senegal IPM, Django, PWA, HMAC Security, Medical Digitization.

---

## SOMMAIRE SYNTHÉTIQUE

* **Pages préliminaires**
* **Introduction générale**
* **Chapitre 1 : Présentation du cadre du projet**
* **Chapitre 2 : Analyse de l’existant et cadrage**
* **Chapitre 3 : Conception de la solution**
* **Chapitre 4 : Réalisation, tests et résultats**
* **Conclusion générale et perspectives**
* **Pages de fin (Bibliographie, Annexes, Table détaillée)**

---

## LISTE DES SIGLES ET ABRÉVIATIONS

| Sigle | Signification |
| :--- | :--- |
| **ACID** | Atomicité, Cohérence, Isolation, Durabilité *(Propriétés de transactions SQL)* |
| **API** | Interface de Programmation d'Application *(Application Programming Interface)* |
| **APD** | Analyste Programmeur Développeur *(Filière ISEP)* |
| **CDP** | Commission de Protection des Données Personnelles *(Sénégal, Loi 2008-12)* |
| **CMU** | Couverture Maladie Universelle *(Agence Nationale SEN-CSU)* |
| **CRUD** | Création, Lecture, Mise à jour, Suppression *(Create, Read, Update, Delete)* |
| **CSRF** | Falsification de requête intersites *(Cross-Site Request Forgery)* |
| **CSS** | Feuilles de style en cascade *(Cascading Style Sheets)* |
| **DISEP** | Diplôme de l’Institut Supérieur d’Enseignement Professionnel |
| **GPS** | Système de positionnement global *(Global Positioning System)* |
| **HMAC** | Code d’authentification de message basé sur le hachage *(Hash-based MAC)* |
| **HTML** | Langage de balisage d'hypertexte *(HyperText Markup Language)* |
| **IDOR** | Référence directe non sécurisée à un objet *(Insecure Direct Object Reference)* |
| **IPM** | Institution de Prévoyance Maladie *(Sénégal)* |
| **ISEP** | Institut Supérieur d’Enseignement Professionnel |
| **ISO** | Organisation internationale de normalisation *(International Organization for Standardization)* |
| **JWT** | Jeton Web JSON *(JSON Web Token)* |
| **MCD** | Modèle Conceptuel de Données |
| **MLD** | Modèle Logique de Données |
| **MVC / MVT** | Modèle-Vue-Contrôleur / Modèle-Vue-Template *(Architecture logicielle Django)* |
| **ORM** | Mapping Objet-Relationnel *(Object-Relational Mapping)* |
| **OSM** | OpenStreetMap *(Données cartographiques ouvertes)* |
| **PDF** | Format de document portable *(Portable Document Format)* |
| **PWA** | Application Web Progressive *(Progressive Web App)* |
| **QR Code** | Code à réponse rapide *(Quick Response Code)* |
| **RBAC** | Contrôle d'accès basé sur les rôles *(Role-Based Access Control)* |
| **REST** | Transfert d'état représentationnel *(Representational State Transfer)* |
| **SaaS** | Logiciel en tant que service *(Software as a Service)* |
| **SEN-CSU** | Agence Sénégalaise de la Couverture Sanitaire Universelle |
| **SQL** | Langage de requête structurée *(Structured Query Language)* |
| **SSL / TLS** | Sécurité de la couche de transport *(Transport Layer Security)* |
| **TIC** | Technologies de l’Information et de la Communication |
| **UML** | Langage de modélisation unifié *(Unified Modeling Language)* |
| **UX / UI** | Expérience Utilisateur / Interface Utilisateur *(User Experience / User Interface)* |
| **VCF** | Fichier de contact virtuel *(Virtual Contact File)* |
| **WSGI** | Interface de passerelle pour serveur Web *(Web Server Gateway Interface)* |

---

## LISTE DES FIGURES

* **Figure 1 :** Schéma du circuit papier traditionnel de prise en charge médicale au Sénégal
* **Figure 2 :** Cartographie des acteurs et parties prenantes du système de santé sénégalais
* **Figure 3 :** Diagramme de cas d'utilisation global de la plateforme SantéSN
* **Figure 4 :** Diagramme de séquence de délivrance d'ordonnance en pharmacie avec verrouillage atomique
* **Figure 5 :** Diagramme de séquence d'instruction et de remboursement d'une dépense hors réseau
* **Figure 6 :** Architecture logicielle MVT (Modèle-Vue-Template) et déploiement Cloud de SantéSN
* **Figure 7 :** Modèle Conceptuel de Données (MCD) relationnel de SantéSN
* **Figure 8 :** Schéma d'isolation étanche multi-organismes (Multi-Tenant Scoped QuerySet)
* **Figure 9 :** Interface de connexion sécurisée et formulaire avec limitation des tentatives
* **Figure 10 :** Tableau de bord interactif du Gestionnaire d'IPM (indicateurs financiers et files d'attente)
* **Figure 11 :** Carte sanitaire géolocalisée et sélecteur de calques dynamique (Plan & Satellite HD)
* **Figure 12 :** Fiche de consultation et outil de prescription d'ordonnance médicale certifiée
* **Figure 13 :** Scanner optique par caméra de la pharmacie et validation instantanée de la prise en charge
* **Figure 14 :** Carte dématérialisée de l'assuré (format physique ISO 7810 avec QR Code et jauge de plafond)
* **Figure 15 :** Écran de consultation des droits hors-ligne via le Service Worker PWA
* **Figure 16 :** Rapport d'exécution automatisée des 196 tests unitaires et d'intégration

---

## LISTE DES TABLEAUX

* **Tableau 1 :** Matrice d'analyse SWOT du circuit de prise en charge médicale existant au Sénégal
* **Tableau 2 :** Matrice de comparaison des solutions logicielles du marché face aux besoins locaux
* **Tableau 3 :** Grille d'évaluation des besoins fonctionnels par rôle utilisateur
* **Tableau 4 :** Spécifications des exigences non-fonctionnelles et contraintes de sécurité
* **Tableau 5 :** Planning prévisionnel et chronogramme de réalisation (itérations Agile / Scrum)
* **Tableau 6 :** Dictionnaire de données des entités fondamentales de la base relationnelle SantéSN
* **Tableau 7 :** Matrice de contrôle d'accès basée sur les rôles (Matrice RBAC)
* **Tableau 8 :** Tableau récapitulatif des technologies et outils retenus
* **Tableau 9 :** Synthèse du plan de tests et couverture de validation logicielle
* **Tableau 10 :** Évaluation financière et budget estimatif d'exploitation annuelle (Cloud, domaine, maintenance)
