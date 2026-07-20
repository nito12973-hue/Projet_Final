# Guide utilisateur — SantéSN

Ce guide explique comment utiliser la plateforme SantéSN au quotidien, écran par
écran, pour chacun des quatre rôles : **Administrateur**, **Assuré**, **Médecin**,
**Pharmacien**. Il complète `FONCTIONNEMENT.txt` (référence technique) et
`CLAUDE.md` (suivi du projet) sans les remplacer.

## Sommaire

- [Se connecter](#se-connecter)
- [Fonctions communes à tous les rôles](#fonctions-communes-à-tous-les-rôles)
- [Administrateur](#administrateur)
- [Assuré](#assuré)
- [Médecin](#médecin)
- [Pharmacien](#pharmacien)
- [Questions fréquentes](#questions-fréquentes)

---

## Se connecter

SantéSN n'a pas d'inscription libre : **seul un administrateur peut créer un
compte**. Si vous n'avez pas encore d'identifiants, contactez votre
administrateur.

1. Ouvrez la page de connexion.
2. Saisissez votre **email** et votre **mot de passe** (pas de nom
   d'utilisateur séparé — l'email sert d'identifiant).
3. Vous êtes automatiquement redirigé vers le tableau de bord correspondant à
   votre rôle : vous n'avez jamais à choisir un rôle vous-même, il est
   déterminé par votre compte.

Si l'application vient d'être installée et qu'aucun administrateur n'existe
encore, un assistant de configuration guide la création du tout premier
compte admin — cet écran ne réapparaît plus une fois un admin créé.

## Fonctions communes à tous les rôles

Ces trois éléments sont accessibles depuis le menu latéral, quel que soit
votre rôle :

- **Notifications** (icône cloche) : messages envoyés par l'administrateur,
  individuellement ou à tout un rôle. Un badge indique le nombre de
  notifications non lues ; ouvrez-en une pour la marquer comme lue.
- **Mot de passe** : changez votre mot de passe à tout moment sans perdre
  votre session en cours.
- **Réduire le menu** (desktop uniquement, chevron en haut du menu) : bascule
  le menu latéral en mode icônes seules pour gagner de la place à l'écran ;
  votre préférence est mémorisée d'une visite à l'autre. Sur mobile, le menu
  s'ouvre en tiroir via l'icône ☰.

## Administrateur

### Ce que vous voyez en arrivant

Le tableau de bord Admin est le centre de pilotage de la plateforme : des
compteurs cliquables (assurés, médecins, prestataires, services, prises en
charge en attente) qui mènent directement à chaque liste, un bloc *Actions
rapides* (ajouter un assuré, un médecin, un prestataire, suivre les prises
en charge), et un rappel du principe de moindre privilège : l'administrateur
gère comptes/prestataires/suivi, mais ne saisit jamais de diagnostic, ne
crée pas d'ordonnance et ne valide pas de délivrance — ce sont les rôles
Médecin et Pharmacien qui s'en chargent.

### Gestion des utilisateurs

- **Créer un utilisateur** : renseignez nom, email, rôle (Admin, Assuré,
  Médecin ou Pharmacien). Le mot de passe est généré automatiquement et
  affiché **une seule fois** à l'écran — notez-le ou communiquez-le
  immédiatement, il ne sera plus jamais visible ensuite.
- **Importer en masse depuis Excel** : téléchargez le modèle, remplissez une
  ligne par compte à créer (colonnes Email, Prénom, Nom, Téléphone, Rôle, et
  selon le rôle : Date de naissance pour un Assuré, Spécialité pour un
  Médecin). L'import est *tout ou rien* : s'il y a une seule ligne en erreur,
  aucun compte n'est créé — corrigez le fichier et réimportez-le.
- **Modifier / activer / désactiver / supprimer** un compte, ou
  **réinitialiser son mot de passe** (nouveau mot de passe généré et affiché
  une seule fois, comme à la création).
- **Export Excel** de la liste filtrée des utilisateurs.
- Par sécurité, un administrateur **ne peut pas** changer son propre rôle, se
  désactiver ou se supprimer lui-même.

### Gestion métier

- **Assurés** : créer un assuré **principal** (cela crée aussi son compte de
  connexion, avec le même écran de mot de passe généré) ; la liste affiche
  aussi les ayants droit de chaque assuré, mais leur création/modification au
  quotidien se fait plutôt depuis l'espace Assuré lui-même. Supprimer un
  assuré principal désactive aussi son compte de connexion.
- **Médecins** : créer (crée aussi le compte de connexion), modifier,
  supprimer (désactive aussi le compte lié). Un avertissement liste tout ce
  qui sera supprimé en cascade (consultations, rendez-vous, paiements,
  ordonnances) avant confirmation.
- **Pharmaciens** : pas d'écran de création dédié — créez le compte depuis
  *Gestion des utilisateurs* avec le rôle Pharmacien, la fiche métier est
  créée automatiquement.
- **Prestataires** : hôpitaux, cliniques, pharmacies et cabinets partenaires
  (nom, type, adresse, ville, téléphone, statut partenaire). Cliquez sur la
  carte du formulaire pour positionner le prestataire (facultatif) : cette
  position est ensuite utilisée pour le trier par proximité dans l'écran
  *Prestataires proches* de l'Assuré.
- **Services médicaux** : actes facturables avec leur prix, rattachés
  éventuellement à un prestataire.
- **Plans de couverture** : taux de remboursement et plafond annuel,
  attribués à un assuré principal (ses ayants droit héritent du même plan).
- **Prises en charge** : demandes de couverture d'un assuré, avec statut *en
  attente / validée / refusée / terminée*. Seule une prise en charge
  **validée** permet une couverture partielle par l'assurance lors d'une
  consultation ; sinon le patient règle 100 % du montant.
- **Paiements** : liste de tous les paiements générés automatiquement à
  chaque consultation, filtrable par statut. *Marquer réglé* exige de
  préciser un mode de règlement.

### Rapports

Graphiques (consultations par mois, répartitions par rôle/type/statut) et
tableaux de données détaillés (repliables sous chaque graphique). Deux
exports disponibles : Excel (un onglet par tableau) et PDF (mise en forme
imprimable).

### Notifications

Envoyer un message à un utilisateur précis ou à tout un rôle d'un coup ;
consulter l'historique des notifications envoyées.

## Assuré

### Premier accès

À la première connexion, complétez votre profil (nom, prénom, date de
naissance, téléphone, adresse) : cela crée votre fiche d'assuré **principal**
et votre numéro de carte de prise en charge (généré automatiquement).

Une fois votre profil complété, le tableau de bord affiche votre numéro de
carte, des compteurs cliquables (ayants droit, rendez-vous à venir,
ordonnances disponibles) et vos prochains rendez-vous, avec un bouton
*Nouveau rendez-vous* toujours accessible en haut de la page.

### Mes ayants droit

Ajoutez votre conjoint et vos enfants comme bénéficiaires de votre
couverture : chacun reçoit son propre numéro de carte et hérite
automatiquement de votre plan de couverture. **Un ayant droit n'a jamais de
compte de connexion propre** — vous gérez tout pour lui depuis votre espace.

### Prestataires proches

Autorisez la géolocalisation de votre navigateur pour voir, sur une carte,
les prestataires partenaires les plus proches de vous, triés du plus proche
au plus loin — la liste et votre position sur la carte se mettent à jour
**en continu** pendant que vous vous déplacez, sans avoir à recharger la
page. Sans localisation, la liste complète du réseau reste disponible,
triée par ville. Chaque prestataire propose un lien *Prendre rendez-vous*
qui ouvre le formulaire de rendez-vous avec ce prestataire déjà sélectionné.

### Mes rendez-vous

Prenez rendez-vous pour vous-même ou pour un de vos ayants droit : choisissez
le médecin, éventuellement un prestataire (pré-rempli si vous arrivez depuis
*Prestataires proches*), la date/heure et le motif. Vous pouvez annuler un
rendez-vous à venir depuis la même page.

### Mes ordonnances

Consultez les ordonnances délivrées par vos médecins, chacune avec son QR
code (et son code textuel affiché en dessous) à présenter en pharmacie.

### Mon historique

Retrouvez toutes vos consultations passées (et celles de vos ayants droit),
avec pour chacune la part restant à votre charge et si elle a déjà été
réglée ou non.

## Médecin

### Ce que vous voyez en arrivant

Le tableau de bord affiche des compteurs cliquables (rendez-vous à venir,
patients suivis, consultations enregistrées) et la liste de vos prochains
rendez-vous avec leur statut. De là, vous accédez à l'agenda, à vos
patients ou à l'historique des consultations d'un clic.

### Agenda

Vue de vos rendez-vous à venir ; changez leur statut (confirmé, terminé,
annulé) au fil de la journée. Vous pouvez aussi ajouter un rendez-vous
vous-même pour un patient.

### Patients

Liste des patients que vous avez déjà consultés.

### Consultations

**Enregistrer une consultation** : sélectionnez le patient, renseignez
diagnostic et traitement, et éventuellement un service médical facturable et
la prise en charge du patient concernée. Un paiement est calculé et créé
**automatiquement** à l'enregistrement (part assurance / part patient selon
que la prise en charge est validée ou non) — vous n'avez rien à saisir
vous-même pour la facturation.

### Ordonnances

Depuis une consultation, générez une ordonnance : saisissez les médicaments
en texte libre, un QR code unique est généré automatiquement (rien à
dessiner ni à imprimer à part le QR affiché). Le patient le retrouve dans son
espace, et la pharmacie s'en sert pour délivrer les médicaments.

### Mon profil

Modifiez vos informations (spécialité, téléphone, prestataire de
rattachement).

## Pharmacien

### Ce que vous voyez en arrivant

Le tableau de bord met en avant un bouton *Scanner un QR Code* directement
dans l'en-tête (l'action la plus fréquente), un compteur de délivrances déjà
validées, et la liste de vos dernières délivrances (date, patient, code
d'ordonnance).

### Scanner un QR Code

Saisissez (ou faites saisir par un lecteur de code) le code affiché sous le
QR code de l'ordonnance du patient (format `RX-XXXXXXXXXX`). L'écran affiche
alors le patient, le médecin, la date et la liste des médicaments prescrits.

### Valider la délivrance

Une fois les médicaments remis au patient, confirmez la délivrance depuis le
même écran. Une ordonnance déjà délivrée ne peut pas l'être une seconde fois
— l'écran l'indique clairement si quelqu'un essaie de la scanner à nouveau.

### Historique

Retrouvez toutes les délivrances que vous avez validées, les plus récentes
en premier.

## Questions fréquentes

**J'ai oublié mon mot de passe, comment le récupérer ?**
Il n'y a pas de récupération en libre-service (aucun envoi d'email n'est
configuré). Demandez à votre administrateur de le réinitialiser depuis
*Gestion des utilisateurs* — un nouveau mot de passe temporaire vous sera
communiqué, à changer ensuite depuis le menu *Mot de passe*.

**Je suis assuré, puis-je créer un compte pour mon conjoint ou mon enfant ?**
Non, et ce n'est pas nécessaire : ajoutez-les comme *ayants droit* depuis
votre espace, ils sont couverts sans avoir besoin de se connecter
eux-mêmes.

**Une prise en charge en attente couvre-t-elle déjà mes consultations ?**
Non. Tant qu'elle n'est pas au statut *validée*, vous réglez 100 % du montant
de la consultation ; c'est une règle métier volontaire, pas un bug.

**Je suis médecin/pharmacien mais je ne vois pas mon tableau de bord après
connexion.**
Votre compte existe mais n'a peut-être pas (ou plus) de fiche métier
associée (par exemple après une suppression par l'administrateur) —
contactez-le pour vérifier votre situation.
