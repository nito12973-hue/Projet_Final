# CHAPITRE 2 : ANALYSE DE L’EXISTANT ET CADRAGE

---

## 2.1. Étude de l’existant

### 2.1.1. Description du circuit traditionnel de prise en charge au Sénégal
Pour comprendre les fondements de notre intervention, il est nécessaire de décomposer étape par étape le circuit opérationnel actuellement en vigueur dans la majorité des Institutions de Prévoyance Maladie (IPM) et mutuelles d'assurance au Sénégal. Ce circuit repose sur une chaîne d'interactions séquentielles lourdes :

```
                  CIRCUIT TRADITIONNEL PAPIER DU TIERS PAYANT
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │   1. Assuré     │ ───>  │  2. Secrétariat │ ───>  │  3. Praticien   │
  │ Déplacement au  │       │     de l'IPM    │       │   Consultation  │
  │ siège de l'IPM  │       │ Émission du Bon │       │   Ordonnance    │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
                                                               │
                                                               ▼
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │ 6. Règlement    │ <───  │ 5. Audit & Compta│ <─── │ 4. Pharmacie    │
  │ Par chèque ou   │       │ Tri des liasses │       │ Vérification ID │
  │ virement (60j+) │       │ Contrôle manuel │       │ Copie carbone   │
  └─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Phase de demande préalable :** L'assuré ou son ayant droit malade doit d'abord se rendre physiquement au bureau de son IPM (ou auprès du service des ressources humaines de son entreprise) pour demander un « bon de consultation » ou « lettre de garantie ». L'agent administratif vérifie manuellement sur un registre papier ou un tableur Excel local si le travailleur est à jour de ses cotisations et si ses enfants sont légalement déclarés.
2. **Phase de consultation médicale :** Muni de son bon papier et de son carnet d'assuré, le patient se présente dans une structure sanitaire conventionnée (hôpital public ou clinique privée). Le médecin ausculte le patient, remplit le volet médical du bon et rédige une ordonnance manuscrite sur son propre papier à en-tête. Le bon de consultation est signé et tamponné.
3. **Phase de dispensation en pharmacie :** Le patient se rend ensuite dans une officine conventionnée. Le pharmacien examine l'ordonnance et le carnet de l'assuré pour vérifier l'adéquation avec la liste des médicaments remboursables par l'IPM (médicaments de spécialité vs génériques DCI). Le pharmacien applique manuellement le pourcentage de couverture (ex: 80 % pris en charge par l'IPM, 20 % réglé en espèces par le patient), agrafe le bon à une copie de l'ordonnance et délivre les produits.
4. **Phase de facturation et de liquidation :** À la fin de chaque mois, chaque pharmacie et clinique regroupe l'ensemble des ordonnances et bons physiques accumulés. Ces documents sont triés par IPM, agrafés à un bordereau récapitulatif papier dactylographié, puis déposés physiquement au siège de chaque IPM.
5. **Phase de contrôle et paiement :** Les auditeurs comptables de l'IPM réceptionnent ces cartons de factures. Ils vérifient un à un les montants, les taux de prise en charge et les éventuels dépassements de plafonds. Après ce contrôle manuel souvent fastidieux, l'ordonnateur des dépenses émet un chèque ou un ordre de virement bancaire au profit du prestataire, avec un délai de traitement variant généralement entre 45 et 120 jours.

---

## 2.2. Critique de l’existant

### 2.2.1. Analyse des faiblesses et matrice SWOT
Cette organisation manuelle, bien qu'éprouvée historiquement, montre aujourd'hui ses limites structurelles face à la croissance démographique et à l'impératif de célérité des soins médicaux. L'analyse critique synthétique du système existant peut être résumée à travers la matrice SWOT suivante :

| Catégorie | Facteurs d'Analyse |
| :--- | :--- |
| **Forces (Strengths)** | • Système institutionnel juridiquement bien ancré (Code du Travail sénégalais, conventions collectives).<br>• Large maillage territorial des pharmacies d'officine privées et publiques au Sénégal.<br>• Solidarité professionnelle permettant une mutualisation des risques santé. |
| **Faiblesses (Weaknesses)** | • **Dépendance totale au papier :** Perte, détérioration ou rature de pièces justificatives médicales.<br>• **Asynchronisme des contrôles :** La vérification des plafonds intervient a posteriori, bien après que les soins ont été consommés.<br>• **Délais d'attente pénibles :** Lenteurs administratives décourageantes pour les patients souffrants.<br>• **Trésorerie asphyxiée :** Délais de remboursement exorbitants pénalisant les prestataires de santé. |
| **Opportunités (Opportunities)** | • Taux de pénétration record de la téléphonie mobile et de l'Internet 4G/5G au Sénégal.<br>• Succès et démocratisation des technologies QR Code et des paiements mobiles (Wave, Orange Money).<br>• Volonté politique de l'État sénégalais d'accélérer la Couverture Sanitaire Universelle (SEN-CSU) par le numérique. |
| **Menaces (Threats)** | • Résistance au changement de certains acteurs habitués aux circuits informels.<br>• Risque de pannes d'électricité ou d'interruptions du réseau télécom dans les zones périurbaines et rurales.<br>• Vulnérabilités de cybersécurité et risque d'exposition illégale de données médicales sensibles. |

### 2.2.2. Les typologies de fraudes constatées sur le terrain
Nos entretiens avec des gestionnaires d'IPM sénégalaises ont permis d'identifier quatre scénarios de fraude récurrents :

1. **Le prêt de carte d'assuré :** Faute de photo numérique actualisée et de contrôle biométrique ou cryptographique, un assuré en règle prête son carnet à un membre de sa famille élargie, à un colocataire ou à une relation amicale pour lui faire bénéficier indûment d'une consultation ou d'analyses spécialisées coûteuses.
2. **La falsification d'ordonnances :** Modification du nombre de boîtes prescrites (ex: transformer un `1` en `4` boîtes) ou ajout d'un médicament non prescrit par le praticien sur une ordonnance manuscrite valide.
3. **La double délivrance :** Une ordonnance papier n'étant pas systématiquement conservée ou visée de façon indélébile, un patient mal intentionné peut se faire délivrer un traitement dans une pharmacie à Pikine, puis se rendre dans une autre pharmacie aux Parcelles Assainies pour retirer le même lot de médicaments remboursés par la même IPM.
4. **La surfacturation d'actes fictifs :** Certains prestataires peu scrupuleux facturent à l'IPM des soins complexes ou des examens d'imagerie qui n'ont jamais été réalisés sur le patient.

---

## 2.3. Expression des besoins fonctionnels et non fonctionnels

### 2.3.1. Expression des besoins fonctionnels par acteur
Pour remédier efficacement aux faiblesses observées, le système **SantéSN** doit satisfaire un ensemble d'exigences fonctionnelles rigoureuses, articulées autour des cinq rôles clés de la plateforme :

```
                                  MATRICE DES ACTEURS SANTÉSN
  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │   1. ASSURÉ      │  │   2. MÉDECIN     │  │  3. PHARMACIEN   │  │ 4. GESTIONNAIRE  │  │ 5. ADMINISTRATEUR│
  │  (Patient / AD)  │  │  (Prescripteur)  │  │  (Dispensateur)  │  │    (Auditeur)    │  │    (Système)     │
  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

