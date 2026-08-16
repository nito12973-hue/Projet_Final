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

Le tableau de bord Admin ouvre sur **ce qui attend une action**, pas sur des
statistiques. Le bandeau sombre *À traiter maintenant* affiche quatre files :
prises en charge à décider, rendez-vous à confirmer, ordonnances non
délivrées, règlements en attente. Chaque tuile est cliquable et mène à la
liste déjà filtrée. La tuile des prises en charge passe en orange dès que la
plus ancienne demande dépasse sept jours. Quand plus rien n'attend, le
bandeau affiche simplement *Rien en attente*.

En dessous : les montants réglés et en attente avec leur tendance sur 30
jours, la répartition entre assurés principaux et ayants droit, cinq
indicateurs d'activité, les dernières prises en charge (celles en attente
remontent en premier) et les derniers comptes créés. Le panneau *Fiches à
compléter* signale les données manquantes qui gênent l'exploitation
(prestataire sans coordonnées sur la carte, assuré sans plan de couverture,
médecin ou pharmacien non rattaché) ; il disparaît quand tout est complet.

En haut de chaque écran, une barre vous donne la recherche d'utilisateur, vos
notifications et votre compte.

Rappel du principe de moindre privilège : l'administrateur gère
comptes/prestataires/suivi, mais ne saisit jamais de diagnostic, ne crée pas
d'ordonnance et ne valide pas de délivrance — ce sont les rôles Médecin et
Pharmacien qui s'en chargent.

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
- **Rendez-vous** : suivi de tous les rendez-vous de la plateforme, en
  **lecture seule**, filtrable par statut et par nom (patient ou médecin).
  Confirmer ou annuler un rendez-vous reste l'affaire du médecin et de
  l'assuré : l'administrateur observe le flux sans y intervenir.
- **Ordonnances** : suivi des ordonnances émises et de leur délivrance en
  pharmacie, en **lecture seule**. Le filtre *Non délivrées* isole les
  ordonnances qu'aucun patient n'est venu retirer — c'est le seul écran qui
  le montre. La validation d'une délivrance reste l'affaire du pharmacien, et
  le QR n'est pas affiché ici : il n'a de sens qu'au comptoir.
- **Paiements** : liste de tous les paiements générés automatiquement à
  chaque consultation, filtrable par statut. *Marquer réglé* exige de
  préciser un mode de règlement.

  Pour enregistrer plusieurs règlements d une traite (rapprochement de fin de
  mois) : exportez les paiements en CSV, complétez les colonnes *Mode de
  règlement* et *Date de règlement* d après votre relevé, puis utilisez
  **Importer des règlements**. Ne modifiez pas la colonne *Référence*, c est
  elle qui identifie chaque paiement.

  Cet import n ajoute jamais de paiement : les montants restent calculés par
  l application à partir du service et du plan de couverture. Comme pour les
  comptes, l import est *tout ou rien* — une seule ligne en erreur annule
  l ensemble, et les erreurs sont listées ligne par ligne.

### Rapports

Graphiques (consultations — bascule jour / mois / année, répartitions par
rôle/type/statut) et tableaux de données détaillés (repliables sous chaque
graphique). Deux exports disponibles : Excel (un onglet par tableau) et PDF
(mise en forme imprimable, toujours sur la vue "par mois").

### Notifications

Envoyer un message à un utilisateur précis ou à tout un rôle d'un coup ;
consulter l'historique des notifications envoyées.

### Paramètres

L'entrée **Paramètres** du menu ouvre une page organisée en catégories. Chaque
catégorie de la colonne de gauche est une **page à part entière** : cliquez
dessus et elle s'ouvre directement (vous pouvez l'ajouter à vos favoris, et le
bouton Retour du navigateur fonctionne normalement).

- **Mon compte** : votre prénom, nom et téléphone. Vous pouvez aussi changer
  votre adresse e-mail, mais comme c'est elle qui vous sert à vous connecter,
  l'application vous demande votre mot de passe actuel pour confirmer. Votre
  rôle, lui, est défini par l'administration et n'est pas modifiable.
- **Sécurité** : changer votre mot de passe.
- **Notifications** : envoyer un message aux utilisateurs et consulter
  l'historique. Cette section reste également accessible directement depuis le
  menu, car c'est une action courante.
