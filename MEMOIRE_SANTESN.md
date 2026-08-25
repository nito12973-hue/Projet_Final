# RÉPUBLIQUE DU SÉNÉGAL
**Un Peuple — Un But — Une Foi**
**MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR, DE LA RECHERCHE ET DE L'INNOVATION**

---

### **UNIVERSITÉ CHEIKH ANTA DIOP DE DAKAR (UCAD)**
### **ÉCOLE SUPÉRIEURE POLYTECHNIQUE (ESP)**
#### **DÉPARTEMENT GÉNIE INFORMATIQUE & TÉLÉCOMMUNICATIONS**

---

# **MÉMOIRE DE FIN D'ÉTUDES**
### Pour l'obtention du Diplôme d'Ingénieur de Conception / Master en Génie Logiciel

---

## **SUJET :**
# **CONCEPTION ET RÉALISATION D'UNE PLATEFORME WEB SÉCURISÉE DE GESTION INTÉGRÉE DU TIERS PAYANT ET DE DÉMATÉRIALISATION DU PARCOURS DE SOINS : CAS DE LA PLATEFORME SantéSN**

---

**Présenté et soutenu par :**  
Monsieur l'Impétrant

**Sous la direction de :**
* **Encadrant Universitaire :** Professeur / Enseignant-Chercheur (UCAD / ESP)
* **Encadrant Professionnel :** Ingénieur Référent / Chef de Projet IPM

**Membres du Jury :**
* **Président :** Professeur Titulaire des Universités
* **Rapporteur :** Maître de Conférences
* **Examinateur :** Ingénieur Système & Sécurité

**Année Académique :** 2025 – 2026

---

## DÉDICACES

*À mes chers parents,*  
Qui ont consenti d'incommensurables sacrifices pour mon éducation et m'ont constamment inculqué les valeurs d'excellence, de rigueur, de persévérance et d'humilité. Que ce travail soit le modeste témoignage de ma profonde et éternelle gratitude.

*À mes frères et sœurs,*  
Pour leur soutien indéfectible, leur constante bienveillance et leurs encouragements tout au long de mon cursus académique.

*À tous mes enseignants et formateurs,*  
Qui ont façonné mon esprit critique et m'ont transmis la passion des sciences du numérique et de l'ingénierie logicielle.

*À toute la communauté médicale et mutualiste du Sénégal,*  
Qui œuvre chaque jour avec dévouement pour l'amélioration de la santé et du bien-être des populations.

---

## REMERCIEMENTS

Au terme de ce travail de fin d'études, je tiens à exprimer ma profonde reconnaissance à toutes les personnes qui ont contribué, de près ou de loin, à sa réussite.

J'adresse mes plus vifs remerciements à mon **encadrant universitaire**, pour sa disponibilité constante, ses orientations méthodologiques avisées et la rigueur scientifique qu'il a su m'inculquer tout au long de ce projet.

J'exprime ma sincère gratitude aux **responsables des Institutions de Prévoyance Maladie (IPM)**, aux **médecins**, aux **pharmaciens d'officine** et aux **gestionnaires de cliniques** du Sénégal qui ont accepté de m'accorder des entretiens précieux, d'ouvrir leurs portes pour l'analyse des processus métiers et de tester les premières versions de la plateforme.

Mes remerciements s'adressent également à l'ensemble du **corps professoral et administratif de l'École Supérieure Polytechnique**, pour la qualité de l'encadrement académique et humain dispensé tout au long de mon parcours.

Enfin, je remercie les membres du jury qui me font l'insigne honneur d'évaluer ce travail de mémoire.

---

## RÉSUMÉ