#### A. Besoins de l'Assuré (Patient / Ayant droit)
* **BF-ASS-01 :** Accéder à sa carte d'assuré dématérialisée (format carte bancaire ISO 7810 avec puce dorée et QR Code dynamique personnel).
* **BF-ASS-02 :** Consulter en temps réel la jauge de son plafond annuel familial restant et l'historique détaillé des consommations médicales de son foyer.
* **BF-ASS-03 :** Visualiser sur une carte interactive (SIG) les cliniques, cabinets médicaux et pharmacies conventionnés les plus proches avec calcul d'itinéraire.
* **BF-ASS-04 :** Déclarer et gérer ses ayants droit légaux (conjoint, enfants mineurs) avec téléversement des pièces justificatives (extrait de naissance, certificat de mariage).
* **BF-ASS-05 :** Soumettre une demande de remboursement hors réseau avec photo du reçu d'honoraires pour les soins urgents hors réseau conventionné.
* **BF-ASS-06 :** Disposer d'un mode hors-ligne complet (PWA) permettant d'afficher sa carte et son QR code même en l'absence de réseau Internet.

#### B. Besoins du Médecin Traitant
* **BF-MED-01 :** Authentifier instantanément un patient par recherche de son matricule, scan de son QR code ou saisie de son identité.
* **BF-MED-02 :** Consulter l'historique médical des consultations antérieures et les allergies déclarées du patient.
* **BF-MED-03 :** Créer une consultation médicale et prescrire une ordonnance électronique normée (choix de médicaments, posologie, durée de traitement).
* **BF-MED-04 :** Signer électroniquement l'ordonnance avec apposition d'un tampon officiel SantéSN et génération d'un **sceau d'intégrité cryptographique HMAC**.
* **BF-MED-05 :** Générer un document PDF certifié imprimable au format A4 avec QR Code de délivrance infalsifiable.

