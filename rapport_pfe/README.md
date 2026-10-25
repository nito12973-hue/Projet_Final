# GUIDE DU RAPPORT DE PROJET DE FIN D'ÉTUDES (PFE / DISEP)
## Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Traware de Diamniadio
### Département TIC — Filière Analyste Programmeur Développeur (APD)
**Thème :** *Conception et Réalisation d'une Plateforme Web et Mobile de Dématérialisation du Tiers Payant et de la Prise en Charge Médicale au Sénégal : SantéSN*

---

## 📁 Organisation des Fichiers Rédigés

L'ensemble du mémoire a été rédigé dans le respect scrupuleux du canevas officiel fourni par l'ISEP Diamniadio (volume cible de **42 à 45 pages hors annexes**, soit environ **52 pages complètes**) :

| Fichier Markdown | Intitulé de la Section | Contenu & Rôle Académique |
| :--- | :--- | :--- |
| **`00_PAGES_PRELIMINAIRES.md`** | Pages préliminaires (i à vii) | Page de garde officielle, Dédicaces, Remerciements, Résumé (FR) et Abstract (EN), Sommaire, Sigles et abréviations, Liste des figures et tableaux. |
| **`01_INTRODUCTION_GENERALE.md`** | Introduction générale (pp. 1–5) | Contexte sanitaire sénégalais (IPM/CMU), problématique de la fraude papier, objectifs généraux et spécifiques, méthodologie Agile/UML, annonce du plan. |
| **`02_CHAPITRE_1_CADRE_DU_PROJET.md`** | Chapitre 1 : Cadre du projet (pp. 6–13) | Présentation de l'ISEP Diamniadio et du département TIC/APD, genèse de SantéSN, bénéficiaires (Assurés, Médecins, Pharmaciens, IPM), périmètre fonctionnel, organisation de l'équipe et chaîne d'outils. |
| **`03_CHAPITRE_2_ANALYSE_ET_CADRAGE.md`** | Chapitre 2 : Analyse et cadrage (pp. 14–24) | Description détaillée du circuit papier actuel, matrice SWOT critique, typologie des fraudes terrain, besoins fonctionnels par rôle, exigences non-fonctionnelles (sécurité CDP), étude comparative des solutions, planning Scrum. |
| **`04_CHAPITRE_3_CONCEPTION_DE_LA_SOLUTION.md`** | Chapitre 3 : Conception de la solution (pp. 25–34) | Méthode orientée objet (UML), architecture multicouche Cloud (MVT), diagrammes de cas d'utilisation, diagrammes de séquence (délivrance pharmacie et plafonnement), Modèle Conceptuel et Logique de Données (MCD/MLD relationnel), justification de la stack (Django 5.2, PostgreSQL Neon, Leaflet, jsQR). |
| **`05_CHAPITRE_4_REALISATION_TESTS_RESULTATS.md`** | Chapitre 4 : Réalisation, tests et résultats (pp. 35–47) | Environnement technique, présentation détaillée des 5 espaces applicatifs (Assuré, Médecin, Pharmacien, Gestionnaire, Admin), rapport de validation des 196 tests automatisés (100% de succès), budget d'exploitation annuelle et ROI, analyse des difficultés techniques et solutions (accents, concurrence d'accès, caméras mobiles). |
| **`06_CONCLUSION_ET_PERSPECTIVES.md`** | Conclusion et perspectives (pp. 48–50) | Bilan des objectifs, apports académiques et professionnels pour le groupe, perspectives d'avenir (SEN-CSU, Mobile Money Wave/Orange Money, Intelligence Artificielle anti-fraude). |
| **`07_PAGES_DE_FIN_ET_ANNEXES.md`** | Pages de fin et annexes (pp. 51–57) | Bibliographie et webographie aux normes APA (16 références), annexes avec extraits de code source critiques (HMAC SHA256, verrous transactionnels, Service Worker PWA), Table des matières détaillée numérotée. |

---

## 📄 Document Word (.docx) Prêt à l'Emploi

Le rapport complet a été compilé et mis en page automatiquement dans le fichier Word :
👉 **[`SanteSN_Rapport_PFE_ISEP_Diamniadio.docx`](file:///c:/Users/nito1/Desktop/Projet_Final/rapport_pfe/SanteSN_Rapport_PFE_ISEP_Diamniadio.docx)**

### Caractéristiques de mise en page du document Word :
* **Format standard A4** avec marges académiques de 2,5 cm (1 pouce).
* **Typographie soignée** : Police Calibri 11,5 pt, interligne 1,15, paragraphes aérés.
* **Titres hiérarchisés** : Titre 1 (Teal institutionnel `#0E7C86`), Titre 2 (Brun chaud `#6A3E1E`), Titres 3 et 4 en gras.
* **Tableaux stylisés** : En-têtes colorés en Teal avec texte blanc, alternance de lignes pour une lisibilité optimale.
* **Blocs de code et schémas** : Police Consolas avec retrait et encadrement élégant.
* **Sauts de page** : Découpage net entre les pages préliminaires et chaque chapitre.

---

## ✏️ Personnalisation Finale avant Dépôt

Ouvrez simplement le fichier `SanteSN_Rapport_PFE_ISEP_Diamniadio.docx` dans Microsoft Word, LibreOffice Writer ou Google Docs pour :
1. Remplacer les crochets de la page de garde par vos informations réelles :
   * **[Prénom NOM de l'Étudiant 1]** (et de votre binôme le cas échéant) ;
   * **[Prénom NOM de l'Encadreur]** (Encadreur pédagogique de l'ISEP) ;
   * **[Prénom NOM de l'Encadreur Professionnel]** (le cas échéant).
2. Vérifier vos dédicaces personnelles et remerciements.
3. Insérer vos captures d'écran de l'application (disponibles en ligne sur https://projet-final-bice.vercel.app) dans le Chapitre 4 si vous souhaitez enrichir visuellement le document.