Au Sénégal, la couverture sanitaire repose en grande partie sur les Institutions de Prévoyance Maladie (IPM), les mutuelles de santé et les compagnies d'assurance privées à travers le mécanisme du tiers payant. Cependant, la gestion opérationnelle de ce système demeure majoritairement tributaire de supports papier vulnérables (bons de prise en charge volants, ordonnances manuscrites, factures physiques). Cet archaïsme engendre des délais de remboursement critiques de 3 à 6 mois pour les prestataires de soins, une opacité dans le suivi des plafonds de couverture annuels des foyers, ainsi qu'une prolifération des fraudes à l'ordonnance et des doublons de facturation qui menacent l'équilibre financier des régimes mutualistes.

Ce mémoire présente la conception, le développement et la validation d'une solution numérique globale, résiliente et sécurisée : la plateforme **SantéSN**. Conçue selon une architecture modulaire en couches avec le framework Django/Python, SantéSN unifie en temps réel les quatre acteurs cardinaux du parcours de soins : les Administrateurs d'IPM, les Médecins prescripteurs, les Pharmaciens d'officine et les Patients assurés avec leurs ayants droit.

Le système intègre une carte d'assuré physique et dématérialisée normalisée ISO 7810 ID-1 munie d'un QR Code dynamique vectoriel à lecture sécurisée, une gestion en temps réel des plafonds budgétaires annuels glissants, la certification numérique des ordonnances médicales avec cachet officiel anti-fraude, un scanner optique pour les pharmaciens empêchant toute double délivrance, ainsi qu'une cartographie interactive géolocalisée (GIS) des prestataires conventionnés. 

La robustesse logicielle de la plateforme est attestée par une suite de 107 tests automatisés validant le cloisonnement strict des accès par rôle (RBAC), la protection des données de santé conformément aux dispositions de la Commission de Protection des Données Personnelles (CDP) du Sénégal, et l'optimisation des performances sur les réseaux à bande passante contrainte.

**Mots-clés :** Tiers Payant, Assurance Santé, Dématérialisation, Django, Architecture Logicielle, QR Code Sécurisé, RBAC, IPM, Sénégal, e-Santé.

---

## ABSTRACT

In Senegal, healthcare coverage relies heavily on Health Insurance Institutions (Institutions de Prévoyance Maladie - IPM), mutual funds, and private insurers through the third-party payment system. However, the operational management of this ecosystem remains predominantly bound to vulnerable paper-based workflows (manual vouchers, handwritten prescriptions, physical invoices). This outdated approach causes severe reimbursement delays of 3 to 6 months for healthcare providers, lack of visibility into households' annual coverage ceilings, and widespread fraudulent reuse of prescriptions that jeopardizes the financial sustainability of mutual healthcare funds.

This thesis presents the design, software development, and formal evaluation of an enterprise-grade, secure digital healthcare platform: **SantéSN**. Built upon a modular Python/Django architecture, SantéSN seamlessly interconnects the four core stakeholders of the medical reimbursement cycle: Health Insurance Administrators, Medical Doctors, Community Pharmacists, and Insured Patients along with their dependents.

Key innovations include an ISO 7810 ID-1 standardized physical and digital insurance card with vector-based dynamic QR verification, real-time tracking and automated capping of annual family expenditure ceilings, digital prescription certification with anti-fraud official stamps, optical webcam-based pharmacy verification preventing duplicate dispensing, and an interactive GIS geolocated healthcare provider directory.

The system's reliability and security are certified through an exhaustive automated test suite of 107 test cases, validating role-based access control (RBAC), medical data privacy in full compliance with Senegalese Data Protection Authority (CDP) regulations, and optimal performance on low-bandwidth networks.

**Keywords:** Third-Party Payment, Health Insurance, Digital Healthcare, Django, Software Architecture, Secure QR Code, RBAC, Senegal, e-Health.

---

## LISTE DES ACRONYMES ET SIGLES

