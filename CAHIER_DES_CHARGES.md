# SantéSN — Plateforme numérique de gestion de la prise en charge médicale

**Document de projet suivant la structure de mémoire imposée**

---

> **Note de lecture.** Ce document suit exactement la table des matières fournie.
> Toutes les données techniques (métriques, modèles, routes, résultats de tests)
> ont été **relevées sur le code source** à la date du 17 août 2026 et sont
> vérifiables. Les emplacements marqués **[À SOURCER]** attendent une donnée
> chiffrée externe : elle doit être reprise d'une source officielle citée en
> webographie, jamais estimée. Un chiffre inventé est la faille la plus facile à
> ouvrir en soutenance.

---

# Introduction générale

L'assurance maladie repose sur une chaîne d'acteurs qui ne partagent presque
jamais le même support d'information. L'assuré détient une carte, l'employeur
détient les droits, le médecin détient le diagnostic, la pharmacie détient la
délivrance, et l'organisme assureur détient la décision de prise en charge.
Chacun de ces maillons fonctionne ; c'est leur articulation qui coûte cher, en
temps comme en confiance.

SantéSN est une plateforme web qui réunit ces maillons autour d'un objet
central : le **bénéficiaire**, et non le compte utilisateur. Ce déplacement,
apparemment mineur, commande toute l'architecture — il est développé au
chapitre III.

## 1. Contexte et justification du sujet

