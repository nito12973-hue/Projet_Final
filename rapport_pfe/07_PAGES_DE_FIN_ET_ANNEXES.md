# PAGES DE FIN ET ANNEXES

---

## 1. Bibliographie et Webographie (Norme APA)

### Ouvrages et Publications Académiques
1. **Pressman, R. S., & Maxim, B. R. (2020).** *Software Engineering: A Practitioner's Approach* (9th ed.). McGraw-Hill Education.
2. **Fowler, M. (2018).** *Refactoring: Improving the Design of Existing Code* (2nd ed.). Addison-Wesley Professional.
3. **Sommerville, I. (2016).** *Software Engineering* (10th ed.). Pearson.
4. **Roebuck, K. (2012).** *Progressive Web Applications: High-impact Strategies - What You Need to Know: Definitions, Adoptions, Impact, Benefits, Maturity, Vendors*. Emereo Publishing.
5. **Ministère de la Santé et de l'Action Sociale du Sénégal (MSAS). (2021).** *Plan Stratégique National de Santé Digitale 2022-2026*. Dakar, Sénégal.

### Législation et Textes Réglementaires
6. **République du Sénégal. (1975).** *Loi n° 75-50 du 3 avril 1975 relative aux Institutions de Prévoyance Maladie (IPM)*. Journal Officiel de la République du Sénégal.
7. **République du Sénégal. (2008).** *Loi n° 2008-12 du 25 janvier 2008 sur la protection des données à caractère personnel*. Commission de Protection des Données Personnelles (CDP), Dakar.
8. **Commission de Protection des Données Personnelles (CDP Sénégal). (2023).** *Guide pratique de conformité pour les systèmes d'information traitant des données de santé*. Dakar.
9. **Organisation Mondiale de la Santé (OMS). (2021).** *Stratégie mondiale pour la santé numérique 2020-2025*. Genève, Suisse.

### Documentation Technique et Webographie
10. **Django Software Foundation. (2024).** *Django Documentation (Version 5.2 LTS)*. Consulté sur https://docs.djangoproject.com/fr/5.2/
11. **PostgreSQL Global Development Group. (2024).** *PostgreSQL 16 Database Documentation*. Consulté sur https://www.postgresql.org/docs/
12. **Neon Inc. (2024).** *Neon Serverless Postgres Architecture and Connection Pooling Guide*. Consulté sur https://neon.tech/docs/introduction
13. **Leaflet Open Source Project. (2024).** *Leaflet JS - An open-source JavaScript library for mobile-friendly interactive maps*. Consulté sur https://leafletjs.com/reference.html
14. **OWASP Foundation. (2023).** *OWASP Top 10 Web Application Security Risks*. Consulté sur https://owasp.org/www-project-top-ten/
15. **Meta Platforms Inc. (2024).** *WhatsApp Business Platform Cloud API Reference (v21.0)*. Consulté sur https://developers.facebook.com/docs/whatsapp/cloud-api/
16. **Mozilla Developer Network (MDN). (2024).** *Progressive Web Apps (PWAs) & Service Worker API*. Consulté sur https://developer.mozilla.org/fr/docs/Web/Progressive_web_apps

---

## 2. Annexes

### Annexe 1 : Extrait du Sceau Cryptographique HMAC-SHA256 (Génération et Vérification)

```python
import hmac
import hashlib
from django.conf import settings

def generer_sceau_ordonnance(ordonnance):
    """
    Calcule l'empreinte cryptographique infalsifiable d'une ordonnance.
    Concatène l'identifiant du patient, la date, l'ID du médecin et la liste
    des médicaments pour interdire toute modification ultérieure.
    """
    cle_secrete = settings.SECRET_KEY.encode("utf-8")
    lignes_concat = "|".join(
        f"{ligne.nom_medicament}:{ligne.quantite}:{ligne.posologie}"
        for ligne in ordonnance.lignes.all().order_by("id")
    )
    message = f"{ordonnance.pk}_{ordonnance.patient_id}_{ordonnance.medecin_id}_{ordonnance.date_prescription}_{lignes_concat}"
    sceau = hmac.new(cle_secrete, message.encode("utf-8"), hashlib.sha256).hexdigest()
    return sceau

def verifier_integrite_ordonnance(ordonnance, sceau_recu):
    """Vérifie en temps constant l'authenticité d'une ordonnance présentée."""
    sceau_calcule = generer_sceau_ordonnance(ordonnance)
    return hmac.compare_digest(sceau_calcule, sceau_recu)
```

