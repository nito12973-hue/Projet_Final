# Documentation & Ressources de Soutenance — SantéSN

Ce dossier rassemble l'ensemble des livrables documentaires, schémas d'architecture et ressources graphiques pour la présentation et l'exploitation de la plateforme SantéSN.

## Structure du dossier

- **`captures/`** : Captures d'écran haute définition des parcours clés (Espace Assuré avec carte QR et bouton WhatsApp, Agenda Praticien, Scanner Pharmacien, Supervision Administrateur, Dashboard IPM).
- **`DECISIONS.md` (racine)** : Registre complet des décisions architecturales et métier (isolation multi-tenant, offloading médias protégés, fail-closed manager, intégration WhatsApp).

## Rôles & Parcours Documentés

1. **Assuré (Salarié & Ayants Droit)** :
   - Consultation des droits & plafond annuel restant.
   - Carte de tiers payant numérique QR code.
   - Prise de rendez-vous directe via l'application web ou le chatbot WhatsApp (+221 78 957 61 45).
   - Suivi des ordonnances et demandes de remboursement hors réseau.

2. **Médecin Conventionné** :
   - Vérification de l'éligibilité du patient par scan de sa carte QR ou numéro matricule.
   - Gestion de l'agenda et acceptation des rendez-vous.
   - Rédaction d'ordonnances sécurisées avec sceau cryptographique et QR d'authenticité.

3. **Pharmacien Conventionné** :
   - Scanner d'ordonnance et contrôle de conformité.
   - Vérification du conventionnement actif avec l'IPM du patient.
   - Dispense des médicaments avec calcul automatique de la part assurance (tiers payant) et de la part patient.

4. **Gestionnaire IPM / Mutuelle** :
   - Instruction des demandes de prise en charge et devis médicaux.
   - Traitement des remboursements par virement Mobile Money (Wave / Orange Money).
   - Gestion du réseau conventionné et paramétrage des plafonds.

5. **Administrateur IT / DevOps** :
   - Supervision système (`/supervision/`, `/health/`, `/metrics/` Prometheus).
   - Journalisation d'audit immuable.
   - Plan de sauvegarde et restauration (`backups/`).
   - Secret médical garanti : aucun accès aux dossiers de soins des patients.