Au Sénégal, la couverture du risque maladie s'organise autour de plusieurs
dispositifs coexistants : la Couverture Maladie Universelle, les Institutions de
Prévoyance Maladie (IPM) obligatoires pour les entreprises d'une certaine
taille, et les mutuelles de santé communautaires. **[À SOURCER : part de la
population couverte, nombre d'IPM actives — source Agence de la CMU / ANSD.]**

Dans le cas des IPM, qui constituent le cadre de cette étude, le fonctionnement
courant présente quatre caractéristiques structurantes :

**La couverture est familiale, mais l'identité est individuelle.** Un employé
assuré ouvre des droits pour son conjoint et ses enfants. Ces ayants droit
consomment des soins en leur nom propre, mais ne sont pas titulaires du contrat.
Il leur faut donc une identité opposable au prestataire — une carte — sans pour
autant disposer d'un accès autonome au dossier de l'assuré principal.

**La décision de prise en charge et l'acte de soin sont décorrélés.** Une
demande de prise en charge peut être en attente, validée ou refusée pendant que
le soin, lui, a déjà eu lieu. La part restant à la charge du patient dépend
pourtant de cette décision. Tant que les deux informations vivent sur des
supports séparés, l'assuré découvre son reste à charge après coup.

**L'ordonnance papier est le maillon le plus fragile.** Elle se perd, se
photocopie, se rature. Rien, sur le papier, ne distingue une ordonnance déjà
servie d'une ordonnance neuve. Le pharmacien ne dispose d'aucun moyen simple de
vérifier qu'il ne délivre pas deux fois le même traitement.

**La prise de rendez-vous reste téléphonique**, donc dépendante des horaires
d'ouverture et sans trace exploitable pour l'organisme.

La justification du sujet tient dans le fait que ces quatre problèmes ne sont pas
quatre problèmes : ce sont quatre symptômes d'une même absence de continuité
numérique entre l'assureur, le prestataire et le bénéficiaire.

## 2. Problématique

La numérisation des services de santé est souvent abordée par le dossier médical
— on informatise le contenu du soin. Cette approche se heurte, dans le contexte
d'un organisme assureur, à deux obstacles : l'assureur n'a **pas vocation** à
connaître le diagnostic de ses assurés, et le prestataire n'a pas vocation à
ouvrir son système d'information à un tiers payeur.

La problématique se formule donc ainsi :

> **Comment concevoir une plateforme qui rende continue la chaîne de prise en
> charge médicale — de l'identification du bénéficiaire à la délivrance des
> médicaments — tout en maintenant un cloisonnement strict des données
> médicales entre les acteurs qui la composent ?**

La difficulté est que les deux exigences tirent en sens opposé. La continuité
demande le partage ; le secret médical demande la rétention. Une plateforme qui
privilégie la première devient un dossier médical partagé que ni la
réglementation ni les praticiens n'accepteront. Une plateforme qui privilégie la
seconde n'apporte rien de plus qu'un classeur.

## 3. Questions de recherche, générale et spécifiques

**Question générale.** Quelle architecture de données et de permissions permet
d'unifier le parcours de prise en charge sans constituer un dossier médical
centralisé ?

**Questions spécifiques.**

1. Comment représenter un bénéficiaire qui possède une identité et des droits,
   mais pas de compte de connexion ?
2. À quelle condition le montant restant à la charge du patient peut-il refléter
   fidèlement l'état réel de sa prise en charge, et non une hypothèse ?
3. Comment dématérialiser l'ordonnance de façon qu'elle soit vérifiable en
   pharmacie sans qu'aucune donnée médicale ne circule en clair ?
4. Quelle granularité de traçabilité permet d'auditer les décisions
   administratives sans dupliquer l'information que portent déjà les actes de
   soin ?

## 4. Objectif général et objectifs subsidiaires

**Objectif général.** Concevoir, développer et éprouver une plateforme web de
gestion de la prise en charge médicale couvrant les quatre rôles de la chaîne
— administrateur, assuré, médecin, pharmacien — et garantissant par construction
le cloisonnement des données médicales.

**Objectifs subsidiaires.**

| N° | Objectif | Vérifiable par |
|---|---|---|
| O1 | Modéliser bénéficiaires, ayants droit et droits de couverture | Diagramme de classes, tests d'invariants |
| O2 | Automatiser le calcul de la part patient à partir du statut réel de la prise en charge | Tests de `Paiement.calculer_pour` |
| O3 | Dématérialiser l'ordonnance sous forme structurée avec vérification par QR code | Parcours médecin → pharmacien |
| O4 | Cloisonner les accès par rôle, côté serveur | Matrice 98 routes × 5 profils |
| O5 | Assurer la traçabilité des décisions administratives | Journal d'activité, tests de survie |
| O6 | Livrer une interface utilisable sur téléphone et imprimable | Mesures responsive et impression |

## 5. Hypothèses de recherche

**H1 — Hypothèse du bénéficiaire.** Porter l'identité de couverture par une
entité `Patient` distincte du compte `User` permet de couvrir les ayants droit
sans leur ouvrir d'accès.

**H2 — Hypothèse de la causalité tarifaire.** Adosser le taux de couverture
appliqué au **statut** de la prise en charge liée, et non au seul profil du
patient, supprime l'écart entre le montant annoncé et le montant dû.

**H3 — Hypothèse du QR non porteur.** Un code QR qui n'encode qu'un identifiant
ou une URL — la vérification des droits restant côté serveur — permet la
dématérialisation sans exposition, y compris si le code est photographié.

**H4 — Hypothèse de la trace sélective.** Journaliser les décisions
administratives et les destructions, à l'exclusion des actes de soin et de la
navigation, suffit à l'auditabilité tout en gardant le journal lisible.

Ces quatre hypothèses sont reprises et confrontées aux résultats au
chapitre IV, section 2, sous-section 2.

## 6. Méthodologie retenue

Le travail a suivi une démarche **itérative et incrémentale**, structurée en
quinze phases, avec pour chaque module un cycle imposé en cinq temps :

1. **Analyse** — lecture de l'existant, détection des erreurs et doublons, sans
   aucune modification ;
2. **Proposition** — fichiers concernés, justification, impacts, et attente de
   validation pour tout changement structurant ;
3. **Développement** — un seul module à la fois, réutilisation du code existant ;
4. **Vérification** — contrôles automatisés puis test manuel de l'interface ;
5. **Restitution** — fichiers modifiés, fonctionnalités, tests, suite.

Deux principes méthodologiques ont été appliqués de façon systématique et
méritent d'être explicités, car ce sont eux qui ont produit les résultats les
moins attendus :

**Vérifier par la mesure, jamais par la relecture.** Plusieurs défauts réels
n'étaient pas détectables à la lecture du code : des QR codes rendus vides, du
texte saisi invisible en thème sombre, une colonne d'actions repoussée hors de
l'écran sur téléphone. Tous ont été trouvés en instrumentant un navigateur sans
interface (protocole Chrome DevTools) et en relevant des valeurs calculées —
contrastes, rectangles englobants, nombre de requêtes SQL.

**Traiter le test comme une preuve, pas comme une formalité.** Chaque
fonctionnalité livrée s'accompagne de tests de permissions, de redirections et
de garde-fous. La suite compte aujourd'hui **569 tests répartis en 74 classes**.

## 7. Annonce du plan

Le **chapitre I** pose le cadre théorique : concepts de l'assurance maladie et du
numérique en santé, puis état de l'art des solutions existantes et positionnement
de SantéSN. Le **chapitre II** décrit le contexte de l'étude, général puis
spécifique. Le **chapitre III** expose la spécification des besoins, le choix des
méthodes de modélisation, la modélisation elle-même, puis les choix
technologiques et le protocole d'expérimentation. Le **chapitre IV** présente les
données, la réalisation des interfaces, la discussion des résultats au regard des
hypothèses, et les recommandations.

---

# CHAPITRE I : CADRE THÉORIQUE ET CONCEPTUEL

## Section 1 : Revue conceptuelle

### Sous-section 1 : Concepts de l'assurance maladie

**Assuré principal.** Personne titulaire du contrat, généralement un employé
affilié par son employeur. Elle ouvre les droits et répond de ses ayants droit.
Dans SantéSN, elle est la seule catégorie de bénéficiaire à disposer d'un compte
de connexion.

**Ayant droit.** Personne rattachée à un assuré principal par un lien de parenté
(conjoint, enfant) et couverte à ce titre. Elle consomme des soins en son nom,
possède sa propre carte, mais n'a **pas** d'accès autonome à la plateforme : son
dossier est géré par l'assuré principal. Cette asymétrie — une identité sans
compte — est le premier concept structurant du modèle.

**Plan de couverture.** Contrat définissant un **taux de couverture** (part
supportée par l'assureur, exprimée en pourcentage) et un éventuel **plafond
annuel**. Les ayants droit héritent du plan de leur assuré principal.

**Prise en charge.** Demande formulée pour un bénéficiaire, portant un motif et
une date, et prenant l'un de trois statuts : *en attente*, *validée*, *refusée*.
Elle constitue la **décision** de l'assureur, distincte de l'acte de soin.

**Part patient (ticket modérateur).** Fraction du coût restant due par le
bénéficiaire. Dans SantéSN, elle n'est pas une propriété du patient mais le
**résultat d'un calcul** : le taux du plan ne s'applique que si la prise en
charge rattachée à la consultation est au statut *validée* ; à défaut, le
patient règle l'intégralité. Ce choix est discuté au chapitre III.

**Tiers payant.** Mécanisme par lequel le prestataire est réglé directement par
l'assureur, le bénéficiaire n'avançant que sa part. C'est le modèle économique
que la plateforme outille.

**Prestataire conventionné.** Établissement — hôpital, clinique, cabinet,
pharmacie — lié à l'organisme par une convention. Le caractère *partenaire* et la
date de conventionnement sont des attributs du prestataire.

### Sous-section 2 : Concepts du numérique en santé

**E-santé.** Ensemble des usages des technologies de l'information appliqués à
la santé. On distingue utilement les systèmes qui traitent **le contenu du soin**
(dossier médical, aide au diagnostic) de ceux qui traitent **la circulation
administrative autour du soin** (droits, rendez-vous, facturation). SantéSN
relève exclusivement de la seconde catégorie — précision décisive pour son
périmètre.

**Dématérialisation de l'ordonnance.** Remplacement du support papier par un
enregistrement structuré. Une ordonnance dématérialisée n'est pas une image d'une
ordonnance : elle est composée de **lignes de prescription** exploitables
individuellement (médicament, dosage, posologie, durée, quantité).

**Code QR.** Code-barres bidimensionnel normalisé (ISO/IEC 18004), capable de
porter une charge utile de quelques centaines de caractères et lisible par tout
téléphone. Deux usages doivent être distingués : le QR **porteur de données**,
qui transporte l'information elle-même, et le QR **porteur de référence**, qui ne
transporte qu'un identifiant, l'information restant sur le serveur. Le second est
le seul acceptable pour des données de santé, puisqu'un code photographié
n'apprend alors rien à qui le détient.

**Contrôle d'accès fondé sur les rôles (RBAC).** Modèle où les permissions sont
attachées à des rôles, eux-mêmes attribués aux utilisateurs. Il s'oppose au
contrôle par liste d'accès individuelle. Sa vertu ici est la lisibilité : quatre
rôles, des règles énonçables en une phrase chacune.

**Cloisonnement et principe du besoin d'en connaître.** Un acteur n'accède qu'aux
données nécessaires à sa fonction. Appliqué à SantéSN : le pharmacien voit les
ordonnances non délivrées, jamais le diagnostic ; le médecin ne voit que les
dossiers de **ses propres** consultations ; l'administrateur voit l'acte et sa
facturation, jamais son contenu médical.

**Auditabilité.** Capacité à établir *a posteriori* qui a décidé quoi et quand.
Elle suppose une trace non modifiable, qui survive à la disparition de l'objet
tracé — sans quoi supprimer un objet effacerait la preuve de sa suppression.

## Section 2 : Revue de littérature et état de l'art

L'état de l'art se lit selon deux axes : la **couverture fonctionnelle** et le
**modèle de déploiement**.

### Les systèmes d'information hospitaliers libres

**OpenMRS** et **GNU Health** sont des plateformes libres de dossier médical
électronique, largement déployées dans les pays à ressources limitées. Elles
couvrent le dossier patient, les consultations, parfois la pharmacie et la
facturation. Leur logique est celle de l'**établissement** : elles informatisent
un hôpital.

**OpenEMR** poursuit un objectif comparable pour les structures ambulatoires.

*Limite au regard de notre problématique :* ces systèmes sont centrés sur le
producteur de soins. L'assureur y est au mieux un destinataire de facture. La
notion d'ayant droit sans compte, de plan de couverture et de statut de prise en
charge n'y est pas première.

### Les systèmes nationaux d'information sanitaire

**DHIS2**, développé par l'Université d'Oslo et déployé dans de nombreux
ministères de la santé africains, est un système d'agrégation de données
sanitaires à visée épidémiologique et de pilotage.

*Limite :* il travaille sur des agrégats, non sur le parcours individuel d'un
bénéficiaire. Il ne répond pas à la question du droit ouvert.

### Les plateformes de prise de rendez-vous

**Doctolib** et ses équivalents ont démontré l'acceptabilité de la prise de
rendez-vous en ligne à grande échelle.

*Limite :* le rendez-vous y est le produit, non un maillon d'une chaîne de
couverture. Aucune articulation avec un droit d'assurance.

### La prescription électronique

L'**Estonie** constitue la référence la plus citée en matière d'ordonnance
entièrement dématérialisée à l'échelle nationale : le patient se présente en
pharmacie avec sa pièce d'identité, la prescription étant récupérée dans un
registre central. La **France**, avec *Mon espace santé* et le dispositif
d'ordonnance numérique, poursuit une trajectoire comparable.

*Enseignement retenu :* ces dispositifs confirment l'hypothèse H3 — la sécurité
ne vient pas du support, mais du fait que le support ne porte qu'une référence.

*Limite de transposition :* ils supposent un identifiant national de santé et une
infrastructure centralisée que le cadre de cette étude n'offre pas. D'où le choix
d'un identifiant **porté par la carte de l'organisme** (`numero_carte`), et non
d'un identifiant national.

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

**La contribution revendiquée n'est pas technologique, elle est architecturale :**
placer la *couverture* — et non le *dossier* — au centre du modèle, et montrer
que ce déplacement suffit à unifier le parcours sans constituer de dossier
médical partagé.

---

# CHAPITRE II : CONTEXTE DE L'ÉTUDE

## Section 1 : Contexte général

### Sous-section 1 : Le système de santé et la couverture du risque maladie au Sénégal

Le financement de la santé au Sénégal combine plusieurs mécanismes :

- la **Couverture Maladie Universelle**, portée par une agence dédiée et
  s'appuyant largement sur les mutuelles de santé communautaires ;
- les **Institutions de Prévoyance Maladie (IPM)**, obligatoires pour les
  entreprises atteignant un seuil d'effectif, financées par cotisations
  employeur et salarié, et couvrant l'employé ainsi que sa famille ;
- les **assurances privées** et les **mutuelles professionnelles** ;
- le **paiement direct** par les ménages, qui demeure une part significative de
  la dépense de santé. **[À SOURCER : part du paiement direct dans la dépense
  courante de santé — source Comptes nationaux de la santé / OMS.]**

**[À SOURCER : effectifs couverts par les IPM, nombre de structures
conventionnées — source Agence de la CMU / ministère en charge de la santé.]**

Le cadre retenu pour cette étude est celui de l'**IPM**, pour trois raisons : la
population couverte y est identifiée et stable, la logique d'ayants droit y est
constitutive, et le tiers payant y est la norme.

### Sous-section 2 : La numérisation des services et ses contraintes locales

Trois contraintes ont directement orienté les choix techniques :

**L'accès à Internet passe majoritairement par le téléphone mobile.** La
plateforme devait donc être pleinement utilisable sur un écran étroit — non pas
« consultable », mais **opérationnelle** : un administrateur doit pouvoir
désactiver un compte depuis un téléphone. Cette exigence a produit un défaut réel
et sa correction, documentés au chapitre IV.

**La qualité de connexion est variable.** Le coût du premier chargement a été
mesuré et optimisé ; le détail figure au chapitre IV, section 2.

**Le papier ne disparaît pas.** Une ordonnance doit rester imprimable au format
A4, une carte de prise en charge au format carte bancaire. La dématérialisation
ne remplace pas le papier : elle le rend vérifiable.

## Section 2 : Contexte spécifique

### Sous-section 1 : L'organisme, son réseau et ses acteurs

Le système modélisé fait intervenir quatre rôles et un ensemble d'entités
conventionnées.

| Acteur | Rôle dans la chaîne | Accès à la plateforme |
|---|---|---|
| **Administrateur** | Gère comptes, référentiels, prises en charge, règlements | Complet, hors contenu médical |
| **Assuré principal** | Gère ses ayants droit, demande rendez-vous et prises en charge, consulte son reste à charge | Son foyer uniquement |
| **Médecin** | Traite les rendez-vous, enregistre consultations et ordonnances | Ses propres patients |
| **Pharmacien** | Scanne l'ordonnance, valide la délivrance | Ordonnances non délivrées |
| **Ayant droit** | Bénéficie des soins, porte une carte | **Aucun** — géré par l'assuré principal |
| **Prestataire** | Hôpital, clinique, cabinet, pharmacie conventionnés | Entité, non utilisateur |

### Sous-section 2 : Limites du fonctionnement actuel et expression du besoin

L'analyse du fonctionnement en vigueur fait apparaître six limites, chacune
traduite en besoin :

| # | Limite constatée | Besoin exprimé |
|---|---|---|
| L1 | L'ayant droit n'a pas d'identité opposable simple | Une carte de prise en charge par bénéficiaire |
| L2 | L'assuré ignore l'état de sa demande de prise en charge | Un suivi visible du statut de chaque demande |
| L3 | Le reste à charge est découvert après le soin | Un calcul automatique adossé au statut réel |
| L4 | L'ordonnance papier n'est ni vérifiable ni traçable | Une ordonnance structurée, vérifiée par QR |
| L5 | La double délivrance n'est pas détectable | Un état de délivrance opposable au pharmacien |
| L6 | Les décisions administratives ne laissent pas de trace | Un journal d'activité non modifiable |

Ces six besoins constituent le socle de la spécification fonctionnelle du
chapitre III.

---

# CHAPITRE III : CADRE MÉTHODOLOGIQUE ET CONCEPTION

## Section 1 : Spécification et modélisation du système

### Sous-section 1 : Spécification des besoins fonctionnels et non-fonctionnels

#### A. Besoins fonctionnels

**BF-1 — Authentification et gestion des rôles.** Connexion unique par
adresse électronique et mot de passe. Aucune inscription publique : les comptes
sont créés par l'administrateur. Le rôle est stocké en base, jamais choisi à la
connexion. Le premier administrateur est créé par un assistant d'initialisation
accessible uniquement tant qu'aucun administrateur n'existe. Limitation des
tentatives : cinq échecs entraînent un blocage temporaire de cinq minutes.

**BF-2 — Gestion des utilisateurs (administrateur).** Création, modification,
activation, désactivation, suppression, réinitialisation de mot de passe,
attribution de rôle, export de la liste filtrée. Garde-fous : un administrateur ne
peut ni modifier son propre rôle, ni se désactiver, ni se supprimer.

**BF-3 — Gestion des bénéficiaires.** Enregistrement des assurés principaux et de
leurs ayants droit, rattachement à un plan de couverture, attribution d'un numéro
de carte. Toute fiche métier disposant d'une connexion crée son compte
automatiquement ; les ayants droit n'en ont jamais.

**BF-4 — Référentiels.** Prestataires (avec géolocalisation), services médicaux
tarifés, plans de couverture.

**BF-5 — Rendez-vous.** La demande appartient au **bénéficiaire** ; le médecin
la traite (confirmation, annulation, clôture). Le médecin ne peut pas créer un
rendez-vous pour un patient de son choix — règle métier corrigée en cours de
projet, voir chapitre IV.

**BF-6 — Prises en charge.** Demande, examen, validation ou refus. Invariant :
le patient d'une consultation doit être celui de sa prise en charge.

**BF-7 — Consultations et ordonnances.** Le médecin enregistre diagnostic,
traitement et service rendu ; il saisit une ordonnance **structurée** en lignes
de prescription. Un code QR est généré par ordonnance.

**BF-8 — Délivrance en pharmacie.** Scan du QR, contrôle de l'état de
délivrance, validation, historique.

**BF-9 — Paiements.** Calcul automatique du montant total, de la part assurance
et de la part patient à l'enregistrement de la consultation ; suivi du
règlement.

**BF-10 — Rapports et exports.** Agrégats, graphiques, exports tableur et PDF.

**BF-11 — Traçabilité.** Journal des décisions administratives et des
suppressions, en lecture seule.

#### B. Besoins non fonctionnels

Les exigences non fonctionnelles ont été formulées de façon **mesurable**. C'est
ce qui permet, au chapitre IV, de dire si elles sont satisfaites plutôt que de
l'affirmer.

| Réf. | Exigence | Critère de vérification |
|---|---|---|
| BNF-1 | Cloisonnement par rôle vérifié côté serveur | Aucune route accessible hors rôle |
| BNF-2 | Aucune donnée médicale dans un code QR | Inspection de la charge utile |
| BNF-3 | Utilisable sur téléphone | Aucun débordement horizontal |
| BNF-4 | Lisibilité des textes | Contraste conforme WCAG AA (≥ 4,5:1) |
| BNF-5 | Navigation au clavier | Indicateur de focus visible partout |
| BNF-6 | Performance d'affichage | Coût du premier rendu mesuré |
| BNF-7 | Robustesse sur base vide | Aucun écran en erreur sans données |
| BNF-8 | Intégrité référentielle | Aucune violation de clé étrangère |
| BNF-9 | Maintenabilité | Suite de tests exécutée à chaque livraison |
| BNF-10 | Impression | Ordonnance A4, carte au format ISO 7810 ID-1 |

### Sous-section 2 : Étude et choix des méthodes de modélisation

Deux familles de méthodes étaient mobilisables.

**Merise** repose sur la séparation des niveaux conceptuel, logique et physique,
et sur le couple modèle conceptuel de données / modèle conceptuel de traitements.
Elle reste très employée dans l'enseignement et l'administration francophones, et
excelle à décrire une base de données relationnelle.

**UML** propose un ensemble de diagrammes couvrant à la fois la structure
(classes, objets), le comportement (cas d'utilisation, états, activités) et les
interactions (séquence, communication).

**Choix retenu : UML**, pour trois raisons.

1. **La dimension comportementale est ici déterminante.** Le cœur du sujet n'est
   pas la structure des données — elle est simple — mais les **transitions
   d'état** : une prise en charge qui devient validée, un rendez-vous qui devient
   confirmé, une ordonnance qui devient délivrée. Le diagramme d'états-transitions
   d'UML exprime cela directement ; Merise ne dispose pas d'équivalent aussi
   naturel.

2. **Le système est défini par ses acteurs.** Quatre rôles aux permissions
   disjointes : le diagramme de cas d'utilisation constitue à lui seul une
   spécification lisible par un non-informaticien.

3. **Correspondance directe avec la technologie retenue.** Le cadriciel Django
   suit une logique orientée objet où une classe de modèle devient une table.
   Le diagramme de classes UML se traduit sans transposition intermédiaire.

*Réserve assumée.* UML décrit moins finement que Merise les dépendances
fonctionnelles et la normalisation. Cette réserve est levée par le fait que
l'ORM du cadriciel garantit les formes normales usuelles dès lors que le modèle
objet est correct.

### Sous-section 3 : Modélisation

#### A. Diagramme de cas d'utilisation (description)

**Acteur Administrateur** — Gérer les utilisateurs · Gérer les bénéficiaires ·
Gérer les référentiels · Statuer sur les prises en charge · Suivre les paiements ·
Consulter les rapports · Consulter le journal · Imprimer une carte.

**Acteur Assuré** — Gérer son profil · Gérer ses ayants droit · Demander un
rendez-vous · Suivre ses prises en charge · Consulter ses ordonnances ·
Consulter son historique et son reste à charge · Localiser un prestataire proche.

**Acteur Médecin** — Consulter son agenda · Traiter un rendez-vous ·
Enregistrer une consultation · Rédiger une ordonnance structurée · Consulter la
fiche de ses patients.

**Acteur Pharmacien** — Scanner une ordonnance · Valider une délivrance ·
Consulter l'historique des délivrances.

*Relations notables :* « Enregistrer une consultation » **inclut** « Calculer le
paiement » ; « Valider une délivrance » **étend** « Scanner une ordonnance ».

#### B. Diagramme de classes (description)

Le modèle comporte **17 entités persistantes**. Les relations structurantes :

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

**Trois décisions de modélisation méritent d'être défendues en soutenance.**

**1. `Patient.user` est facultatif et en `SET_NULL`.** C'est la traduction directe
de l'hypothèse H1. Un ayant droit est un `Patient` sans `User`. Corollaire
important : supprimer un compte ne supprime **pas** la fiche du bénéficiaire —
les droits survivent à l'accès, ce qui est le comportement attendu, mais impose
de traiter explicitement les fiches lors d'une purge.

**2. `Paiement` est en relation 1–1 avec `Consultation`, et tous ses montants
sont dérivés.** Le paiement n'est pas saisi : il est **calculé**. Le taux
appliqué provient du plan du patient **uniquement si** la prise en charge liée est
au statut *validée* ; sinon, le patient supporte 100 %. C'est l'hypothèse H2
inscrite dans le code.

**3. `JournalActivite` ne comporte aucune clé étrangère vers l'objet tracé.**
Une clé en cascade effacerait l'entrée en même temps que l'objet supprimé — or
c'est précisément la suppression qu'il s'agit de conserver. L'objet et l'auteur
sont donc enregistrés sous forme de **texte figé**, à côté d'une clé `SET_NULL`
vers l'auteur. Supprimer le compte d'un administrateur n'efface pas la trace de
ses décisions.

#### C. Diagrammes d'états-transitions

**Rendez-vous**

```
        [demande de l'assuré]
                 │
                 ▼
            ┌─ DEMANDE ─┐
            │           │
      (médecin)     (médecin/assuré)
            │           │
            ▼           ▼
        CONFIRME ──► ANNULE
            │
       (médecin)
            ▼
        TERMINE
```

**Prise en charge**

```
   en_attente ──(administrateur)──► validee   → couverture au taux du plan
        │
        └───────(administrateur)──► refusee   → 100 % à la charge du patient
```

**Ordonnance**

```
   créée par le médecin ──► non délivrée ──(pharmacien : scan + validation)──► délivrée
```

L'état *délivrée* est **terminal** : c'est lui qui rend la double délivrance
détectable, et qui répond au besoin L5.

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

Le point à souligner : **le QR ne porte aucun droit**. Il n'encode qu'une
référence ; c'est le contrôle de rôle côté serveur qui autorise. Un code
photographié par un tiers ne lui apprend rien.

## Section 2 : Implémentation et évaluation des modèles

### Sous-section 1 : Choix technologiques et justification

| Couche | Technologie | Version | Justification |
|---|---|---|---|
| Langage | Python | 3.14 | Lisibilité, écosystème, courbe d'apprentissage |
| Cadriciel | Django | 5.2.16 | ORM, authentification, administration, sécurité par défaut |
| Base (développement) | SQLite | — | Aucune installation, fichier unique |
| Base (production) | PostgreSQL | via `psycopg2-binary` | Concurrence, intégrité, montée en charge |
| Configuration | `python-decouple` | 3.8 | Secrets hors du dépôt (`.env`) |
| Codes QR | `qrcode` | 8.2 | Génération SVG sans dépendance graphique |
| Export tableur | `openpyxl` | 3.1.5 | Fichiers `.xlsx` natifs |
| Export PDF | `reportlab` | 4.4.10 | Documents mis en forme |
| Graphiques | Chart.js | CDN + SRI | Rendu client, aucune dépendance serveur |
| Cartographie | Leaflet + OpenStreetMap | CDN | Fonds de carte libres |
| Géocodage | Nominatim | via relais serveur | Voir justification ci-dessous |

**Pourquoi Django plutôt qu'une architecture découplée (API + client JavaScript) ?**
Trois arguments. Le rendu côté serveur supprime une couche entière de
synchronisation d'état pour une application essentiellement transactionnelle.
La sécurité — protection CSRF, hachage des mots de passe, échappement automatique
des gabarits — est active par défaut plutôt qu'à assembler. Enfin, une page rendue
côté serveur reste utilisable sur une connexion médiocre, ce qui rejoint la
contrainte du chapitre II.

**Pourquoi une application unique ?** Le cahier des charges l'impose. Toute la
logique métier vit dans `Plateform_medicale` ; `config/` ne contient que la
configuration. Une application `accounts` initialement séparée a été fusionnée
pour respecter cette contrainte.

**Pourquoi un relais serveur pour le géocodage ?** L'appel direct au service
Nominatim depuis le navigateur s'est révélé peu fiable à l'usage : le cache du
réseau de diffusion ne fait pas varier ses réponses selon l'origine appelante,
d'où un en-tête d'autorisation présent de façon intermittente ; par ailleurs, un
appel depuis le navigateur ne peut pas porter d'agent utilisateur applicatif
identifiant, ce que la politique d'usage du service attend. La recherche passe
donc par une vue serveur dédiée, qui interroge le service avec un agent
identifié, restreint la recherche au Sénégal et ne renvoie qu'un JSON minimal.

### Sous-section 2 : Description de l'expérimentation

Le protocole d'évaluation comporte **cinq dispositifs**, choisis pour être
reproductibles.

**E1 — Tests automatisés.** Suite exécutée par le lanceur du cadriciel, sur base
de test isolée. Couverture : permissions, redirections, garde-fous anti-blocage,
invariants de modèle, absence de régression sur les libellés et les icônes.
**569 tests, 74 classes.**

**E2 — Matrice de permissions.** Énumération automatique des routes déclarées,
puis appel de chacune sous **cinq profils** (anonyme, assuré, médecin,
pharmacien, administrateur). Objectif : détecter toute route accessible hors de
son rôle. **98 routes** déclarées.

**E3 — Mesure en navigateur réel.** Pilotage d'un navigateur sans interface par
le protocole Chrome DevTools. Relevés : rapports de contraste calculés,
rectangles englobants aux largeurs 1440 / 900 / 360 px, styles effectifs après
navigation clavier réelle, nombre de requêtes SQL par écran.

*Précision méthodologique.* La navigation clavier doit être simulée par
**événements de touche réels**. Un appel programmatique de mise au focus ne
déclenche pas le sélecteur `:focus-visible` : une première mesure a conclu à tort
à l'absence d'indicateur de focus.

**E4 — Épreuve de la base vide.** Toutes les routes sans paramètre sont appelées
sur une base réinitialisée. C'est le cas limite où une moyenne sur zéro élément
ou un graphique sans série provoque une erreur — invisible tant que la base est
peuplée.

**E5 — Contrôle d'intégrité.** Vérification des clés étrangères et de la
cohérence physique de la base après toute opération de masse.

---

# CHAPITRE IV : CADRE ANALYTIQUE ET RÉALISATION

## Section 1 : Présentation et traitement des données

### Sous-section 1 : Description des données (sources, structure, qualité)

#### A. Sources

**Toutes les données de la plateforme proviennent d'une saisie humaine
authentifiée.** Aucun jeu de données externe n'est importé, aucune donnée
médicale n'est générée. Ce point est méthodologiquement essentiel : un système
de santé ne peut être éprouvé sur des prescriptions fictives sans risque de
confusion entre démonstration et réalité.

Quatre origines seulement :

1. l'administrateur, pour les comptes, référentiels et décisions ;
2. l'assuré, pour son profil, ses ayants droit et ses demandes ;
3. le médecin, pour les consultations et les ordonnances ;
4. le pharmacien, pour les délivrances.

Une cinquième origine est **dérivée** : les montants du paiement, calculés et
jamais saisis.

#### B. Structure

| Famille | Entités | Volumétrie attendue |
|---|---|---|
| Identité et accès | `User`, `TentativeConnexion` | Croissance lente |
| Bénéficiaires | `Patient`, `PlanCouverture` | Croissance lente |
| Réseau de soins | `Prestataire`, `Medecin`, `Pharmacien`, `ServiceMedical` | Référentiel stable |
| Droits | `PriseEnCharge` | Croissance moyenne |
| Parcours | `RendezVous`, `Consultation` | **Croissance forte** |
| Prescription | `Ordonnance`, `LigneOrdonnance`, `Delivrance` | **Croissance forte** |
| Financier | `Paiement` | Croissance forte |
| Support | `Notification`, `JournalActivite` | Croissance moyenne |

#### C. Qualité — trois mécanismes de garantie

**1. Les invariants vivent dans les modèles, pas dans les formulaires.**
L'invariant central — *le patient d'une consultation est celui de sa prise en
charge* — était initialement implémenté dans un formulaire. Il était donc
vérifié seulement à la création et seulement par ce formulaire. Deux chemins le
contournaient : la réattribution d'une prise en charge déjà pourvue de
consultations, et l'interface d'administration native, qui n'utilise pas les
formulaires de l'application.

Déplacé dans les méthodes de validation des modèles, l'invariant est désormais
rencontré par **tout** formulaire, application comme administration native. La
réattribution reste permise tant qu'aucune consultation n'est rattachée :
corriger une erreur de saisie est légitime, déplacer des soins déjà enregistrés
ne l'est pas.

**2. La pagination impose un tri.** Un ensemble de résultats paginé sans ordre
explicite produit une répartition instable : un élément peut apparaître deux fois
ou disparaître. Deux vues en manquaient ; un test couvre désormais la règle.

**3. Les valeurs stockées et les libellés affichés sont strictement séparés.**
Les filtres et les requêtes utilisent toujours la valeur stockée, jamais le
libellé accentué. Un piège avéré : une table de couleurs de graphique indexée par
libellé faisait repasser les graphiques en gris à la moindre reformulation, **sans
aucune erreur visible**. Un test la verrouille désormais.

### Sous-section 2 : Traitement, cycle de vie et rétention des données

**Principe directeur : rien de médical ne disparaît automatiquement.**
Consultations, ordonnances, lignes de prescription, délivrances, prises en charge,
paiements et journal ne font l'objet d'aucune purge programmée. La suppression
est toujours une décision humaine, explicite et confirmée.

**Suppressions en cascade maîtrisées.** Les règles ont été choisies entité par
entité. Les liens vers un compte sont en `SET_NULL` — la disparition d'un accès
n'emporte pas la disparition des droits. Les liens de composition (une ligne
appartient à son ordonnance, un paiement à sa consultation) sont en `CASCADE`.

**Symétrie de la suppression.** Supprimer une fiche métier disposant d'un compte
désactive ce compte. Sans cette symétrie, un assuré supprimé conservait un accès
actif et pouvait se recréer une fiche par son propre espace.

**Opération de remise à zéro du 17 août 2026.** Préalablement à la recette, la
base de travail a été purgée des données de peuplement accumulées. L'opération a
été conduite selon un protocole en cinq temps : sauvegarde préalable, inventaire
en lecture seule distinguant les données saisies des données générées, simulation
au moyen du collecteur de dépendances du cadriciel, exécution en **transaction
unique**, puis contrôle d'intégrité. **277 objets supprimés, 0 violation de clé
étrangère.**

Deux enseignements en ont été tirés, tous deux transposables :

- **Le marqueur fiable d'une donnée générée n'est pas son nom, mais son
  horodatage.** Trente comptes créés en onze secondes ne peuvent pas provenir
  d'une saisie manuelle.
- **La documentation du projet affirmait que ces comptes avaient été supprimés.
  Ils ne l'étaient pas.** Une affirmation portant sur le contenu d'une base se
  vérifie par une requête, jamais par la mémoire d'une session antérieure.

## Section 2 : Réalisation et analyse des fonctionnalités

### Sous-section 1 : Implémentation des interfaces utilisateur

#### A. Architecture de l'interface

Un **cadre unique** de tableau de bord — barre latérale et barre supérieure —
est partagé par les quatre rôles, la navigation étant conditionnée par le rôle
courant. Ce choix évite quatre interfaces à maintenir en parallèle et garantit
qu'une correction ergonomique bénéficie à tous.

**77 gabarits** composent l'interface. Les pages publiques (page d'accueil,
écrans de connexion) disposent de feuilles de style autonomes, avec les mêmes
jetons de couleur.

#### B. Identité visuelle

Palette turquoise / marine / terracotta, typographies Manrope et Public Sans.
Emblème « Croix-Pouls » : une croix médicale traversée par un tracé de pouls,
produit par un unique composant réutilisé partout — il n'existe pas deux versions
du logo à maintenir.

**Aucun émoji dans l'application.** Toutes les icônes sont des tracés vectoriels
hérités de la couleur du conteneur.

*Enseignement de conception :* **une icône doit être reconnue, pas seulement
décrite.** L'icône « Paramètres » avait d'abord été dessinée comme un cercle
entouré de rayons — un engrenage stylisé sur le papier, **un soleil à l'écran**.
Le test qui la couvrait cherchait un cercle, que le soleil possédait aussi : il ne
pouvait pas voir l'erreur. Il vérifie désormais ce qui *sépare* les deux formes.

#### C. Adaptation aux petits écrans

**Défaut avéré et corrigé.** Sur les listes d'administration, un tableau de neuf
colonnes occupait **1063 px dans une carte de 356 px**. La colonne « Actions »,
placée en fin de ligne, sortait de l'écran : il devenait impossible de modifier ou
de désactiver un compte depuis un téléphone.

Correction : masquage des colonnes secondaires sous 900 px, la colonne Actions
n'étant **jamais** masquable ; disposition verticale des boutons d'action ; mise
en page tabulaire à largeur fixe. **Résultat mesuré : aucun débordement sur 12
pages × 3 largeurs.**

Les listes conservent leur forme tabulaire — c'est ce qu'on vient y chercher,
comparer des lignes. Le mode carte reste réservé aux écrans de l'assuré.

#### D. Thème sombre

Posé par un attribut sur la racine du document, écrit par un script en tête de
page pour éviter tout clignotement, et conservé dans le stockage local. Seuls les
jetons de couleur changent ; aucune règle de mise en page n'est dupliquée.

*Règle tirée de l'expérience :* **un jeton, un rôle.** Confondre un jeton de
couleur de *surface* avec un jeton de couleur de *texte* est indolore en thème
unique et fatal dès qu'un second thème existe — cela a produit une traînée
blanche en travers du bandeau et des boutons illisibles au premier essai.

#### E. Documents imprimables

**Ordonnance A4** : en-tête praticien et prestataire, bloc patient, tableau des
lignes de prescription, code QR, zone de signature.

**Carte de prise en charge** au format ISO 7810 ID-1 — le format d'une carte
bancaire — recto-verso, avec code QR.

*Défaut avéré, à ne pas réintroduire.* La bibliothèque de génération produit ses
modules sous forme d'éléments **préfixés par un espace de noms**. Insérés dans une
page HTML, ces préfixes ne sont pas résolus par l'analyseur : **les codes QR
sortaient en carré blanc**. Le défaut affectait aussi les QR d'ordonnances,
invisibles depuis l'origine du projet. Un utilitaire commun retire désormais le
préfixe. Corollaire : le tracé n'ayant pas de zone d'affichage déclarée, sa taille
se règle **à la génération**, jamais en feuille de style — une largeur imposée en
CSS revide le code.

#### F. Accessibilité

Indicateur de focus clavier sur tous les éléments interactifs, hiérarchie de
titres respectée, aucun élément interactif dépourvu de nom accessible, contrastes
conformes.

*Défaut avéré et corrigé.* En thème sombre, les champs de formulaire n'imposaient
pas de couleur de texte : **le texte saisi était invisible**, à un rapport de
contraste de 1,07:1. Après correction, **16,44:1 en thème clair et 14,42:1 en
thème sombre**.

### Sous-section 2 : Synthèse et discussion des résultats

#### A. Métriques de réalisation

| Indicateur | Valeur |
|---|---:|
| Entités persistantes | 17 |
| Migrations de schéma | 14 |
| Routes déclarées | 98 |
| Vues | 127 |
| Formulaires | 23 |
| Gabarits | 77 |
| Rôles | 4 |
| Lignes — modèles / vues / formulaires | 871 / 3 660 / 615 |
| Lignes — tests | 6 365 |
| **Tests automatisés** | **569** (74 classes) |

#### B. Résultats de l'évaluation

| Réf. | Exigence | Résultat mesuré | Statut |
|---|---|---|:---:|
| BNF-1 | Cloisonnement par rôle | 98 routes × 5 profils, aucune route ouverte hors rôle | ✅ |
| BNF-2 | Aucune donnée médicale dans le QR | Référence seule ; droits vérifiés côté serveur | ✅ |
| BNF-3 | Usage sur téléphone | Aucun débordement, 12 pages × 3 largeurs | ✅ |
| BNF-4 | Lisibilité | 16,44:1 (clair) · 14,42:1 (sombre) | ✅ |
| BNF-5 | Navigation clavier | Focus visible, vérifié par touches réelles | ✅ |
| BNF-6 | Performance | Premier rendu **2 452 ms → 1 040 ms** | ✅ |
| BNF-7 | Robustesse base vide | **43 / 43** routes administrateur à 200 | ✅ |
| BNF-8 | Intégrité | 0 violation de clé étrangère | ✅ |
| BNF-9 | Maintenabilité | **569 / 569** tests au vert | ✅ |
| BNF-10 | Impression | A4 et ISO 7810 ID-1 conformes | ✅ |

Sur la performance : le gain provient du chargement **non bloquant** de la
feuille de polices distante, qui immobilisait 1 342 ms du premier rendu. En cache
chaud, le coût était déjà d'environ 150 ms — le défaut ne frappait donc que la
première visite, c'est-à-dire celle qui compte, et qui dure plus longtemps sur une
connexion mobile.

#### C. Confrontation aux hypothèses

**H1 — Bénéficiaire distinct du compte : validée.** Le modèle porte des ayants
droit disposant d'une carte et de droits sans aucun accès. La conséquence
imprévue mérite d'être signalée : les relations en `SET_NULL` font qu'une purge de
comptes laisse les fiches en place. Ce n'est pas un défaut du modèle, c'est une
propriété qu'il faut connaître — elle a été rencontrée lors de la remise à zéro.

**H2 — Causalité tarifaire : validée.** La part patient est calculée à partir du
statut réel de la prise en charge. Une demande en attente ou refusée n'ouvre
aucune couverture. La règle est testée et visible côté assuré.

**H3 — QR non porteur : validée.** Le code n'encode qu'une référence. La portée
diffère par rôle : le pharmacien ne voit que les ordonnances **non délivrées**, le
médecin uniquement celles de **ses propres** consultations. Le diagnostic n'est
jamais exposé.

**H4 — Trace sélective : validée, mais c'est l'hypothèse la plus discutable.**
Le journal couvre les décisions administratives et les suppressions — 17 points
d'appel — à l'exclusion des connexions, des actes de soin et des changements de
statut de rendez-vous. Le raisonnement : une consultation porte déjà son médecin
et sa date, les réécrire ne les apprendrait pas deux fois. **La limite honnête**
est qu'un audit de sécurité complet exigerait la trace des accès en **lecture** aux
données médicales — qui n'est pas implémentée. L'hypothèse est validée pour
l'auditabilité administrative, non pour l'auditabilité médicale.

#### D. Discussion critique — limites du travail

L'honnêteté sur les limites est ce qui distingue un travail de recherche d'une
présentation commerciale. Cinq limites sont assumées.

**1. Une ordonnance ne peut pas être corrigée.** Il n'existe pas de vue de
modification : seulement la création. Un médecin qui se trompe de dosage n'a
aucun recours dans l'application. Cette absence est **délibérée** — elle demande
une décision métier qui n'a pas été prise : qui peut corriger, et une ordonnance
déjà délivrée peut-elle encore changer ? Pour une démonstration, l'absence ne se
voit pas ; pour un usage réel en santé, **c'est le premier chantier**.

**2. La feuille de style principale est trop volumineuse.** Environ 4 850 lignes
insérées dans un gabarit unique. C'est le principal frein technique restant, et
c'est de cette concentration que sont nés trois des défauts de thème sombre
rencontrés.

**3. Aucun service d'envoi de courriel n'est configuré.** Les mots de passe
générés sont affichés une seule fois à l'écran. Acceptable en démonstration,
insuffisant en exploitation.

**4. Aucun règlement en ligne.** Le périmètre exclut explicitement toute
intégration de paiement mobile et toute transaction, même simulée. La plateforme
enregistre un règlement constaté ; elle ne l'encaisse pas.

**5. La typographie n'a été jugée que par la mesure.** Tailles et graisses ont
été relevées et harmonisées, mais aucune revue visuelle écran par écran n'a été
conduite.

#### E. Enseignement méthodologique transversal

Le résultat le plus instructif de ce travail n'est pas une fonctionnalité, c'est
une observation sur la vérification.

**Aucun des défauts réels n'a été trouvé en relisant le code.** Codes QR
invisibles depuis l'origine, texte saisi illisible en thème sombre, colonne
d'actions hors écran, requêtes redondantes, icône méconnaissable : tous ont été
révélés par la mesure ou par le rendu. Symétriquement, plusieurs sondes ont
produit des **faux positifs convaincants** qu'il a fallu réfuter — un indicateur
de focus jugé absent parce que la mise au focus programmatique ne déclenche pas
le même sélecteur qu'une frappe réelle.

Une illustration finale, survenue pendant la rédaction de ce document : la suite
de tests était déclarée « complète » à 543 tests. Le recoupement entre les classes
**définies** et les classes **effectivement exécutées** a montré que deux classes
— les deux plus récentes — n'avaient jamais été lancées. Le total réel est de
**569 tests**, tous au vert. La conclusion ne changeait pas ; **sa preuve, si**.

### Sous-section 3 : Recommandations

#### Court terme — avant toute mise en service réelle

**R1. Implémenter la correction d'ordonnance.** Priorité absolue. Une application
médicale où une prescription erronée ne peut pas être rectifiée n'est pas
livrable à un établissement de santé. Décisions à trancher au préalable : périmètre
d'habilitation, et sort d'une ordonnance déjà délivrée — la piste recommandée est
l'**annulation avec motif suivie d'une réémission**, qui préserve la trace, plutôt
que la modification en place.

**R2. Configurer un service d'envoi de courriel** pour la transmission des accès
et la réinitialisation des mots de passe.

**R3. Basculer en PostgreSQL.** Le pilote est déjà déclaré ; SQLite ne convient
pas à des écritures concurrentes.

#### Moyen terme

**R4. Extraire la feuille de style** du gabarit principal vers des fichiers
statiques versionnés.

**R5. Journaliser les accès en lecture aux données médicales**, afin de lever la
limite identifiée sur l'hypothèse H4.

**R6. Adosser les lignes de prescription à un référentiel de médicaments**
— la saisie est aujourd'hui libre, ce qui autorise les variantes
orthographiques et interdit tout contrôle d'interaction.

**R7. Conduire une revue visuelle écran par écran** de la typographie.

#### Long terme

**R8. Ouvrir une interface d'échange** avec les systèmes des prestataires, en
s'appuyant sur un standard d'interopérabilité en santé plutôt que sur un format
propriétaire.

**R9. Étudier le rôle « Praticien »**, prévu mais volontairement non créé : un
rôle sans tableau de bord produirait des comptes sans destination après connexion.

**R10. Instruire la conformité réglementaire** au regard du cadre applicable à
la protection des données personnelles de santé au Sénégal.

---

# Conclusion générale

Ce travail est parti d'une tension : la chaîne de prise en charge médicale exige
de la continuité, tandis que le secret médical exige de la rétention. L'hypothèse
directrice était qu'on pouvait tenir les deux en déplaçant le centre du modèle —
en plaçant la **couverture** au cœur du système plutôt que le **dossier**.

Ce déplacement s'est révélé fécond. Il a permis de représenter un ayant droit
comme une identité sans accès, de faire du reste à charge un calcul plutôt qu'une
déclaration, et de dématérialiser l'ordonnance au moyen d'un code qui ne transporte
rien — la vérification restant entière du côté du serveur. Les quatre hypothèses
sont validées, la quatrième avec une réserve explicite : l'auditabilité obtenue
est administrative, non médicale.

Sur le plan de la réalisation, la plateforme couvre les quatre rôles de bout en
bout et satisfait les dix exigences non fonctionnelles formulées, chacune vérifiée
par une mesure reproductible plutôt que par une appréciation.

Il serait malhonnête de conclure que SantéSN est prêt pour l'exploitation. Il lui
manque la correction d'ordonnance, et cette absence n'est pas un détail
d'ergonomie : c'est une exigence de sécurité du patient. La distinction que ce
mémoire revendique est donc précise — **le système est démontrable aujourd'hui,
exploitable après ce chantier**.

Enfin, la contribution la plus transférable de ce travail n'est peut-être pas
l'application elle-même, mais la discipline de vérification qui l'a produite.
Chaque défaut réellement corrigé l'a été parce qu'une valeur a été relevée plutôt
qu'un code relu. C'est un enseignement que l'on peut emporter bien au-delà du
domaine de l'assurance santé.

---

# Webographie

**Cadriciel et bibliothèques**

- Documentation Django — https://docs.djangoproject.com/
- Django REST et sécurité, guide « Security in Django » — https://docs.djangoproject.com/en/stable/topics/security/
- Bibliothèque `qrcode` (Python) — https://pypi.org/project/qrcode/
- `openpyxl`, lecture-écriture de fichiers Excel — https://openpyxl.readthedocs.io/
- ReportLab, génération de PDF — https://docs.reportlab.com/
- `python-decouple` — https://pypi.org/project/python-decouple/
- Chart.js — https://www.chartjs.org/docs/latest/
- Leaflet — https://leafletjs.com/reference.html
- OpenStreetMap et politique d'usage de Nominatim — https://operations.osmfoundation.org/policies/nominatim/

**Normes et référentiels**

- W3C — Web Content Accessibility Guidelines (WCAG) 2.2 — https://www.w3.org/TR/WCAG22/
- W3C — Accessible Rich Internet Applications (WAI-ARIA) — https://www.w3.org/WAI/standards-guidelines/aria/
- ISO/IEC 18004 — Code à barres bidimensionnel QR Code — https://www.iso.org/standard/83389.html
- ISO/IEC 7810 — Cartes d'identification, caractéristiques physiques — https://www.iso.org/standard/70483.html
- HL7 FHIR — standard d'interopérabilité en santé — https://www.hl7.org/fhir/

**Systèmes de santé et couverture**

- Organisation mondiale de la santé — Couverture sanitaire universelle — https://www.who.int/health-topics/universal-health-coverage
- Agence nationale de la Statistique et de la Démographie (Sénégal) — https://www.ansd.sn/
- Agence de la Couverture Maladie Universelle (Sénégal) — **[À COMPLÉTER : adresse officielle en vigueur]**

**Solutions comparées (état de l'art)**

- OpenMRS — https://openmrs.org/
- GNU Health — https://www.gnuhealth.org/
- OpenEMR — https://www.open-emr.org/
- DHIS2 — https://dhis2.org/
- e-Estonia, prescription électronique — https://e-estonia.com/solutions/healthcare/e-prescription/
- Mon espace santé (France) — https://www.monespacesante.fr/

---

*Document établi le 17 août 2026. Toutes les métriques ont été relevées sur le
code source à cette date et sont reproductibles par les commandes décrites au
chapitre III, section 2, sous-section 2.*