---

### Annexe 2 : Verrouillage Pessimiste Atomique en Pharmacie (`views/pharmacien.py`)

```python
from django.db import transaction
from django.core.exceptions import ValidationError

@transaction.atomic
def valider_delivrance_ordonnance(pharmacien_user, ordonnance_pk):
    """
    Valide la délivrance en pharmacie de façon atomique (ACID).
    Empêche physiquement toute double délivrance simultanée via select_for_update.
    """
    # Verrouillage pessimiste exclusif sur la ligne de l'ordonnance
    ordonnance = Ordonnance.objects.select_for_update().get(pk=ordonnance_pk)
    
    if ordonnance.statut != Ordonnance.Statut.ACTIVE:
        raise ValidationError(f"Alerte : Ordonnance déjà traitée ou annulée (Statut : {ordonnance.statut}).")
    
    # 1. Mise à jour du statut
    ordonnance.statut = Ordonnance.Statut.DELIVREE
    ordonnance.pharmacie_delivrance = pharmacien_user.prestataire
    ordonnance.date_delivrance = timezone.now()
    ordonnance.save(update_fields=["statut", "pharmacie_delivrance", "date_delivrance"])
    
    # 2. Débit sécurisé du plafond familial de l'assuré
    patient = ordonnance.patient
    patient.enregistrer_consommation_tiers_payant(ordonnance.montant_part_ipm)
    
    # 3. Création automatique de la créance comptable pour la pharmacie
    CreancePharmacie.objects.create(
        organisme=patient.organisme,
        prestataire=pharmacien_user.prestataire,
        ordonnance=ordonnance,
        montant_a_rembourser=ordonnance.montant_part_ipm,
    )
```

---

### Annexe 3 : Configuration du Service Worker PWA (`static/js/sw.js`)

```javascript
const CACHE_NAME = 'santesn-pwa-v2.1';
const ASSETS_A_METTRE_EN_CACHE = [
    '/',
    '/espace/assure/',
    '/assure/carte-dematerialisee/',
    '/static/css/styles.css',
    '/static/icons/logo-santesn.svg',
    '/static/icons/puce-carte.svg',
    '/static/manifest.json'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_A_METTRE_EN_CACHE);
        })
    );
    self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((reponseEnCache) => {
            // Priorité au cache pour la carte hors-ligne, repli sur le réseau
            return reponseEnCache || fetch(event.request).catch(() => {
                if (event.request.headers.get('accept').includes('text/html')) {
                    return caches.match('/assure/carte-dematerialisee/');
                }
            });
        })
    );
});
```

---

## 3. Table des Matières Détaillée