#### C. Besoins du Pharmacien d'Officine
* **BF-PHA-01 :** Scanner l'ordonnance médicale ou la carte de l'assuré à l'aide de la caméra du smartphone ou de la webcam de l'ordinateur de comptoir.
* **BF-PHA-02 :** Valider instantanément l'authenticité de l'ordonnance et contrôler que son statut est strictement « active » (non expirée et non déjà délivrée).
* **BF-PHA-03 :** Calculer automatiquement la part prise en charge par l'IPM (tiers payant) et le reste à charge à payer par l'assuré en espèces ou mobile money.
* **BF-PHA-04 :** Effectuer une **validation atomique (ACID) en base de données** marquant l'ordonnance comme « délivrée » de façon immédiate et irréversible pour proscrire toute double dispensation.
* **BF-PHA-05 :** Consulter le registre journalier des ventes et télétransmettre électroniquement les créances à l'IPM sans paperasse.

#### D. Besoins du Gestionnaire d'IPM
* **BF-GES-01 :** Piloter l'activité de l'IPM à travers un tableau de bord analytique (consommations par type de soins, taux de sinistralité, alertes de dépassement de plafonds).
* **BF-GES-02 :** Paramétrer les conventions de partenariat avec les établissements de santé (taux de tiers payant, tarification négociée, coordonnées GPS).
* **BF-GES-03 :** Configurer les plans de couverture des entreprises affiliées (plafonds annuels, listes d'exclusions, quotes-parts par catégorie).
* **BF-GES-04 :** Instruire les demandes de remboursement hors réseau (approbation, rejet motivé, notification instantanée de l'assuré).
* **BF-GES-05 :** Émettre les bordereaux mensuels de télétransmission et déclencher les liquidations comptables pour le virement aux prestataires.

#### E. Besoins de l'Administrateur Système (IT)
* **BF-ADM-01 :** Gérer les comptes utilisateurs et l'affectation stricte des rôles selon le principe du moindre privilège (RBAC).
* **BF-ADM-02 :** Superviser le journal d'audit immuable (*Audit Trail*) traçant chaque action sensible (connexion, délivrance, consultation de dossier médical).
* **BF-ADM-03 :** Garantir l'isolation hermétique des données entre organismes concurrents (Architecture Multi-Tenant sans interférence).
* **BF-ADM-04 :** Surveiller les métriques techniques de performance et l'intégrité de la base de données.

---

### 2.3.2. Expression des besoins non fonctionnels

Les exigences non fonctionnelles définissent les contraintes de qualité logicielle, de performance, d'ergonomie et de sécurité que le système doit impérativement respecter :

1. **Sécurité et Confidentialité Médicale (Fail-Closed) :**
   * *Protection CDP Sénégal :* Le traitement des données médicales doit être strictement conforme aux dispositions de la loi sénégalaise n° 2008-12 sur la protection des données personnelles.
   * *Principe Zero-Trust :* Chaque requête API ou vue web doit vérifier côté serveur l'habilitation de l'utilisateur connecté sans jamais se fier aux données envoyées par le client.
   * *Protection contre les failles OWASP Top 10 :* Immunité garantie contre les injections SQL (via l'ORM Django paramétré), les attaques CSRF (jetons cryptographiques systématiques), les attaques XSS (échappement automatique des templates) et les failles IDOR (accès indirects bloqués).
   * *Sceau HMAC-SHA256 :* L'authenticité des ordonnances et des cartes assurés est protégée par une empreinte numérique calculée avec une clé secrète serveur.

2. **Performance et Disponibilité :**
   * Temps de réponse moyen d'une page ou d'une transaction de scan inférieur à 800 millisecondes sur une connexion 3G/4G standard.
   * Base de données Cloud PostgreSQL hébergée sur une architecture résiliente avec basculement automatique et sauvegardes automatiques journalières.

3. **Ergonomie et Accessibilité (Mobile First) :**
   * Conception adaptative (*Responsive Design*) garantissant une utilisation fluide sur smartphones Android, tablettes et ordinateurs de bureau.
   * Prise en charge d'un **mode clair et d'un mode sombre** natif respectant les normes de contraste WCAG 2.1 AA pour le confort visuel des praticiens de santé.
   * Respect d'une politique « zéro emoji » dans les documents officiels (ordonnances, fiches de soins, factures) au profit d'icônes vectorielles SVG institutionnelles.

4. **Résilience et Tolérance aux Pannes Réseau (Offline First) :**
   * Grâce à la technologie PWA et à l'enregistrement d'un Service Worker, les assurés peuvent afficher leur carte d'assuré et leurs droits même en l'absence totale de couverture réseau.

---

## 2.4. Solutions envisagées et choix retenu

### 2.4.1. Analyse comparative des alternatives techniques

Avant d'arrêter nos choix d'ingénierie, nous avons évalué trois approches architecturales distinctes :

| Critères d'Évaluation | Option 1 : Progiciel Propriétaire Existant | Option 2 : Application Mobile Native (Flutter / Kotlin) | Option 3 : Solution Web PWA Django (SantéSN Retenue) |
| :--- | :--- | :--- | :--- |
| **Coût d'acquisition et licences** | Très élevé (coûts récurrents en devises, dépendance éditeur étranger). | Moyen (double développement Android & iOS ou maintenance multi-plateforme). | **Zéro coût de licence (100 % Open Source), souveraineté technologique totale.** |
| **Accessibilité pour les acteurs** | Nécessite des postes clients lourds spécifiques sous Windows. | Obligation d'installation via Google Play / Apple Store (barrière pour smartphones d'entrée de gamme). | **Accès universel via n'importe quel navigateur moderne, sans installation forcée.** |
| **Mode hors-ligne et réactivité** | Faible ou inexistant. | Excellent mais volumineux (fichiers APK de 50 Mo+). | **Excellente légèreté (cache PWA de moins de 3 Mo, Service Worker instantané).** |
| **Sécurité des données de santé** | Hébergement souvent hors du continent (non-conformité CDP). | Risque d'extraction de logique côté client mobile. | **Logique métier 100 % sécurisée côté serveur Django, chiffrement HTTPS strict.** |
| **Facilité de déploiement** | Déploiements locaux fastidieux sur chaque site. | Mises à jour soumises aux délais de validation des stores. | **Déploiement Cloud continu en temps réel (CI/CD) instantané pour tous les usagers.** |

### 2.4.2. Justification du choix retenu
Le choix d'une **Application Web Progressive (PWA) adossée au framework Django** s'impose comme la solution optimale pour le contexte socio-technique sénégalais :
* **Django (Python) :** Réputé dans le monde entier comme le framework le plus robuste pour les applications bancaires et médicales nécessitant une sécurité sans faille (*Batteries-included*), un ORM puissant immunisé contre les injections SQL et une gestion native des utilisateurs et permissions.
* **PWA (Progressive Web App) :** Offre le meilleur des deux mondes entre le web et le mobile. Elle permet aux assurés d'ajouter l'icône SantéSN directement sur l'écran d'accueil de leur smartphone sans passer par un magasin d'applications, tout en garantissant un fonctionnement hors-ligne pour la présentation des cartes de soins.
* **PostgreSQL (Neon) :** Base de données relationnelle leader, assurant l'intégrité transactionnelle ACID absolue, indispensable pour garantir qu'un centime d'assurance ou une boîte de médicament ne soit jamais comptabilisé deux fois.

---

## 2.5. Planification du projet

La conduite du projet a été structurée sur un calendrier prévisionnel rigoureux de 12 semaines, découpé en six itérations (sprints Scrum) successives :

| Phase / Sprint | Période | Livrables et Objectifs Opérationnels |
| :--- | :---: | :--- |
| **Phase 0 : Cadrage & Étude préalable** | Semaines 1 – 2 | Cahier des charges fonctionnel, benchmark des IPM, matrice SWOT, choix technologiques. |
| **Sprint 1 : Socle & Multi-Tenancy** | Semaines 3 – 4 | Modélisation MCD, paramétrage Django/PostgreSQL, système d'authentification RBAC et isolation multi-organismes. |
| **Sprint 2 : Assurés & Cartes ISO** | Semaines 5 – 6 | Module de gestion des assurés, ayants droit, génération des cartes ISO 7810 avec QR Code et algorithme de plafonnement. |
| **Sprint 3 : Espace Médical & Ordonnances** | Semaines 7 – 8 | Agenda de consultation, dossier médical patient, prescription d'ordonnances et signature électronique avec sceau HMAC. |
| **Sprint 4 : Espace Pharmacie & Scanner** | Semaines 9 – 10 | Scanner optique par caméra (`jsQR`), vérification d'ordonnance en direct, délivrance atomique et calcul du tiers payant. |
| **Sprint 5 : Gestionnaire & SIG Leaflet** | Semaines 11 – 12 | Paramétrage des conventions, géolocalisation Leaflet, cartographie sanitaire, télétransmission et remboursements hors réseau. |
| **Sprint 6 : QA, PWA, Tests & Clôture** | Semaines 13 – 14 | Service Worker PWA, suite des 196 tests automatisés validés, audit de sécurité, déploiement Vercel et rédaction finale du mémoire. |