- **Apparence** : choisir le thème **clair**, **sombre**, ou **Système** pour
  suivre le réglage de votre appareil, et réduire le menu latéral. Ces choix ne
  concernent que l'appareil sur lequel vous les faites — ils ne sont pas
  enregistrés sur votre compte.
- **Données** (administrateur) : importer des utilisateurs depuis Excel,
  télécharger le modèle, exporter les utilisateurs et les rapports.
- **Sécurité → Comptes temporairement bloqués** : après 5 échecs de connexion
  consécutifs, un compte est bloqué 5 minutes, puis débloqué automatiquement.
  Cette section liste les comptes actuellement bloqués avec le temps restant.
  Vous pouvez filtrer par rôle, rechercher par nom ou e-mail, et débloquer un
  compte immédiatement si la personne vous contacte — une confirmation vous est
  alors demandée. Le déblocage se fait compte par compte, volontairement : un
  grand nombre de blocages simultanés peut signaler une tentative d'intrusion,
  et tout débloquer d'un coup annulerait la protection au pire moment. Quand
  personne n'est bloqué, la section le dit simplement.
- **Avancé** : section repliée qui ne règle rien. Elle indique quels services
  externes la plateforme utilise et signale que l'envoi d'e-mails n'est pas
  configuré — c'est la raison pour laquelle les mots de passe générés
  s'affichent à l'écran au lieu d'être envoyés.

Dans la section Sécurité, le bouton **Déconnecter partout** ferme toutes vos
sessions, y compris celle en cours : vous devrez vous reconnecter. Utilisez-le
si vous pensez que votre compte est compromis, ou si vous avez oublié de vous
déconnecter sur un poste partagé. Il n'affecte que **votre** compte.

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
triée par ville.

Une barre de filtres (recherche par nom, ville, type de prestataire,
distance maximale) affine la liste et la carte instantanément, sans
rechargement. Chaque prestataire est présenté avec son type, sa distance
et un temps de trajet estimé, ainsi que le nombre de médecins qui y sont
rattachés. Le bouton *Voir le profil* centre la carte sur le prestataire
et ouvre sa fiche (nom, ville, téléphone, itinéraire) directement sur la
carte, sans changer de page. *Prendre rendez-vous* ouvre le formulaire de
rendez-vous avec ce prestataire déjà sélectionné. Si aucun prestataire ne
correspond (réseau vide ou filtres trop restrictifs), un message
explicite propose d'actualiser ou de réinitialiser les filtres.

### Mes rendez-vous

Prenez rendez-vous pour vous-même ou pour un de vos ayants droit : choisissez
le médecin, éventuellement un prestataire (pré-rempli si vous arrivez depuis
*Prestataires proches*), la date/heure et le motif. Vous pouvez annuler un
rendez-vous à venir depuis la même page.

### Mes ordonnances

Consultez les ordonnances délivrées par vos médecins, chacune avec son QR
code (et son code textuel affiché en dessous) à présenter en pharmacie.

### Mes prises en charge

Suivez l'état de vos demandes de couverture et de celles de vos ayants
droit : *En attente*, *Validée*, *Refusée* ou *Terminée*. **C'est ce statut
qui détermine ce que vous payez** : tant qu'une demande n'est pas validée,
les soins concernés restent intégralement à votre charge — le taux de votre
plan de couverture ne s'applique qu'aux demandes validées.

Chaque demande affiche les consultations qui s'y rattachent, avec la part
prise en charge par l'assurance, la part restant à votre charge et son
statut de règlement, puis les totaux. Une demande à laquelle aucune
consultation n'est encore rattachée n'affiche aucun montant : il n'y a rien
à facturer pour l'instant.

Le filtre en haut de page limite l'affichage à un statut. Si une demande a
été refusée, contactez l'administration : le motif du refus n'est pas
enregistré dans l'application.

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

**Si le code est illisible.** Ordonnance froissée, impression pâle, code mal
recopié : utilisez le bloc *Code illisible ?* pour rechercher par **nom du
patient** ou par **fragment du code** (trois caractères minimum).

L'application vous présente alors la liste des ordonnances correspondantes —
patient, médecin, date, code et état — et **ne choisit jamais à votre place**,
même s'il n'y a qu'un seul résultat. C'est volontaire : deux patients peuvent
porter le même nom de famille. Vérifiez le patient et la date, puis cliquez sur
*Sélectionner* ; vous retombez sur l'écran de vérification habituel.

Si plus de vingt ordonnances correspondent, l'application vous le signale :
précisez le nom pour réduire la liste.

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
