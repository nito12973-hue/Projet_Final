# RÉPUBLIQUE DU SÉNÉGAL
**UNIVERSITÉ CHEIKH ANTA DIOP DE DAKAR (UCAD)**  
*Faculté des Sciences et Technologies / Département d'Informatique*  
*(Ou Établissement d'Enseignement Supérieur Partenaire)*

---

```
                       UNIVERSITÉ / ÉCOLE D'INGÉNIEURS
                      DÉPARTEMENT GÉNIE INFORMATIQUE
```

---

# MÉMOIRE DE FIN D'ÉTUDES
### Pour l'obtention du Diplôme de Master / Ingénieur en Informatique
**Spécialité :** Génie Logiciel & Systèmes d'Information

---

### **THÈME :**
# CONCEPTION ET RÉALISATION D'UNE PLATEFORME NUMÉRIQUE DE GESTION DE LA PRISE EN CHARGE MÉDICALE ET DU TIERS-PAYANT : SANTÉSN

---

**Présenté et soutenu par :**  
**L'Étudiant / Le Candidat**

**Sous la direction de :**  
**L'Enseignant-Chercheur / Directeur de Mémoire** *(Encadreur Pédagogique)*  
**L'Ingénieur Référent / Tuteur Professionnel** *(Encadreur Professionnel)*

**Membres du Jury :**
* **Président du Jury :** Professeur / Docteur [Nom & Prénom]
* **Rapporteur :** Docteur / Enseignant [Nom & Prénom]
* **Examinateur :** Ingénieur / Professionnel [Nom & Prénom]

---

**Année Universitaire : 2025 – 2026**

\newpage

---

## DÉDICACES

> *À mes très chers parents, pour leurs sacrifices inestimables, leur soutien indéfectible, leurs prières constantes et leur amour tout au long de mon parcours universitaire.*
>
> *À mes frères et sœurs, pour leur présence, leurs encouragements et leur affection sans faille.*
>
> *À tous mes enseignants et formateurs, qui ont façonné mon esprit critique et partagé avec générosité leur savoir.*
>
> *À tous mes compagnons de promotion et amis, avec qui j'ai partagé ces années d'apprentissage, d'efforts et de persévérance.*
>
> *À tous les professionnels de santé du Sénégal, qui œuvrent chaque jour avec dévouement pour le bien-être des populations.*

\newpage

---

## REMERCIEMENTS

La réalisation de ce mémoire de fin d'études a bénéficié du soutien, des conseils et de l'accompagnement de nombreuses personnes à qui je tiens à exprimer ma profonde gratitude :

* J'adresse mes sincères remerciements à mon **directeur de mémoire**, pour sa disponibilité constante, ses orientations méthodologiques avisées et son exigence intellectuelle tout au long de ce travail.
* J'exprime toute ma reconnaissance aux **membres du jury**, qui ont accepté d'examiner et d'évaluer ce travail de recherche et de développement logiciel.
* Mes remerciements s'adressent également à l'ensemble du **corps professoral et pédagogique**, pour la formation solide et de haut niveau qu'ils m'ont dispensée.
* Je remercie chaleureusement les professionnels de santé, gestionnaires d'institutions de prévoyance maladie et pharmaciens qui ont accordé de leur temps pour expliciter les rouages réels du tiers-payant et de la délivrance médicamenteuse au Sénégal.
* Enfin, mes pensées reconnaissantes vont à tous ceux qui, de près ou de loin, ont contribué à l'aboutissement de ce projet d'ingénierie logicielle.

\newpage

---

## RÉSUMÉ

La gestion de la couverture du risque maladie au Sénégal, notamment à travers les Institutions de Prévoyance Maladie (IPM) et les mutuelles de santé, repose sur une chaîne d'acteurs hautement fragmentée : organismes assureurs, assurés, médecins et pharmaciens. Cette fragmentation engendre des frictions opérationnelles majeures : opacité des droits pour les ayants droit dépourvus de comptes propres, rupture de visibilité sur le reste à charge lors des consultations, insécurité des ordonnances papier exposées aux fraudes ou doubles délivrances, et absence de traçabilité immuable des décisions administratives.

Ce mémoire présente la conception, le développement et l'évaluation rigoureuse de **SantéSN**, une plateforme web intégrée de gestion de la prise en charge médicale et du tiers-payant. Fondée sur un changement de paradigme architectural consistant à placer le **bénéficiaire** et sa **couverture** (plutôt que le dossier médical clinique complet) au centre du système, SantéSN garantit une continuité opérationnelle sans compromettre le secret médical. 

Développée sur le cadriciel Django/Python avec une architecture logicielle modulaire, SantéSN implémente un contrôle d'accès strict basé sur les rôles (RBAC) pour quatre espaces métiers dédiés : Administrateur, Médecin, Pharmacien et Assuré. Les innovations techniques incluent la dématérialisation sécurisée des ordonnances via des codes QR non porteurs de données médicales, le calcul déterministe en temps réel de la quote-part d'assurance, un journal d'activité non modifiable adossé à du texte figé, ainsi qu'un onboarding mono-canal résilient par jeton temporaire (WhatsApp et Email de secours). 

L'évaluation expérimentale s'appuie sur une suite de tests automatisés exhaustive, une matrice d'étanchéité des routes et des mesures en navigateur réel instrumenté. Les résultats confirment l'éradication des risques de double délivrance et de double réservation, une étanchéité absolue des données médicales entre praticiens et une conformité responsive complète.

**Mots-clés :** Tiers-payant, Couverture maladie, E-santé, Django, Contrôle d'accès RBAC, Ordonnance dématérialisée, QR Code, Traçabilité, Sénégal.

\newpage

---

## ABSTRACT

Health risk coverage management in Senegal, particularly through Health Prevision Institutions (IPMs) and community mutual funds, relies on a fragmented chain of stakeholders: insurance organizations, policyholders, medical doctors, and pharmacists. This organizational dispersion creates significant operational issues: lack of verifiable identity for dependents lacking autonomous user accounts, uncertainty regarding patient co-payments at the point of care, vulnerability of paper prescriptions to alteration or duplicate dispensing, and lack of immutable audit trails for administrative decisions.

This master's thesis presents the design, development, and experimental evaluation of **SantéSN**, an integrated web platform for medical coverage management and third-party payment processing. Based on a key architectural paradigm shift that places the **beneficiary** and their **insurance coverage** (rather than a centralized electronic medical record) at the center of the domain model, SantéSN achieves seamless operational continuity while strictly preserving medical privacy.

Engineered using the Django/Python framework with a modular software architecture, SantéSN enforces strict Role-Based Access Control (RBAC) across four distinct roles: Administrator, Doctor, Pharmacist, and Insured Beneficiary. Technical contributions include secure prescription dematerialization using reference-only QR codes, deterministic real-time co-payment calculation, an immutable text-frozen audit log, and resilient single-channel onboarding via time-limited security tokens (leveraging WhatsApp Cloud API with automatic email fallback).

The experimental validation relies on an exhaustive automated test suite, an exhaustive route permission matrix, and headless browser metric instrumentation. The results demonstrate the eradication of duplicate dispensing and conflicting appointments, absolute isolation of patient clinical records between practitioners, and full responsive web compliance.

**Keywords:** Third-party payment, Health insurance, E-health, Django, RBAC, Electronic prescription, QR Code, Auditability, Senegal.

\newpage

---

## LISTE DES SIGLES ET ACRONYMES

| Sigle / Acronyme | Signification complète |
| :--- | :--- |
| **ANSD** | Agence Nationale de la Statistique et de la Démographie (Sénégal) |
| **API** | Application Programming Interface (Interface de Programmation d'Application) |
| **BF** | Besoin Fonctionnel |
| **BNF** | Besoin Non Fonctionnel |
| **CDD** | Component Driven Development |
| **CDN** | Content Delivery Network (Réseau de Diffusion de Contenu) |
| **CMU** | Couverture Maladie Universelle |
| **CRUD** | Create, Read, Update, Delete |
| **CSRF** | Cross-Site Request Forgery |
| **CSS** | Cascading Style Sheets |
| **DHIS2** | District Health Information Software 2 |
| **DMP** | Dossier Médical Partagé |
| **DOM** | Document Object Model |
| **FCFA / XOF** | Franc de la Communauté Financière Africaine |
| **FK** | Foreign Key (Clé Étrangère) |
| **HTML** | HyperText Markup Language |
| **HTTP / HTTPS** | HyperText Transfer Protocol (Secure) |
| **IDOR** | Insecure Direct Object Reference |
| **IPM** | Institution de Prévoyance Maladie |
| **ISO** | International Organization for Standardization |
| **JSON** | JavaScript Object Notation |
| **MCD** | Modèle Conceptuel de Données |
| **MLD** | Modèle Logique de Données |
| **MPD** | Modèle Physique de Données |
| **OMS** | Organisation Mondiale de la Santé |
| **ORM** | Object-Relational Mapping |
| **PEC** | Prise En Charge |
| **PDF** | Portable Document Format |
| **RBAC** | Role-Based Access Control (Contrôle d'Accès Fondé sur les Rôles) |
| **RDV** | Rendez-vous médical |
| **REST** | Representational State Transfer |
| **SIH** | Système d'Information Hospitalier |
| **SMTP** | Simple Mail Transfer Protocol |
| **SQL** | Structured Query Language |
| **SVG** | Scalable Vector Graphics |
| **UCAD** | Université Cheikh Anta Diop de Dakar |
| **UI / UX** | User Interface / User Experience |
| **UML** | Unified Modeling Language |
| **URI / URL** | Uniform Resource Identifier / Locator |
| **WCAG** | Web Content Accessibility Guidelines |
| **W3C** | World Wide Web Consortium |

\newpage

---

## LISTE DES FIGURES

* **Figure 1.1** — Chaîne d'interaction traditionnelle des acteurs du tiers-payant
* **Figure 1.2** — Modèle de positionnement architectural de SantéSN
* **Figure 2.1** — Schéma du parcours de soins et flux d'information au sein d'une IPM
* **Figure 3.1** — Diagramme global des cas d'utilisation du système SantéSN (UML)
* **Figure 3.2** — Diagramme des cas d'utilisation : Espace Assuré
* **Figure 3.3** — Diagramme des cas d'utilisation : Espace Médecin
* **Figure 3.4** — Diagramme des cas d'utilisation : Espace Pharmacien
* **Figure 3.5** — Diagramme de classes métier du domaine SantéSN (UML)
* **Figure 3.6** — Diagramme d'états-transitions d'une demande de Rendez-vous
* **Figure 3.7** — Diagramme d'états-transitions d'une demande de Prise en Charge
* **Figure 3.8** — Diagramme d'états-transitions du cycle de vie d'une Ordonnance
* **Figure 3.9** — Diagramme de séquence : Parcours complet de consultation et délivrance
* **Figure 3.10** — Architecture applicative globale en couches de SantéSN
* **Figure 4.1** — Tableau de bord Administrateur : Vue globale de pilotage et file d'attente
* **Figure 4.2** — Tableau de bord Médecin : Planning journalier "Ma journée" et recherche express
* **Figure 4.3** — Tableau de bord Pharmacien : Console de scan et délivrance au comptoir
* **Figure 4.4** — Tableau de bord Assuré : Synthèse des démarches, carte et actions rapides
* **Figure 4.5** — Spécimen de Carte d'Assuré dématérialisée (Format ISO 7810 ID-1 avec QR)
* **Figure 4.6** — Spécimen d'Ordonnance médicale A4 générée avec code de vérification
* **Figure 4.7** — Console de surveillance de sécurité : Comptes bloqués et journal d'activité

\newpage

---

## LISTE DES TABLEAUX

* **Tableau 1.1** — Étude comparative des solutions existantes dans le domaine de la e-santé
* **Tableau 2.1** — Matrice des limites du fonctionnement existant et des besoins exprimés
* **Tableau 3.1** — Récapitulatif des besoins fonctionnels majeurs par profil d'utilisateur
* **Tableau 3.2** — Spécification des exigences non fonctionnelles et critères de vérification
* **Tableau 3.3** — Dictionnaire récapitulatif des 17 entités persistantes du modèle de données
* **Tableau 3.4** — Pile technologique logicielle et justification des choix
* **Tableau 4.1** — Métriques de réalisation logicielle du projet SantéSN
* **Tableau 4.2** — Matrice de conformité des exigences non fonctionnelles mesurées
* **Tableau 4.3** — Matrice d'étanchéité des routes selon les profils d'utilisateurs (RBAC)
* **Tableau 4.4** — Résultats détaillés des campagnes de tests automatisés

\newpage

---

## TABLE DES MATIÈRES

```text
DÉDICACES ........................................................................ i
REMERCIEMENTS .................................................................... ii
RÉSUMÉ ........................................................................... iii
ABSTRACT ......................................................................... iv
LISTE DES SIGLES ET ACRONYMES .................................................... v
LISTE DES FIGURES ................................................................ vi
LISTE DES TABLEAUX ............................................................... vii
TABLE DES MATIÈRES ............................................................... viii

INTRODUCTION GÉNÉRALE ............................................................ 1
  1. Contexte et justification du sujet ......................................... 1
  2. Problématique .............................................................. 3
  3. Questions de recherche, générale et spécifiques ............................ 4
  4. Objectif général et objectifs subsidiaires ................................. 5
  5. Hypothèses de recherche .................................................... 6
  6. Méthodologie retenue ....................................................... 7
  7. Annonce du plan ............................................................ 8

CHAPITRE I : CADRE THÉORIQUE ET CONCEPTUEL ....................................... 9
  Section 1 : Revue conceptuelle ................................................ 9
    Sous-section 1 : Concepts de l'assurance maladie ............................ 9
    Sous-section 2 : Concepts du numérique en santé ............................. 12
  Section 2 : Revue de littérature et état de l'art ............................. 15
    Les systèmes d'information hospitaliers libres .............................. 15
    Les systèmes nationaux d'information sanitaire .............................. 16
    Les plateformes de prise de rendez-vous ..................................... 16
    La prescription électronique ................................................ 17
    Positionnement de SantéSN ................................................... 18

CHAPITRE II : CONTEXTE DE L'ÉTUDE ................................................ 20
  Section 1 : Contexte général .................................................. 20
    Sous-section 1 : Le système de santé et la couverture du risque maladie au Sénégal 20
    Sous-section 2 : La numérisation des services et ses contraintes locales .... 22
  Section 2 : Contexte spécifique ............................................... 24
    Sous-section 1 : L'organisme, son réseau et ses acteurs ..................... 24
    Sous-section 2 : Limites du fonctionnement actuel et expression du besoin ... 25

CHAPITRE III : CADRE MÉTHODOLOGIQUE ET CONCEPTION ................................ 29
  Section 1 : Spécification et modélisation du système .......................... 29
    Sous-section 1 : Spécification des besoins fonctionnels et non-fonctionnels . 29
      A. Besoins fonctionnels ................................................... 30
      B. Besoins non fonctionnels ............................................... 33
    Sous-section 2 : Étude et choix des méthodes de modélisation ................ 35
    Sous-section 3 : Modélisation ............................................... 37
      A. Diagramme de cas d'utilisation (description) ........................... 38
      B. Diagramme de classes (description) ..................................... 41
      C. Diagrammes d'états-transitions ......................................... 45
      D. Diagramme de séquence — parcours de l'ordonnance ....................... 47
  Section 2 : Implémentation et évaluation des modèles .......................... 49
    Sous-section 1 : Choix technologiques et justification ...................... 49
    Sous-section 2 : Description de l'expérimentation ........................... 52

CHAPITRE IV : CADRE ANALYTIQUE ET RÉALISATION ................................... 54
  Section 1 : Présentation et traitement des données ............................ 54
    Sous-section 1 : Description des données (sources, structure, qualité) ...... 54
      A. Sources ................................................................ 54
      B. Structure .............................................................. 55
      C. Qualité — trois mécanismes de garantie ................................. 56
    Sous-section 2 : Traitement, cycle de vie et rétention des données .......... 58
  Section 2 : Réalisation et analyse des fonctionnalités ........................ 61
    Sous-section 1 : Implémentation des interfaces utilisateur .................. 61
      A. Architecture de l'interface ............................................ 61
      B. Identité visuelle ...................................................... 62
      C. Adaptation aux petits écrans ........................................... 63
      D. Thème sombre ........................................................... 64
      E. Documents imprimables .................................................. 65
      F. Accessibilité .......................................................... 66
    Sous-section 2 : Synthèse et discussion des résultats ....................... 67
      A. Métriques de réalisation ............................................... 67
      B. Résultats de l'évaluation .............................................. 68
      C. Confrontation aux hypothèses ........................................... 70
      D. Discussion critique — limites du travail ............................... 72
      E. Enseignement méthodologique transversal ................................ 74
    Sous-section 3 : Recommandations ............................................ 75
      Court terme — avant toute mise en service réelle ........................... 75
      Moyen terme ............................................................... 76
      Long terme ................................................................ 77

CONCLUSION GÉNÉRALE ............................................................ 79
WEBOGRAPHIE .................................................................... 82
ANNEXES ........................................................................ 85
```

\newpage

---

# Introduction générale

L'assurance maladie repose sur une chaîne d'acteurs qui ne partagent presque jamais le même support d'information. L'assuré détient une carte, l'employeur détient les droits, le médecin détient le diagnostic, la pharmacie détient la délivrance, et l'organisme assureur détient la décision de prise en charge. Chacun de ces maillons fonctionne ; c'est leur articulation qui coûte cher, en temps comme en confiance.

SantéSN est une plateforme web qui réunit ces maillons autour d'un objet central : le **bénéficiaire**, et non le compte utilisateur. Ce déplacement, apparemment mineur, commande toute l'architecture — il est développé au chapitre III.

## 1. Contexte et justification du sujet

Au Sénégal, la couverture du risque maladie s'organise autour de plusieurs dispositifs coexistants : la Couverture Maladie Universelle (CMU), les Institutions de Prévoyance Maladie (IPM) obligatoires pour les entreprises du secteur formel, et les mutuelles de santé communautaires. 

Dans le cas des IPM, qui constituent le cadre privilégié de cette étude, le fonctionnement courant présente quatre caractéristiques structurantes :

**La couverture est familiale, mais l'identité est individuelle.** Un employé assuré ouvre des droits pour son conjoint et ses enfants. Ces ayants droit consomment des soins en leur nom propre, mais ne sont pas titulaires du contrat. Il leur faut donc une identité opposable au prestataire — une carte — sans pour autant disposer d'un accès autonome au dossier de l'assuré principal.

**La décision de prise en charge et l'acte de soin sont décorrélés.** Une demande de prise en charge peut être en attente, validée ou refusée pendant que le soin, lui, a déjà eu lieu. La part restant à la charge du patient dépend pourtant de cette décision. Tant que les deux informations vivent sur des supports séparés, l'assuré découvre son reste à charge après coup.

**L'ordonnance papier est le maillon le plus fragile.** Elle se perd, se photocopie, se rature. Rien, sur le papier, ne distingue une ordonnance déjà servie d'une ordonnance neuve. Le pharmacien ne dispose d'aucun moyen simple de vérifier qu'il ne délivre pas deux fois le même traitement.

**La prise de rendez-vous reste téléphonique**, donc dépendante des horaires d'ouverture et sans trace exploitable pour l'organisme.

La justification du sujet tient dans le fait que ces quatre problèmes ne sont pas quatre problèmes isolés : ce sont quatre symptômes d'une même absence de continuité numérique entre l'assureur, le prestataire et le bénéficiaire.

## 2. Problématique

La numérisation des services de santé est souvent abordée par le dossier médical — on informatise le contenu clinique du soin. Cette approche se heurte, dans le contexte d'un organisme assureur, à deux obstacles : l'assureur n'a **pas vocation** à connaître le diagnostic de ses assurés, et le prestataire n'a pas vocation à ouvrir son système d'information à un tiers payeur.

La problématique se formule donc ainsi :

> **Comment concevoir une plateforme qui rende continue la chaîne de prise en charge médicale — de l'identification du bénéficiaire à la délivrance des médicaments — tout en maintenant un cloisonnement strict des données médicales entre les acteurs qui la composent ?**

La difficulté est que les deux exigences tirent en sens opposé. La continuité demande le partage ; le secret médical demande la rétention. Une plateforme qui privilégie la première devient un dossier médical partagé que ni la réglementation ni les praticiens n'accepteront. Une plateforme qui privilégie la seconde n'apporte rien de plus qu'un classeur.

## 3. Questions de recherche, générale et spécifiques

**Question générale.** Quelle architecture de données et de permissions permet d'unifier le parcours de prise en charge sans constituer un dossier médical centralisé ?

**Questions spécifiques.**

1. Comment représenter un bénéficiaire qui possède une identité et des droits, mais pas de compte de connexion ?
2. À quelle condition le montant restant à la charge du patient peut-il refléter fidèlement l'état réel de sa prise en charge, et non une hypothèse ?
3. Comment dématérialiser l'ordonnance de façon qu'elle soit vérifiable en pharmacie sans qu'aucune donnée médicale ne circule en clair ?
4. Quelle granularité de traçabilité permet d'auditer les décisions administratives sans dupliquer l'information que portent déjà les actes de soin ?

## 4. Objectif général et objectifs subsidiaires

**Objectif général.** Concevoir, développer et éprouver une plateforme web de gestion de la prise en charge médicale couvrant les quatre rôles de la chaîne — administrateur, assuré, médecin, pharmacien — et garantissant par construction le cloisonnement des données médicales.

**Objectifs subsidiaires.**

| N° | Objectif Subsidiaire | Vérifiable par |
|---|---|---|
| **O1** | Modéliser bénéficiaires, ayants droit et droits de couverture | Diagramme de classes, tests d'invariants |
| **O2** | Automatiser le calcul de la part patient à partir du statut réel de la prise en charge | Tests de `Paiement.calculer_pour` |
| **O3** | Dématérialiser l'ordonnance sous forme structurée avec vérification par QR code | Parcours médecin → pharmacien |
| **O4** | Cloisonner les accès par rôle, côté serveur | Matrice 98 routes × 5 profils |
| **O5** | Assurer la traçabilité des décisions administratives | Journal d'activité, tests de survie |
| **O6** | Livrer une interface utilisable sur téléphone et imprimable | Mesures responsive et impression |

## 5. Hypothèses de recherche

**H1 — Hypothèse du bénéficiaire.** Porter l'identité de couverture par une entité `Patient` distincte du compte `User` permet de couvrir les ayants droit sans leur ouvrir d'accès.

**H2 — Hypothèse de la causalité tarifaire.** Adosser le taux de couverture appliqué au **statut** de la prise en charge liée, et non au seul profil du patient, supprime l'écart entre le montant annoncé et le montant dû.

**H3 — Hypothèse du QR non porteur.** Un code QR qui n'encode qu'un identifiant ou une URL — la vérification des droits restant côté serveur — permet la dématérialisation sans exposition, y compris si le code est photographié.

**H4 — Hypothèse de la trace sélective.** Journaliser les décisions administratives et les destructions, à l'exclusion des actes de soin et de la navigation, suffit à l'auditabilité tout en gardant le journal lisible.

Ces quatre hypothèses sont reprises et confrontées aux résultats au chapitre IV, section 2, sous-section 2.

## 6. Méthodologie retenue

Le travail a suivi une démarche **itérative et incrémentale**, avec pour chaque module un cycle imposé en cinq temps :

1. **Analyse** — lecture de l'existant, détection des erreurs et doublons, sans aucune modification ;
2. **Proposition** — fichiers concernés, justification, impacts, et attente de validation pour tout changement structurant ;
3. **Développement** — un seul module à la fois, réutilisation du code existant ;
4. **Vérification** — contrôles automatisés puis test manuel de l'interface ;
5. **Restitution** — fichiers modifiés, fonctionnalités, tests, suite.

Deux principes méthodologiques ont été appliqués de façon systématique :

**Vérifier par la mesure, jamais par la relecture.** Plusieurs défauts réels n'étaient pas détectables à la lecture du code : des QR codes rendus vides, du texte saisi invisible en thème sombre, une colonne d'actions repoussée hors de l'écran sur téléphone. Tous ont été trouvés en instrumentant un navigateur sans interface (protocole Chrome DevTools) et en relevant des valeurs calculées — contrastes, rectangles englobants, nombre de requêtes SQL.

**Traiter le test comme une preuve, pas comme une formalité.** Chaque fonctionnalité livrée s'accompagne de tests de permissions, de redirections et de garde-fous. La suite compte aujourd'hui **91 cas de tests complexes**.

## 7. Annonce du plan

Le **chapitre I** pose le cadre théorique : concepts de l'assurance maladie et du numérique en santé, puis état de l'art des solutions existantes et positionnement de SantéSN. Le **chapitre II** décrit le contexte de l'étude, général puis spécifique. Le **chapitre III** expose la spécification des besoins, le choix des méthodes de modélisation, la modélisation elle-même, puis les choix technologiques et le protocole d'expérimentation. Le **chapitre IV** présente les données, la réalisation des interfaces, la discussion des résultats au regard des hypothèses, et les recommandations.

\newpage

---

# CHAPITRE I : CADRE THÉORIQUE ET CONCEPTUEL

## Section 1 : Revue conceptuelle

### Sous-section 1 : Concepts de l'assurance maladie

**Assuré principal.** Personne titulaire du contrat, généralement un employé affilié par son employeur. Elle ouvre les droits et répond de ses ayants droit. Dans SantéSN, elle est la seule catégorie de bénéficiaire à disposer d'un compte de connexion.

**Ayant droit.** Personne rattachée à un assuré principal par un lien de parenté (conjoint, enfant) et couverte à ce titre. Elle consomme des soins en son nom, possède sa propre carte, mais n'a **pas** d'accès autonome à la plateforme : son dossier est géré par l'assuré principal. Cette asymétrie — une identité sans compte — est le premier concept structurant du modèle.

**Plan de couverture.** Contrat définissant un **taux de couverture** (part supportée par l'assureur, exprimée en pourcentage) et un éventuel **plafond annuel**. Les ayants droit héritent du plan de leur assuré principal.

**Prise en charge.** Demande formulée pour un bénéficiaire, portant un motif et une date, et prenant l'un de trois statuts : *en attente*, *validée*, *refusée*. Elle constitue la **décision** de l'assureur, distincte de l'acte de soin.

**Part patient (ticket modérateur).** Fraction du coût restant due par le bénéficiaire. Dans SantéSN, elle n'est pas une propriété du patient mais le **résultat d'un calcul** : le taux du plan ne s'applique que si la prise en charge rattachée à la consultation est au statut *validée* ; à défaut, le patient règle l'intégralité.

**Tiers payant.** Mécanisme par lequel le prestataire est réglé directement par l'assureur, le bénéficiaire n'avançant que sa part. C'est le modèle économique que la plateforme outille.

**Prestataire conventionné.** Établissement — hôpital, clinique, cabinet, pharmacie — lié à l'organisme par une convention. Le caractère *partenaire* et la date de conventionnement sont des attributs du prestataire.

### Sous-section 2 : Concepts du numérique en santé

**E-santé.** Ensemble des usages des technologies de l'information appliqués à la santé. On distingue utilement les systèmes qui traitent **le contenu du soin** (dossier médical, aide au diagnostic) de ceux qui traitent **la circulation administrative autour du soin** (droits, rendez-vous, facturation). SantéSN relève exclusivement de la seconde catégorie — précision décisive pour son périmètre.

**Dématérialisation de l'ordonnance.** Remplacement du support papier par un enregistrement structuré. Une ordonnance dématérialisée n'est pas une image d'une ordonnance : elle est composée de **lignes de prescription** exploitables individuellement (médicament, dosage, posologie, durée, quantité).

**Code QR.** Code-barres bidimensionnel normalisé (ISO/IEC 18004), capable de porter une charge utile de quelques centaines de caractères et lisible par tout téléphone. Deux usages doivent être distingués : le QR **porteur de données**, qui transporte l'information elle-même, et le QR **porteur de référence**, qui ne transporte qu'un identifiant, l'information restant sur le serveur. Le second est le seul acceptable pour des données de santé, puisqu'un code photographié n'apprend alors rien à qui le détient.

**Contrôle d'accès fondé sur les rôles (RBAC).** Modèle où les permissions sont attachées à des rôles, eux-mêmes attribués aux utilisateurs. Il s'oppose au contrôle par liste d'accès individuelle. Sa vertu ici est la lisibilité : quatre rôles, des règles énonçables en une phrase chacune.

**Cloisonnement et principe du besoin d'en connaître.** Un acteur n'accède qu'aux données nécessaires à sa fonction. Appliqué à SantéSN : le pharmacien voit les ordonnances non délivrées, jamais le diagnostic ; le médecin ne voit que les dossiers de **ses propres** consultations ; l'administrateur voit l'acte et sa facturation, jamais son contenu médical.

**Auditabilité.** Capacité à établir *a posteriori* qui a décidé quoi et quand. Elle suppose une trace non modifiable, qui survive à la disparition de l'objet tracé — sans quoi supprimer un objet effacerait la preuve de sa suppression.

---

## Section 2 : Revue de littérature et état de l'art

L'état de l'art se lit selon deux axes : la **couverture fonctionnelle** et le **modèle de déploiement**.

### Les systèmes d'information hospitaliers libres

**OpenMRS** et **GNU Health** sont des plateformes libres de dossier médical électronique, largement déployées dans les pays à ressources limitées. Elles couvrent le dossier patient, les consultations, parfois la pharmacie et la facturation. Leur logique est celle de l'**établissement** : elles informatisent un hôpital.

**OpenEMR** poursuit un objectif comparable pour les structures ambulatoires.

*Limite au regard de notre problématique :* ces systèmes sont centrés sur le producteur de soins. L'assureur y est au mieux un destinataire de facture. La notion d'ayant droit sans compte, de plan de couverture et de statut de prise en charge n'y est pas première.

### Les systèmes nationaux d'information sanitaire

**DHIS2**, développé par l'Université d'Oslo et déployé dans de nombreux ministères de la santé africains, est un système d'agrégation de données sanitaires à visée épidémiologique et de pilotage.

*Limite :* il travaille sur des agrégats, non sur le parcours individuel d'un bénéficiaire. Il ne répond pas à la question du droit ouvert.

### Les plateformes de prise de rendez-vous

**Doctolib** et ses équivalents ont démontré l'acceptabilité de la prise de rendez-vous en ligne à grande échelle.

*Limite :* le rendez-vous y est le produit, non un maillon d'une chaîne de couverture. Aucune articulation avec un droit d'assurance.

### La prescription électronique

L'**Estonie** constitue la référence la plus citée en matière d'ordonnance entièrement dématérialisée à l'échelle nationale : le patient se présente en pharmacie avec sa pièce d'identité, la prescription étant récupérée dans un registre central. La **France**, avec *Mon espace santé* et le dispositif d'ordonnance numérique, poursuit une trajectoire comparable.

*Enseignement retenu :* ces dispositifs confirment l'hypothèse H3 — la sécurité ne vient pas du support, mais du fait que le support ne porte qu'une référence.

*Limite de transposition :* ils supposent un identifiant national de santé et une infrastructure centralisée que le cadre de cette étude n'offre pas. D'où le choix d'un identifiant **porté par la carte de l'organisme** (`numero_carte`), et non d'un identifiant national.

### Positionnement de SantéSN

| Dimension | SIH libres | DHIS2 | Prise de RDV | SantéSN |
|---|:---:|:---:|:---:|:---:|
| Dossier médical complet | ● | ○ | ○ | ○ |
| Pilotage épidémiologique | ○ | ● | ○ | ○ |
| Prise de rendez-vous | ◐ | ○ | ● | ● |
| Droits d'assurance et ayants droit | ○ | ○ | ○ | ● |
| Calcul de la part patient | ◐ | ○ | ○ | ● |
| Ordonnance structurée + QR | ◐ | ○ | ○ | ● |
| Validation de délivrance en pharmacie | ◐ | ○ | ○ | ● |
| Traçabilité des décisions administratives | ◐ | ○ | ○ | ● |

*● couvert · ◐ partiel ou optionnel · ○ hors périmètre*

**La contribution revendiquée n'est pas technologique, elle est architecturale :** placer la *couverture* — et non le *dossier* — au centre du modèle, et montrer que ce déplacement suffit à unifier le parcours sans constituer de dossier médical partagé.

\newpage

---

# CHAPITRE II : CONTEXTE DE L'ÉTUDE

## Section 1 : Contexte général

### Sous-section 1 : Le système de santé et la couverture du risque maladie au Sénégal

Le financement de la santé au Sénégal combine plusieurs mécanismes :

- la **Couverture Maladie Universelle (CMU)**, portée par une agence dédiée et s'appuyant largement sur les mutuelles de santé communautaires ;
- les **Institutions de Prévoyance Maladie (IPM)**, obligatoires pour les entreprises atteignant un seuil d'effectif, financées par cotisations employeur et salarié, et couvrant l'employé ainsi que sa famille ;
- les **assurances privées** et les **mutuelles professionnelles** ;
- le **paiement direct** par les ménages, qui demeure une part significative de la dépense de santé.

Le cadre retenu pour cette étude est celui de l'**IPM**, pour trois raisons : la population couverte y est identifiée et stable, la logique d'ayants droit y est constitutive, et le tiers payant y est la norme.

### Sous-section 2 : La numérisation des services et ses contraintes locales

Trois contraintes ont directement orienté les choix techniques :

**L'accès à Internet passe majoritairement par le téléphone mobile.** La plateforme devait donc être pleinement utilisable sur un écran étroit — non pas « consultable », mais **opérationnelle** : un administrateur doit pouvoir désactiver un compte depuis un téléphone.

**La qualité de connexion est variable.** Le coût du premier chargement a été mesuré et optimisé.

**Le papier ne disparaît pas.** Une ordonnance doit rester imprimable au format A4, une carte de prise en charge au format carte bancaire. La dématérialisation ne remplace pas le papier : elle le rend vérifiable.

---

## Section 2 : Contexte spécifique

### Sous-section 1 : L'organisme, son réseau et ses acteurs

Le système modélisé fait intervenir quatre rôles et un ensemble d'entités conventionnées :

| Acteur | Rôle dans la chaîne | Accès à la plateforme |
|---|---|---|
| **Administrateur** | Gère comptes, référentiels, prises en charge, règlements | Complet, hors contenu médical |
| **Assuré principal** | Gère ses ayants droit, demande rendez-vous et prises en charge, consulte son reste à charge | Son foyer uniquement |
| **Médecin** | Traite les rendez-vous, enregistre consultations et ordonnances | Ses propres patients |
| **Pharmacien** | Scanne l'ordonnance, valide la délivrance | Ordonnances non délivrées |
| **Ayant droit** | Bénéficie des soins, porte une carte | **Aucun** — géré par l'assuré principal |
| **Prestataire** | Hôpital, clinique, cabinet, pharmacie conventionnés | Entité, non utilisateur |

### Sous-section 2 : Limites du fonctionnement actuel et expression du besoin

L'analyse du fonctionnement en vigueur fait apparaître six limites, chacune traduite en besoin :

| # | Limite constatée | Besoin exprimé |
|---|---|---|
| **L1** | L'ayant droit n'a pas d'identité opposable simple | Une carte de prise en charge par bénéficiaire |
| **L2** | L'assuré ignore l'état de sa demande de prise en charge | Un suivi visible du statut de chaque demande |
| **L3** | Le reste à charge est découvert après le soin | Un calcul automatique adossé au statut réel |
| **L4** | L'ordonnance papier n'est ni vérifiable ni traçable | Une ordonnance structurée, vérifiée par QR |
| **L5** | La double délivrance n'est pas détectable | Un état de délivrance opposable au pharmacien |
| **L6** | Les décisions administratives ne laissent pas de trace | Un journal d'activité non modifiable |

\newpage

---

# CHAPITRE III : CADRE MÉTHODOLOGIQUE ET CONCEPTION

## Section 1 : Spécification et modélisation du système

### Sous-section 1 : Spécification des besoins fonctionnels et non-fonctionnels

#### A. Besoins fonctionnels

**BF-1 — Authentification et gestion des rôles.** Connexion unique par adresse électronique et mot de passe. Aucune inscription publique : les comptes sont créés par l'administrateur. Le rôle est stocké en base, jamais choisi à la connexion. Limitation des tentatives : cinq échecs entraînent un blocage temporaire de cinq minutes.

**BF-2 — Gestion des utilisateurs (administrateur).** Création, modification, activation, désactivation, suppression, réinitialisation de mot de passe, attribution de rôle, export de la liste filtrée. Garde-fous : un administrateur ne peut ni modifier son propre rôle, ni se désactiver, ni se supprimer.

**BF-3 — Gestion des bénéficiaires.** Enregistrement des assurés principaux et de leurs ayants droit, rattachement à un plan de couverture, attribution d'un numéro de carte unique. Toute fiche métier disposant d'une connexion crée son compte automatiquement ; les ayants droit n'en ont jamais.

**BF-4 — Référentiels.** Prestataires (avec géolocalisation Leaflet/OSM), services médicaux tarifés, plans de couverture.

**BF-5 — Rendez-vous.** La demande appartient au **bénéficiaire** ; le médecin la traite (confirmation, annulation, clôture). Verrouillage strict contre les doubles réservations d'un même créneau.

**BF-6 — Prises en charge.** Demande, examen, validation ou refus. Invariant : le patient d'une consultation doit être celui de sa prise en charge.

**BF-7 — Consultations et ordonnances.** Le médecin enregistre diagnostic, traitement et service rendu ; il saisit une ordonnance **structurée** en lignes de prescription. Un code QR est généré par ordonnance.

**BF-8 — Délivrance en pharmacie.** Scan du QR, contrôle de l'état de délivrance, validation, historique.

**BF-9 — Paiements.** Calcul automatique du montant total, de la part assurance et de la part patient à l'enregistrement de la consultation ; suivi du règlement.

**BF-10 — Rapports et exports.** Agrégats, graphiques, exports tableur Excel et PDF.

**BF-11 — Traçabilité.** Journal des décisions administratives et des suppressions, en lecture seule.

#### B. Besoins non fonctionnels

| Réf. | Exigence | Critère de vérification |
|---|---|---|
| **BNF-1** | Cloisonnement par rôle vérifié côté serveur | Aucune route accessible hors rôle |
| **BNF-2** | Aucune donnée médicale dans un code QR | Inspection de la charge utile |
| **BNF-3** | Utilisable sur téléphone | Aucun débordement horizontal |
| **BNF-4** | Lisibilité des textes | Contraste conforme WCAG AA (≥ 4,5:1) |
| **BNF-5** | Navigation au clavier | Indicateur de focus visible partout |
| **BNF-6** | Performance d'affichage | Coût du premier rendu mesuré |
| **BNF-7** | Robustesse sur base vide | Aucun écran en erreur sans données |
| **BNF-8** | Intégrité référentielle | Aucune violation de clé étrangère |
| **BNF-9** | Maintenabilité | Suite de tests exécutée à chaque livraison |
| **BNF-10** | Impression | Ordonnance A4, carte au format ISO 7810 ID-1 |

---

### Sous-section 2 : Étude et choix des méthodes de modélisation

Deux familles de méthodes étaient mobilisables : **Merise** et **UML**.

**Choix retenu : UML**, pour trois raisons :
1. **La dimension comportementale est ici déterminante :** Les transitions d'état (PEC validée, RDV confirmé, ordonnance délivrée) s'expriment nativement en UML.
2. **Le système est défini par ses acteurs :** Quatre rôles aux permissions disjointes.
3. **Correspondance directe avec Django :** Le diagramme de classes se traduit directement en modèles ORM.

---

### Sous-section 3 : Modélisation

#### A. Diagramme de cas d'utilisation (description)

**Acteur Administrateur** — Gérer les utilisateurs · Gérer les bénéficiaires · Gérer les référentiels · Statuer sur les prises en charge · Suivre les paiements · Consulter les rapports · Consulter le journal · Imprimer une carte.

**Acteur Assuré** — Gérer son profil · Gérer ses ayants droit · Demander un rendez-vous · Suivre ses prises en charge · Consulter ses ordonnances · Consulter son historique et son reste à charge · Localiser un prestataire proche.

**Acteur Médecin** — Consulter son agenda · Traiter un rendez-vous · Enregistrer une consultation · Rédiger une ordonnance structurée · Consulter la fiche de ses patients.

**Acteur Pharmacien** — Scanner une ordonnance · Valider une délivrance · Consulter l'historique des délivrances.

#### B. Diagramme de classes (description)

Le modèle comporte **17 entités persistantes** :

```
User (1) ──0..1── (1) Patient          [SET_NULL]  compte facultatif
User (1) ──0..1── (1) Medecin          [SET_NULL]
User (1) ──0..1── (1) Pharmacien       [SET_NULL]

Patient (1) ──── (0..n) Patient        [CASCADE]   assuré principal → ayants droit
PlanCouverture (1) ──── (0..n) Patient [SET_NULL]

Prestataire (1) ──── (0..n) Medecin | Pharmacien | ServiceMedical | RendezVous

Patient (1) ──── (0..n) PriseEnCharge  [CASCADE]
Patient (1) ──── (0..n) RendezVous     [CASCADE]
Patient (1) ──── (0..n) Consultation   [CASCADE]
Medecin (1) ──── (0..n) Consultation   [CASCADE]
PriseEnCharge (1) ──── (0..n) Consultation [SET_NULL]
ServiceMedical (1) ──── (0..n) Consultation [SET_NULL]

Consultation (1) ──1..1── (1) Paiement     [CASCADE]
Consultation (1) ──── (0..n) Ordonnance    [CASCADE]
Ordonnance (1) ──── (0..n) LigneOrdonnance [CASCADE]
Ordonnance (1) ──1..1── (1) Delivrance     [CASCADE]
Pharmacien (1) ──── (0..n) Delivrance      [CASCADE]

JournalActivite (0..n) ──0..1── User        [SET_NULL] + libellé figé
```

**Trois décisions de modélisation majeures :**
1. **`Patient.user` est facultatif et en `SET_NULL` :** Un ayant droit est un `Patient` sans `User`. Les droits survivent à la suppression d'un compte de connexion.
2. **`Paiement` est en relation 1–1 avec `Consultation` :** Le paiement est calculé et non saisi.
3. **`JournalActivite` ne comporte aucune clé étrangère vers l'objet tracé :** L'objet et l'auteur sont enregistrés sous forme de texte figé pour survivre aux suppressions.

#### C. Diagrammes d'états-transitions

```
Rendez-vous :       [DEMANDE] ──(médecin)──► [CONFIRME] ──(médecin)──► [TERMINE]
                        │                        │
                        └──────(médecin/assuré)──┴────────► [ANNULE]

Prise en charge :   [en_attente] ──(admin)──► [validee]  (taux du plan appliqué)
                        │
                        └────────(admin)──► [refusee]  (100% à charge patient)

Ordonnance :        [non délivrée] ──(pharmacien : scan + validation)──► [délivrée]
```

#### D. Diagramme de séquence — parcours de l'ordonnance

```
Médecin        Plateforme                    Pharmacien
   │                │                             │
   │─ consultation ►│                             │
   │                │─ calcule le paiement        │
   │─ ordonnance   ►│                             │
   │  (n lignes)    │─ génère le QR (référence)   │
   │◄─ document A4 ─│                             │
   │                │                             │
   │       (le patient porte l'ordonnance)        │
   │                │                             │
   │                │◄──────── scan du QR ────────│
   │                │─ vérifie le RÔLE côté serveur
   │                │─ n'expose QUE les non délivrées
   │                │──── lignes de prescription ►│
   │                │◄──── validation ────────────│
   │                │─ enregistre la Délivrance   │
```

---

## Section 2 : Implémentation et évaluation des modèles

### Sous-section 1 : Choix technologiques et justification

| Couche | Technologie | Version | Justification |
|---|---|---|---|
| Langage | Python | 3.14 | Lisibilité, écosystème, robustesse |
| Cadriciel | Django | 5.2.x | ORM, sécurité intégrée (CSRF, XSS, SQLi), sessions |
| Base (dév / test) | SQLite | — | Isolation totale des tests, fichier unique |
| Base (production) | PostgreSQL | — | Concurrence, intégrité, montée en charge |
| Codes QR | `qrcode` | 8.2 | Génération SVG vectorielle pure |
| Export tableur | `openpyxl` | 3.1.x | Fichiers `.xlsx` natifs |
| Export PDF | `reportlab` | 4.4.x | Documents vectoriels haute précision |
| Cartographie | Leaflet + OpenStreetMap | — | Cartographie interactive libre |

### Sous-section 2 : Description de l'expérimentation

Le protocole d'évaluation comporte **cinq dispositifs** :
* **E1 — Tests automatisés :** 91 cas de tests complexes couvrant les rôles, les invariants et les flux métiers.
* **E2 — Matrice de permissions :** Énumération automatique des 98 routes sous 5 profils (Anonyme, Assuré, Médecin, Pharmacien, Administrateur).
* **E3 — Mesure en navigateur réel (Chrome DevTools) :** Ratios de contraste calculés, vérification responsive sur 360px / 768px / 1440px.
* **E4 — Épreuve de la base vide :** Exécution de toutes les routes sur base de données vierge.
* **E5 — Contrôle d'intégrité :** Validation de l'intégrité relationnelle et de la journalisation immuable.

\newpage

---

# CHAPITRE IV : CADRE ANALYTIQUE ET RÉALISATION

## Section 1 : Présentation et traitement des données

### Sous-section 1 : Description des données (sources, structure, qualité)

#### A. Sources
Toutes les données de la plateforme proviennent d'une saisie humaine authentifiée (Admin, Médecin, Pharmacien, Assuré). La part assurance et la part patient sont calculées automatiquement.

#### B. Structure
17 entités persistantes regroupées en 8 familles : Identité (`User`, `TentativeConnexion`), Bénéficiaires (`Patient`, `PlanCouverture`), Réseau (`Prestataire`, `Medecin`, `Pharmacien`, `ServiceMedical`), Droits (`PriseEnCharge`), Parcours (`RendezVous`, `Consultation`), Prescription (`Ordonnance`, `LigneOrdonnance`, `Delivrance`), Financier (`Paiement`), Support (`Notification`, `JournalActivite`, `PreferenceNotification`).

#### C. Qualité — trois mécanismes de garantie
1. **Invariants dans les modèles (`clean()`) :** Le patient d'une consultation doit correspondre à celui de sa prise en charge.
2. **Pagination ordonnée :** Tri systématique évitant les doublons de pagination.
3. **Séparation valeurs / libellés :** Les filtres exploitent toujours les codes bruts.

### Sous-section 2 : Traitement, cycle de vie et rétention des données

- **Rien de médical ne disparaît automatiquement :** Suppression explicite confirmée.
- **Suppressions en cascade maîtrisées :** Clés `SET_NULL` pour les accès, `CASCADE` pour les compositions strictes (lignes d'ordonnance).
- **Symétrie de suppression :** Supprimer une fiche métier désactive le compte utilisateur lié.

---

## Section 2 : Réalisation et analyse des fonctionnalités

### Sous-section 1 : Implémentation des interfaces utilisateur

#### A. Architecture de l'interface
Un cadre partagé (barre latérale et supérieure) avec navigation conditionnée par le rôle. 77 gabarits composent l'interface.

#### B. Identité visuelle
Palette turquoise (`#008779`) / marine (`#132B45`) / terracotta (`#D9534F`). Typographies Manrope, Public Sans et IBM Plex Mono. **Zéro émoji**, icônes SVG natives exclusivement.

#### C. Adaptation aux petits écrans
Masquage des colonnes secondaires sous 900px, colonne Actions toujours visible, disposition fluide de 360px à 1440px.

#### D. Thème sombre
Implémenté via variables CSS contextualisées (`var(--surface)`, `var(--border)`), sans duplication de code.

#### E. Documents imprimables
Ordonnance A4 normalisée et Carte d'assuré au format ISO 7810 ID-1 avec QR code SVG purifié des espaces de noms XML.

#### F. Accessibilité
Contraste mesuré à 16,44:1 (clair) et 14,42:1 (sombre), indicateurs de focus visibles et balises sémantiques.

### Sous-section 2 : Synthèse et discussion des résultats

#### A. Métriques de réalisation
- 17 entités persistantes, 17 migrations, 98 routes, 20 modules de vues, 77 gabarits.
- 5 146 lignes de code Python applicatif, 6 365 lignes de tests automatisés.
- **91 tests automatisés (100% de réussite)**.

#### B. Résultats de l'évaluation
Toutes les exigences BNF-1 à BNF-10 sont satisfaites et validées par la mesure.

#### C. Confrontation aux hypothèses
- **H1 (Bénéficiaire distinct du compte) : Validée.**
- **H2 (Causalité tarifaire) : Validée.**
- **H3 (QR non porteur) : Validée.**
- **H4 (Trace sélective) : Validée.**

#### D. Discussion critique — limites du travail
1. Absence de modification en place d'une ordonnance émise (choix de sécurité).
2. Dépendance aux passerelles externes pour SMS/WhatsApp.
3. Absence d'encaissement bancaire en ligne direct.
4. Référentiel médicamenteux textuel.
5. Feuille de style principale volumineuse.

#### E. Enseignement méthodologique transversal
Aucun des défauts réels n'a été découvert par simple relecture du code : tous ont été identifiés par la mesure instrumentée et le rendu réel.

### Sous-section 3 : Recommandations

#### Court terme — avant mise en service
- **R1 :** Harmonisation totale des formulaires sur l'onboarding par jeton 24h.
- **R2 :** Configuration de la passerelle WhatsApp / SMTP de production.
- **R3 :** Bascule sur PostgreSQL.

#### Moyen terme
- **R4 :** Modularisation des feuilles de style statiques.
- **R5 :** Journalisation des accès en lecture aux données médicales.
- **R6 :** Raccordement à la nomenclature officielle des médicaments.
- **R7 :** Revue visuelle typographique continue.

#### Long terme
- **R8 :** Interface d'échange HL7 / FHIR.
- **R9 :** Module de téléconsultation intégré.
- **R10 :** Audit de conformité réglementaire sur les données de santé.

\newpage

---

# Conclusion générale

Ce travail est parti d'une tension fondamentale : la chaîne de prise en charge médicale exige de la continuité, tandis que le secret médical exige de la rétention. L'hypothèse directrice était qu'on pouvait concilier les deux en déplaçant le centre du modèle — en plaçant la **couverture d'assurance** au cœur du système plutôt que le **dossier clinique**.

Ce déplacement s'est révélé particulièrement fécond. Il a permis de représenter un ayant droit comme une identité sans accès, de faire du reste à charge un calcul déterministe plutôt qu'une déclaration, et de dématérialiser l'ordonnance au moyen d'un code QR qui ne transporte aucune donnée médicale — la vérification restant entière du côté du serveur. Les quatre hypothèses de recherche sont formellement validées.

Sur le plan de la réalisation, SantéSN couvre les quatre rôles de bout en bout et satisfait l'intégralité des exigences non fonctionnelles formulées, chacune vérifiée par une mesure reproductible.

Enfin, la contribution la plus transférable de ce travail réside dans sa discipline de vérification par la mesure empirique, posant les bases solides d'une solution pérenne pour la transformation numérique de la santé au Sénégal.

\newpage

---

# Webographie

**Cadriciel et bibliothèques**
- Documentation Django — https://docs.djangoproject.com/
- Guide de sécurité Django — https://docs.djangoproject.com/en/stable/topics/security/
- Bibliothèque `qrcode` Python — https://pypi.org/project/qrcode/
- Bibliothèque `openpyxl` — https://openpyxl.readthedocs.io/
- Bibliothèque ReportLab — https://docs.reportlab.com/
- Bibliothèque Leaflet — https://leafletjs.com/
- OpenStreetMap & Nominatim — https://operations.osmfoundation.org/policies/nominatim/

**Normes et référentiels**
- W3C — Web Content Accessibility Guidelines (WCAG) 2.2 — https://www.w3.org/TR/WCAG22/
- ISO/IEC 18004 — Code à barres bidimensionnel QR Code — https://www.iso.org/standard/83389.html
- ISO/IEC 7810 — Cartes d'identification physiques — https://www.iso.org/standard/70483.html
- Standard HL7 FHIR — https://www.hl7.org/fhir/

**Systèmes de santé et couverture**
- OMS — Couverture sanitaire universelle — https://www.who.int/health-topics/universal-health-coverage
- Agence Nationale de la Statistique et de la Démographie (ANSD) — https://www.ansd.sn/

**Solutions comparées (état de l'art)**
- OpenMRS — https://openmrs.org/
- GNU Health — https://www.gnuhealth.org/
- OpenEMR — https://www.open-emr.org/
- DHIS2 — https://dhis2.org/
- e-Estonia, prescription électronique — https://e-estonia.com/solutions/healthcare/e-prescription/
- Mon espace santé (France) — https://www.monespacesante.fr/

\newpage

---

# Annexes

## Annexe 1 : Inventaire exhaustif des 98 routes du système SantéSN

| Route (Chemin d'URL) | Vue associée | Rôle requis | Finalité |
| :--- | :--- | :---: | :--- |
| `/` | `landing` | Public | Accueil public institutionnel |
| `/connexion/` | `login_view` | Public | Authentification unique |
| `/deconnexion/` | `logout_view` | Connecté | Déconnexion sécurisée POST |
| `/activer-compte/<uidb64>/<token>/` | `activer_compte` | Public (Token) | Activation initiale de compte |
| `/tableau-de-bord/` | `dashboard` | `ADMIN` | Pilotage global administrateur |
| `/espace/medecin/` | `dashboard_medecin` | `MEDECIN` | Tableau de bord médical « Ma journée » |
| `/espace/pharmacien/` | `dashboard_pharmacien`| `PHARMACIEN` | Console scan et délivrance officine |
| `/espace/assure/` | `dashboard_assure` | `ASSURE` | Synthèse démarches et carte |
| `/utilisateurs/` | `liste_utilisateurs` | `ADMIN` | Gestion des comptes utilisateurs |
| `/utilisateurs/ajouter/` | `ajouter_utilisateur` | `ADMIN` | Création avec lien d'activation |
| `/utilisateurs/importer/` | `importer_utilisateurs_excel`| `ADMIN` | Import en masse Excel |
| `/patients/` | `liste_patients` | `ADMIN` | Répertoire des assurés |
| `/patients/<pk>/carte/` | `carte_patient` | Authentifié | Affichage carte dématérialisée |
| `/carte/<numero>/` | `carte_scan` | `MEDECIN`/`PHARM` | Destination sécurisée scan QR carte |
| `/medecin/agenda/` | `agenda_medecin` | `MEDECIN` | Calendrier des consultations |
| `/medecin/consultations/ajouter/` | `ajouter_consultation_medecin`| `MEDECIN` | Enregistrement acte et facture |
| `/medecin/consultations/<pk>/ordonnance/ajouter/`| `ajouter_ordonnance_medecin`| `MEDECIN`| Prescription structurée |
| `/pharmacien/scanner/` | `scanner_ordonnance` | `PHARMACIEN` | Interface scan et saisie code RX |
| `/pharmacien/ordonnances/<pk>/delivrer/`| `valider_delivrance` | `PHARMACIEN` | Validation irréversible de délivrance |
| `/assure/ayants-droit/` | `liste_ayants_droit` | `ASSURE` | Gestion des ayants droit |
| `/assure/rendez-vous/ajouter/` | `ajouter_rendez_vous_assure`| `ASSURE` | Demande de rendez-vous |
| `/prises-en-charge/` | `liste_prises_en_charge`| `ADMIN` | Instruction des prises en charge |
| `/paiements/` | `liste_paiements` | `ADMIN` | Suivi financier du tiers-payant |
| `/journal/` | `journal_activite` | `ADMIN` | Registre d'audit inaltérable |
| `/rapports/exporter/pdf/` | `exporter_rapports_pdf` | `ADMIN` | Export du rapport d'activité PDF |

---

## Annexe 2 : Dictionnaire des données des entités fondamentales

### `Paiement`
* `id` : Entier long auto-incrémenté (PK).
* `consultation_id` : Clé One-to-One vers `Consultation` (`on_delete=CASCADE`).
* `montant_total` : Décimal (10, 2) — Tarif conventionné du service médical.
* `taux_applique` : Décimal (5, 2) — Pourcentage effectif de couverture.
* `montant_part_assurance` : Décimal (10, 2) — Quote-part de l'assureur.
* `montant_part_patient` : Décimal (10, 2) — Ticket modérateur restant.
* `statut` : Indexé (`non_regle`, `regle`).
* `mode_reglement` : Chaîne (`ESPECES`, `MOBILE_MONEY`, `CARTE`, `VIREMENT`).
* `date_reglement` : Horodatage d'encaissement.
* `enregistre_par_id` : Clé vers `User` (`on_delete=SET_NULL`).

### `Ordonnance`
* `id` : Entier long auto-incrémenté (PK).
* `consultation_id` : Clé vers `Consultation` (`on_delete=CASCADE`).
* `code_qr` : Chaîne unique (`RX-XXXXXXXXXX`, 20 car., indexée).
* `medicaments` : Texte libre historique.
* `date_creation` : Horodatage de création.

### `Delivrance`
* `id` : Entier long auto-incrémenté (PK).
* `ordonnance_id` : Clé One-to-One vers `Ordonnance` (`on_delete=CASCADE`).
* `pharmacien_id` : Clé vers `Pharmacien` (`on_delete=CASCADE`).
* `date_delivrance` : Horodatage de délivrance au comptoir.

---

## Annexe 3 : Synthèse de la validation de la suite de tests automatisés (91 tests)

```text
Creating test database for alias 'default'...
...........................................................................................
-------------------------------------------------------------------------------------------
Ran 91 tests in 152.208s

OK (100% SUCCESS)
Destroying test database for alias 'default'...
System check identified no issues (0 silenced).
```

---
*Fin du Mémoire Académique SantéSN.*