```
PAGES PRÉLIMINAIRES ........................................................... i
  Page de garde officielle ................................................... i
  Dédicaces .................................................................. ii
  Remerciements .............................................................. iii
  Résumé / Abstract .......................................................... iv
  Sommaire synthétique ....................................................... v
  Liste des sigles et abréviations ........................................... vi
  Liste des figures et liste des tableaux .................................... vii

INTRODUCTION GÉNÉRALE ......................................................... 1
  1. Contexte général du projet .............................................. 1
  2. Problématique ........................................................... 2
  3. Objectif général et objectifs spécifiques ............................... 3
  4. Méthodologie adoptée .................................................... 4
  5. Annonce du plan ......................................................... 5

CHAPITRE 1 : PRÉSENTATION DU CADRE DU PROJET ................................... 6
  1.1 Présentation de la structure d’accueil ou du commanditaire ............. 6
      1.1.1 L'ISEP Amadou Traware de Diamniadio .............................. 6
      1.1.2 Le Département TIC et la filière APD ............................. 7
  1.2 Présentation du projet : origine, bénéficiaires, périmètre ............. 8
      1.2.1 Origine et genèse de SantéSN ..................................... 8
      1.2.2 Bénéficiaires du projet .......................................... 9
      1.2.3 Périmètre fonctionnel et limites du système ...................... 10
  1.3 Organisation du groupe : rôles et outils de travail collaboratif ....... 11
      1.3.1 Répartition des rôles et responsabilités ......................... 11
      1.3.2 Méthode de travail et rituels agiles ............................. 12
      1.3.3 Outils de travail collaboratif et chaîne logicielle .............. 13

CHAPITRE 2 : ANALYSE DE L’EXISTANT ET CADRAGE ................................. 14
  2.1 Étude de l’existant .................................................... 14
      2.1.1 Description du circuit traditionnel papier au Sénégal ............ 14
  2.2 Critique de l’existant ................................................. 16
      2.2.1 Analyse des faiblesses et matrice SWOT ........................... 16
      2.2.2 Typologies de fraudes constatées sur le terrain .................. 17
  2.3 Expression des besoins fonctionnels et non fonctionnels ................ 18
      2.3.1 Expression des besoins fonctionnels par acteur ................... 18
      2.3.2 Expression des besoins non fonctionnels .......................... 21
  2.4 Solutions envisagées et choix retenu ................................... 22
      2.4.1 Analyse comparative des alternatives techniques .................. 22
      2.4.2 Justification du choix retenu (Django + PWA) ..................... 23
  2.5 Planification du projet ................................................ 24

CHAPITRE 3 : CONCEPTION DE LA SOLUTION ........................................ 25
  3.1 Démarche et méthode de conception ...................................... 25
      3.1.1 L'approche orientée objet et le langage UML ...................... 25
      3.1.2 Les patrons de conception architecturaux retenus ................. 26
  3.2 Architecture générale de la solution ................................... 27
      3.2.1 Vue d'ensemble de l'architecture applicative multicouche ......... 27
  3.3 Modélisation détaillée ................................................. 28
      3.3.1 Diagramme de cas d'utilisation global ............................ 28
      3.3.2 Diagrammes de séquence des scénarios critiques ................... 29
      3.3.3 Modèle Conceptuel et Logique de Données (MCD / MLD) .............. 31
  3.4 Choix des outils, technologies et matériels ............................ 33
      3.4.1 Justification technologique approfondie .......................... 33
      3.4.2 Environnement matériel cible ..................................... 34

CHAPITRE 4 : RÉALISATION, TESTS ET RÉSULTATS .................................. 35
  4.1 Mise en œuvre et environnement de travail .............................. 35
      4.1.1 Environnement de développement et outillage ...................... 35
      4.1.2 Organisation modulaire du projet Django .......................... 36
  4.2 Présentation de la solution ............................................ 37
      4.2.1 L'Espace Assuré (Patient et Ayants Droit) ........................ 37
      4.2.2 L'Espace Médecin Traitant ........................................ 38
      4.2.3 L'Espace Pharmacien d'Officine ................................... 39
      4.2.4 L'Espace Gestionnaire d'IPM ...................................... 40
      4.2.5 L'Espace Administrateur Système (IT) ............................. 41
  4.3 Tests et validation .................................................... 42
      4.3.1 Stratégie de tests et assurance qualité .......................... 42
      4.3.2 Résultats d'exécution du banc de 196 tests automatisés ........... 43
  4.4 Évaluation des coûts ................................................... 44
      4.4.1 Budget prévisionnel d'exploitation annuelle (Cloud) .............. 44
      4.4.2 Retour sur investissement (ROI) pour une IPM ..................... 45
  4.5 Difficultés rencontrées et solutions apportées ......................... 46

CONCLUSION GÉNÉRALE ET PERSPECTIVES ........................................... 48
  1. Rappel de la problématique et des objectifs ............................. 48
  2. Bilan des résultats obtenus ............................................. 48
  3. Apports du projet pour le groupe ........................................ 49
  4. Perspectives d'amélioration et vision d'avenir .......................... 49

PAGES DE FIN ET ANNEXES ....................................................... 51
  1. Bibliographie et Webographie (Norme APA) ................................ 51
  2. Annexes techniques ...................................................... 53
  3. Table des matières détaillée ............................................ 55
```