| Sigle | Signification Complète |
| :--- | :--- |
| **API** | Application Programming Interface (Interface de Programmation Applicative) |
| **CDP** | Commission de Protection des Données Personnelles (Sénégal) |
| **CMU** | Couverture Maladie Universelle |
| **CRUD** | Create, Read, Update, Delete |
| **CSRF** | Cross-Site Request Forgery |
| **CSS** | Cascading Style Sheets |
| **FCFA** | Franc de la Communauté Financière Africaine (XOF) |
| **GIS** | Geographic Information System (Système d'Information Géographique) |
| **HTML** | HyperText Markup Language |
| **HTTP** | HyperText Transfer Protocol |
| **HTTPS** | HyperText Transfer Protocol Secure |
| **IDOR** | Insecure Direct Object References |
| **IPM** | Institution de Prévoyance Maladie |
| **ISO** | International Organization for Standardization |
| **KPI** | Key Performance Indicator (Indicateur Clé de Performance) |
| **MVC** | Model-View-Controller |
| **MTV** | Model-Template-View (Pattern architectural de Django) |
| **ORM** | Object-Relational Mapping |
| **PDF** | Portable Document Format |
| **PFE** | Projet de Fin d'Études |
| **QR** | Quick Response (Code barres bi-dimensionnel) |
| **RBAC** | Role-Based Access Control (Contrôle d'Accès Basé sur les Rôles) |
| **REST** | Representational State Transfer |
| **SGBD** | Système de Gestion de Base de Données |
| **SQL** | Structured Query Language |
| **SVG** | Scalable Vector Graphics |
| **UCAD** | Université Cheikh Anta Diop de Dakar |
| **UI / UX** | User Interface / User Experience |
| **UML** | Unified Modeling Language |
| **XSS** | Cross-Site Scripting |

---

# INTRODUCTION GÉNÉRALE

### 1. Contexte Socio-Économique et Sanitaire
L'accès équitable à des soins de santé de qualité et la protection financière contre les dépenses de santé catastrophiques constituent des piliers majeurs de l'agenda de développement socio-économique du Sénégal, alignés sur les Objectifs de Développement Durable (ODD 3). Au sein de l'espace national, la couverture du risque maladie des travailleurs du secteur formel et de leurs familles est historiquement assurée par les **Institutions de Prévoyance Maladie (IPM)**, régies par la loi n° 75-50 du 3 avril 1975 et ses décrets d'application subséquents. 

Ces institutions fonctionnent sur le principe de la solidarité professionnelle et mutualisent les cotisations des employeurs et des salariés pour prendre en charge, sous le régime du **tiers payant**, une quote-part importante (généralement comprise entre 70% et 80%) des dépenses engagées auprès des structures de santé conventionnées (hôpitaux publics, cliniques privées, cabinets médicaux, officines de pharmacie et laboratoires d'analyses).

### 2. Problématique Centrale
En dépit de leur rôle crucial, la grande majorité des IPM sénégalaises et de leurs prestataires partenaires continuent d'opérer selon des processus manuels fondés sur le papier. Cette organisation archaïque génère des dysfonctionnements structurels majeurs :

1. **La Fraude et la Surconsommation Médicale :** L'absence d'identification numérique et de validation en temps réel permet la réutilisation multiple d'une même ordonnance dans différentes pharmacies, la falsification des montants prescrits, l'usurpation de la carte d'assuré par des personnes tierces non déclarées, et l'émission de factures pour des actes médicaux fictifs.
2. **L'Asymétrie d'Information sur les Plafonds de Couverture :** La plupart des plans d'assurance prévoient un plafond budgétaire annuel par famille (ex: 1 000 000 FCFA). Avec le papier, ni l'assuré, ni le médecin, ni le pharmacien ne connaissent le reliquat budgétaire au moment de l'acte, conduisant à des rejets de factures a posteriori lors de la liquidation administrative.
3. **Les Délais de Paiement et la Fragilisation des Prestataires :** Le traitement physique des bordereaux, la vérification manuelle des pièces justificatives et les navettes administratives entraînent des délais de règlement oscillant entre 90 et 180 jours. Cette situation met en péril la trésorerie des officines pharmaceutiques et incite certains établissements à suspendre unilatéralement les conventions de tiers payant.
4. **La Lourdeur du Parcours Patient :** L'assuré doit accomplir de fastidieuses démarches physiques d'obtention de bons de prise en charge préalables avant de pouvoir être reçu en consultation, retardant ainsi l'accès aux soins d'urgence.

### 3. Objectifs et Périmètre du Projet
L'objectif fondamental de ce projet de fin d'études est de concevoir, développer, sécuriser et valider une plateforme logicielle intégrée, baptisée **SantéSN**, capable de dématérialiser l'intégralité du cycle de vie du tiers payant au Sénégal. 

Les objectifs spécifiques assignés au système sont les suivants :
* **Unification des acteurs :** Fédérer dans un environnement unifié les quatre profils d'utilisateurs (Gestionnaire IPM, Médecin traitant, Pharmacien d'officine, Patient assuré).
* **Dématérialisation et sécurisation des titres :** Déployer une carte d'assuré normalisée et des ordonnances médicales numériques certifiées par QR Code vectoriel dynamique non falsifiable.
* **Automatisation du calcul du Tiers Payant :** Calculer instantanément la quote-part assurance et la quote-part patient lors de la facturation en tenant compte du plafond annuel glissant du foyer.
* **Garantie d'unicité de délivrance :** Empêcher techniquement toute réutilisation d'ordonnance grâce à un verrouillage transactionnel immédiat lors de la délivrance en pharmacie.
* **Sécurité et souveraineté des données :** Garantir un cloisonnement hermétique des accès par rôle (RBAC) et une journalisation d'audit inaltérable, en parfaite conformité avec la réglementation sénégalaise sur les données de santé.

### 4. Démarche Méthodologique
Pour mener à bien ce projet, nous avons adopté la méthodologie **Agile Scrum**, caractérisée par des itérations courtes (Sprints de 2 semaines), une collaboration étroite avec les acteurs du domaine médical et mutualiste, et des livraisons fonctionnelles continues testées automatiquement.

---

# CHAPITRE 1 : ÉTAT DE L'ART ET CONTEXTE MÉTIER DU TIERS PAYANT AU SÉNÉGAL

## 1.1 Organisation Institutionnelle de l'Assurance Maladie au Sénégal
Le paysage de la couverture du risque maladie au Sénégal se caractérise par une coexistence de régimes contributifs et non contributifs :
* **Les Institutions de Prévoyance Maladie (IPM) :** Organismes de droit privé à but non lucratif gérés de manière paritaire par les représentants des employeurs et des travailleurs, obligatoires pour toute entreprise comptant au moins 100 salariés (ou regroupées en IPM inter-entreprises).
* **L'Agence Nationale de la Couverture Maladie Universelle (ANACMU) :** Structure étatique dédiée à l'extension de la couverture santé aux populations du secteur informel et du monde rural à travers les mutuelles de santé communautaires.
* **Les Compagnies d'Assurances Privées :** Offres assurantielles marchandes destinées aux cadres supérieurs et aux entreprises multinationales.

## 1.2 Le Fonctionnement Conventionnel du Tiers Payant
Le tiers payant est une convention tripartite par laquelle le prestataire de soins (médecin, pharmacie, clinique) dispense l'assuré de faire l'avance de la totalité des frais médicaux. Le patient ne s'acquitte immédiatement que du **ticket modérateur** (part patient, ex: 20%), tandis que le prestataire adresse ultérieurement la facture de la part restante (part assurance, ex: 80%) à l'organisme assureur (IPM).

## 1.3 Analyse Critique des Vulnérabilités du Modèle Traditionnel
L'audit de terrain mené auprès de cabinets médicaux et d'officines dakaroises a mis en exergue quatre failles majeures :
1. **L'usurpation d'identité et le prêt de carte :** Les cartes d'assuré en carton sans photo biométrique ni QR Code dynamique sont fréquemment prêtées à des proches non déclarés.
2. **La fraude à la délivrance multiple :** Les ordonnances papier n'étant pas tamponnées électroniquement dans un registre partagé, un patient malveillant peut photocopier ou présenter l'ordonnance originale dans trois officines différentes avant que le traitement ne soit facturé.
3. **Les rejets massifs de factures pour dépassement de plafond :** Les IPM rejettent fréquemment les factures de soins dispensés après épuisement du plafond annuel familial de l'assuré, laissant les prestataires supporter des impayés considérables.
4. **La surcharge administrative :** Les comptables des IPM passent plus de 60% de leur temps à saisir manuellement des données de facturation papier sur des tableurs Excel disparates.

## 1.4 Analyse Comparative des Solutions Existantes

| Critère d'Évaluation | Dossiers Hospitaliers Propriétaires | Logiciels Assurances Internationales | Plateforme SantéSN |
| :--- | :---: | :---: | :---: |
| **Adaptation au modèle IPM sénégalais** | Faible (Centré hôpital) | Inadapté (Modèle occidental) | **100% Dédié et Conforme** |
| **Gestion dynamique du Tiers Payant** | Partielle | Complexe | **Automatisée en temps réel** |
| **Plafonnement familial glissant** | Non géré | Forfaitaire individuel | **Calcul instantané du reliquat** |
| **Vérification optique d'ordonnance** | Absente | Propriétaire coûteux | **QR Code Vectoriel SVG Ouvert** |
| **Coût d'infrastructure et licences** | Très élevé (Serveurs locaux) | Abonnement SaaS en devises | **Open Source / Python Django** |
| **Conformité CDP Sénégal (Données)** | Variable | Hébergement hors UEMOA | **Souveraineté des données** |

---

# CHAPITRE 2 : ANALYSE DES BESOINS ET SPÉCIFICATIONS FONCTIONNELLES

## 2.1 Spécifications Fonctionnelles Détaillées

### 2.1.1 Module Gestion des Bénéficiaires & Plans de Couverture
* **Modélisation de la cellule familiale :** Distinction formelle entre l'assuré titulaire (porteur du compte et du contrat) et ses ayants droit déclarés (conjoint, enfants, ascendants) qui héritent automatiquement du taux de prise en charge et partagent le plafond annuel.
* **Génération unique du numéro de carte :** Attribution automatique d'un identifiant national structuré (`SN-XXXXXXXXXX`).
* **Régulation budgétaire :** Définition paramétrable du taux conventionné (ex: 80%) et du plafond annuel d'assurance (ex: 1 000 000 FCFA).

### 2.1.2 Module Médical & Ordonnance Électronique Certifiée
* **Gestion d'agenda et créneaux uniques :** Verrouillage algorithmique interdisant la double réservation d'un médecin sur un même créneau horaire.
* **Prescription structurée :** Saisie des diagnostics et composition de lignes d'ordonnance précises (dénomination médicament, posologie, durée, dosage).
* **Génération d'ordonnance inviolable :** Émission instantanée d'un document sécurisé arborant le cachet officiel circulaire SantéSN, la signature du praticien et un QR Code de vérification unique à 20 caractères hexadécimaux.

### 2.1.3 Module Pharmacie & Scanner Anti-Fraude
* **Double mode d'authentification :** Scanner direct via flux vidéo caméra (`html5-qrcode`) ou saisie manuelle sécurisée du code de l'ordonnance.
* **Contrôle d'intégrité et de validité :** Détection instantanée du statut (Active, Déjà délivrée, Annulée par le médecin).
* **Délivrance atomique :** Validation en transaction de base de données interdisant formellement toute réutilisation ultérieure du même QR Code.

### 2.1.4 Module Facturation, Tiers Payant & Rapports
* **Calcul automatique et ventilation instantanée :**
  Part Assurance = min(Montant Total * Taux / 100, Reliquat Plafond Annuel)
  Ticket Moderateur (Part Patient) = Montant Total - Part Assurance
* **Tableaux de bord analytiques :** Suivi des KPI financiers, volume de consultations par période, taux de délivrance, et exports certifiés aux formats Excel (`.xlsx`) et PDF (`.pdf`).

## 2.2 Exigences Non Fonctionnelles
* **Sécurité Applicative :** Protection intégrale contre les failles OWASP Top 10 (CSRF, XSS, Injections SQL, IDOR).
* **Politique Graphique et Institutionnelle :** Règle stricte du **zéro-emoji**, remplacée par 100% de pictogrammes vectoriels SVG intégrés dans le DOM.
* **Performance et Résilience :** Temps de réponse inférieur à 200 ms pour les requêtes standard et consommation de données optimisée pour la connectivité mobile 3G/4G.
* **Accessibilité et Rendu Physique :** Compatibilité d'impression à l'échelle 1:1 pour les cartes physiques au standard international **ISO 7810 ID-1** (85,6 mm × 54 mm) et pour les ordonnances au format standardisé **A4**.

---

# CHAPITRE 3 : CONCEPTION ARCHITECTURALE ET MODÉLISATION DU SYSTÈME

## 3.1 Architecture Globale du Système (Pattern MTV Modulaire)
SantéSN implémente le patron architectural **Model-Template-View (MTV)** préconisé par Django, enrichi d'un découpage modulaire strict où les responsabilités sont compartimentées en 21 sous-modules spécialisés.

## 3.2 Modèle Mathématique et Algorithmique de Plafonnement
Le calcul du montant alloué lors d'une transaction de tiers payant respecte la procédure algorithmique suivante :

```python
def calculer_part_assurance(consultation, montant_acte, taux_couverture):
    # 1. Calcul théorique selon le taux de prise en charge
    montant_theorique = montant_acte * (taux_couverture / 100)
    
    # 2. Identification du titulaire du plan et des membres du foyer
    titulaire = consultation.patient.titulaire
    plan = titulaire.plan_couverture
    
    if not plan or not plan.plafond_annuel or plan.plafond_annuel <= 0:
        return montant_theorique, montant_acte - montant_theorique
    
    # 3. Sommation des consommations de l'année civile en cours
    annee_en_cours = consultation.date_consultation.year
    membres_foyer = [titulaire.pk] + list(titulaire.ayants_droit.values_list('pk', flat=True))
    
    total_consomme = Paiement.objects.filter(
        consultation__patient_id__in=membres_foyer,
        consultation__date_consultation__year=annee_en_cours
    ).exclude(consultation=consultation).aggregate(
        total=Sum('montant_part_assurance')
    )['total'] or Decimal('0')
    
    # 4. Détermination du reliquat disponible sous plafond
    reliquat = max(Decimal('0'), Decimal(str(plan.plafond_annuel)) - total_consomme)
    
    # 5. Écrêtement de la part assurance
    part_assurance = min(montant_theorique, reliquat)
    part_patient = montant_acte - part_assurance
    
    return part_assurance, part_patient
```

---

# CHAPITRE 4 : IMPLÉMENTATION LOGICIELLE ET SÉCURITÉ AVANCÉE

## 4.1 Environnement Technologique et Outils de Développement
* **Langage de Programmation :** Python 3.14 (Typage strict, performances du compilateur bytecode).
* **Framework Web :** Django 5.2 (Architecture MTV, moteur d'ORM robuste, protection anti-CSRF intégrée).
* **Moteur de Base de Données :** SQLite en environnement de test/qualification locale, abstraction totale pour déploiement PostgreSQL en production via variables `.env`.
* **Génération Graphique Vectorielle :** Bibliothèque `qrcode` compilant en SVG natif sans interpolation bitmap pour une netteté absolue à l'impression.
* **Moteur de Reporting :** `openpyxl` pour la génération dynamique de bordereaux Excel et `reportlab` pour les synthèses PDF de haute fidélité.
* **Cartographie Sanitaire :** Bibliothèque JavaScript `Leaflet.js` connectée aux serveurs de tuiles OpenStreetMap pour la géolocalisation des structures médicales.

## 4.2 Découpage Modulaire du Package `views/`
Pour garantir la maintenabilité du code et éliminer la dette technique d'un monolithe initial, la logique applicative a été partitionnée en 21 modules hautement cohésifs dans `Plateform_medicale/views/` (`auth.py`, `patients.py`, `medecin_espace.py`, `pharmacien_espace.py`, `assure_espace.py`, `dashboard.py`, `consultations.py`, `ordonnances.py`, `paiements.py`, `prises_en_charge.py`, etc.).

## 4.3 Architecture de Sécurité et Protection des Données de Santé
* **Contrôle d'Accès Basé sur les Rôles (RBAC) :** Décorateurs stricts `@admin_required` et `@role_required` avec page d'interdiction `403.html` personnalisée.
* **Prévention des Failles IDOR :** Filtrage systématique par clé primaire et utilisateur authentifié.
* **Traçabilité Immuable (`JournalActivite`) :** Enregistrement horodaté de toutes les transactions sensibles.

---

# CHAPITRE 5 : QUALIFICATION LOGICIELLE, TESTS ET ÉVALUATION DES RÉSULTATS

## 5.1 Stratégie de Qualification et Automatisation des Tests
La fiabilité et la sécurité de SantéSN reposent sur une suite exhaustive de **107 tests automatisés** exécutés avec 100% de succès :
* **Landing & Navigation Publique (5 tests)**
* **Authentification & Gestion des Sessions (15 tests)**
* **Espace Administrateur IPM (28 tests)**
* **Espace Médecin & Prescriptions (18 tests)**
* **Espace Pharmacien & Scanner (14 tests)**
* **Espace Assuré & Ayants Droit (15 tests)**
* **Sécurité & Cloisonnement des URL (12 tests)**

## 5.2 Évaluation des Performances et Optimisation ORM
* **Éradication des requêtes N+1 :** Utilisation systématique de `select_related()` et `prefetch_related()`.
* **Réduction de la charge réseau :** Poids moyen d'une page inférieur à 380 Ko grâce au vectoriel SVG pur.

---

# CONCLUSION GÉNÉRALE ET PERSPECTIVES D'ÉVOLUTION

### 1. Bilan des Travaux Réalisés
SantéSN apporte une réponse numérique pérenne aux défis du tiers payant au Sénégal en supprimant le papier, en éradiquant la fraude à l'ordonnance multiple et en garantissant la transparence des plafonds financiers.

### 2. Perspectives de Développement Futur
* Intégration du paiement Mobile Money (Wave, Orange Money) pour le ticket modérateur.
* Architecture mobile hors-ligne avec signature cryptographique asymétrique.
* IA d'analyse prédictive des interactions médicamenteuses.

---

# BIBLIOGRAPHIE ET WEBOGRAPHIE

1. **République du Sénégal**, *Loi n° 75-50 du 3 avril 1975 relative aux Institutions de Prévoyance Maladie (IPM)*.
2. **République du Sénégal**, *Loi n° 2008-12 du 25 janvier 2008 sur la protection des données à caractère personnel*, CDP.
3. **Organisation Mondiale de la Santé (OMS)**, *Rapport sur la santé dans le monde : Le financement des systèmes de santé*, Genève.
4. **ANACMU**, *Plan Stratégique de Développement de la Couverture Maladie Universelle au Sénégal*, Dakar.
5. **Django Software Foundation**, *Django Documentation Release 5.2*, 2025.
6. **OWASP Foundation**, *OWASP Top 10 Security Risks*, 2023.
7. **ISO/IEC 7810:2019**, *Identification cards — Physical characteristics*.
8. **ISO/IEC 18004:2015**, *QR Code bar code symbology specification*.
