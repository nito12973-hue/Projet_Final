# Étape 1 — Recherche rapide de patients (Dashboard Médecin)

> Document de travail temporaire (voir CLAUDE.md, "Documents de travail"). Une
> fois la fonctionnalité livrée et vérifiée, le contenu utile est reporté dans
> `FONCTIONNEMENT.txt` et ce dossier est nettoyé.

## Contexte

Première étape d'un plan en 7 étapes visant à rapprocher SantéSN d'une
plateforme SaaS médicale de niveau professionnel (voir le message utilisateur
d'origine, non reproduit ici). Chaque étape est brainstormée, spécifiée,
implémentée, testée et validée séparément avant de passer à la suivante.

Le médecin doit pouvoir retrouver un patient instantanément (numéro de carte,
nom, prénom) plutôt que de dépendre du menu déroulant brut de
`ConsultationForm` ou de la liste statique "Mes patients".

## État des lieux (avant cette étape)

- `Patient.numero_carte` existe déjà : généré automatiquement au format
  `SN-` + 10 caractères hexadécimaux majuscules (`Patient._generer_numero_carte`),
  unique, non éditable. Aucun champ "identifiant" distinct n'existe — le
  numéro de carte en tient lieu.
- Aucune fiche patient (page de détail) n'existe pour aucun rôle. L'admin n'a
  que des formulaires d'édition (`modifier_patient.html`) ; le médecin n'a
  qu'une liste en lecture seule (`mes_patients.html`, sans aucun lien vers un
  détail).
- `_patients_du_medecin(medecin)` (views.py) restreint "Mes patients" et le
  filtre déroulant de `historique_consultations` aux patients ayant déjà un
  rendez-vous ou une consultation avec ce médecin — **mais ce n'est qu'un
  filtre d'affichage**. `ConsultationForm.patient` n'est pas restreint : un
  médecin peut déjà, aujourd'hui, créer une consultation pour n'importe quel
  patient du système via le formulaire existant. La recherche rapide ne va
  donc pas élargir un périmètre de permission — elle rend juste utilisable
  une capacité qui existe déjà mais qui est aujourd'hui cachée derrière un
  menu déroulant impraticable.
- Aucun pattern AJAX/JSON n'existe dans le projet (un seul `fetch()`, pour le
  relais de géocodage Nominatim). Tout le reste est du rendu serveur classique
  avec formulaires GET (`.filtres`).
- L'icône `search` existe déjà dans `templatetags/icones.py`.

## Décisions actées avec l'utilisateur

1. **Recherche live (AJAX)**, pas un formulaire à soumission classique.
2. **Portée de la recherche : tous les patients du système**, pas seulement
   ceux déjà liés au médecin (cohérent avec le point ci-dessus sur
   `ConsultationForm`).
3. **Historique médical affiché sur la fiche patient : uniquement les
   consultations du médecin connecté avec ce patient** — pas de vue
   transversale multi-médecins. Choix délibéré pour ne pas créer une
   extension de périmètre d'accès qui n'existe nulle part ailleurs dans le
   projet (secret médical entre prestataires).
4. **Emplacement** : barre de recherche en haut de "Mes patients" **et**
   widget de recherche rapide sur le dashboard médecin — deux points
   d'entrée, un seul composant réutilisé.

## Modèle de données

Aucun changement de modèle. `Patient.numero_carte` et les champs existants
suffisent.

## Routes

Toutes nouvelles, purement additives — aucune route existante n'est modifiée
ou supprimée.

| Méthode | Route | Vue | Nom | Rôle |
|---|---|---|---|---|
| GET | `/medecin/patients/recherche/` | `rechercher_patients_medecin` | `rechercher_patients_medecin` | Médecin |
| GET | `/medecin/patients/<int:pk>/` | `fiche_patient_medecin` | `fiche_patient_medecin` | Médecin |

`ajouter_consultation_medecin` (route existante, inchangée dans son URL)
gagne un paramètre GET optionnel `?patient=<pk>` pour pré-remplir le
formulaire. Sans ce paramètre, comportement strictement identique à
aujourd'hui.

## Vue `rechercher_patients_medecin` (endpoint JSON)

```
GET /medecin/patients/recherche/?q=<texte>
```

- `@role_required(User.Role.MEDECIN)`, comme toutes les vues médecin.
- Si `q` fait moins de 2 caractères (après `strip()`) : retourne
  `{"resultats": []}` sans toucher la base.
- Requête : `Patient.objects.filter(Q(numero_carte__icontains=q) |
  Q(nom__icontains=q) | Q(prenom__icontains=q))`, plus
  `Q(pk=q)` si `q.isdigit()`. `select_related("assure_principal",
  "plan_couverture")`.
- Tri : correspondance exacte sur `numero_carte` en premier, puis par
  `nom`, `prenom`. Limité à 8 résultats (protection contre une liste trop
  longue à l'écran et contre une charge DB inutile sur une saisie très
  courte).
- Réponse JSON, un objet par résultat — **aucune donnée médicale**, seulement
  ce qui sert à identifier/choisir le bon patient (principe de minimisation
  des données, même logique que la contrainte "le QR ne doit pas exposer de
  données sensibles" prévue pour l'Étape 3) :

```json
{
  "resultats": [
    {
      "id": 42,
      "nom": "Diop",
      "prenom": "Awa",
      "numero_carte": "SN-A1B2C3D4E5",
      "type_beneficiaire": "Assure principal",
      "date_naissance": "1990-04-12",
      "deja_vu": true
    }
  ]
}
```

`deja_vu` indique si ce patient fait partie de `_patients_du_medecin(medecin)`
(purement informatif côté UI — badge "déjà suivi" — n'affecte aucune
permission).

## Vue `fiche_patient_medecin`

```
GET /medecin/patients/<int:pk>/
```

- `@role_required(User.Role.MEDECIN)`.
- `get_object_or_404(Patient, pk=pk)` — n'importe quel patient (voir décision
  2).
- Contexte :
  - `patient` (avec `plan_couverture`, `assure_principal`).
  - `ayants_droit` : `patient.ayants_droit.all()` si le patient est
    l'assuré principal (liste vide sinon).
  - `historique` : `Consultation.objects.filter(medecin=medecin,
    patient=patient).select_related("service", "prise_en_charge")
    .prefetch_related("ordonnance_set").order_by("-date_consultation")`
    — même filtre que `historique_consultations`, juste restreint à ce
    patient précis.
  - `prochains_rendez_vous` : rendez-vous à venir entre ce médecin et ce
    patient (même logique que `dashboard_medecin`), pour donner du contexte
    même si aucune consultation n'a encore eu lieu.
- Template `fiche_patient_medecin.html` (nouveau) : panneau identité +
  panneau ayants droit (si applicable) + tableau historique (réutilise le
  style table existant) + bouton "Nouvelle consultation" vers
  `{% url 'ajouter_consultation_medecin' %}?patient={{ patient.pk }}`.
- Réutilise `.panel`, `.badge`, `.actions`, `.etat-vide` — aucune nouvelle
  classe structurante.

## Modification de `ajouter_consultation_medecin`

- Lit `request.GET.get("patient")` **uniquement sur la requête GET
  initiale** (pas sur le POST, qui garde exactement son comportement actuel).
- Si présent et numérique et correspond à un `Patient` existant :
  `ConsultationForm(initial={"patient": patient_id})`.
- Sinon (absent, invalide, ou patient inexistant) : comportement actuel
  inchangé, formulaire vide.
- Aucune restriction de queryset ajoutée sur le champ `patient` du formulaire
  — on ne touche pas au périmètre existant, seulement au pré-remplissage.

## Frontend

- **Pas de template partiel** (`{% include %}` n'est utilisé nulle part dans
  ce projet — voir `FONCTIONNEMENT.txt`, section design system, à propos du
  bloc Leaflet dupliqué intentionnellement sur 3 templates pour la même
  raison). Le même bloc HTML + `<script>` (recherche live) est donc **dupliqué**
  à l'identique dans `mes_patients.html` et `dashboard_medecin.html`, plutôt
  que factorisé — cohérent avec le seul précédent existant dans le projet.
  - `<input type="search">` avec `aria-expanded`, `aria-controls`, et un
    conteneur de résultats `role="listbox"` (`aria-live="polite"`, même
    esprit que le conteneur toasts déjà présent dans `base.html`).
  - JS vanilla inline (cohérent avec `rapports.html`, `scanner_ordonnance.html`)
    — pas de nouvelle dépendance.
  - Debounce ~300 ms, déclenchement à partir de 2 caractères,
    `AbortController` pour annuler une requête en vol si l'utilisateur
    continue de taper (évite qu'une réponse lente n'écrase un résultat plus
    récent).
  - Navigation clavier dans les résultats : `ArrowDown`/`ArrowUp` pour
    déplacer la sélection, `Enter` pour ouvrir la fiche, `Escape` pour fermer
    la liste et rendre le focus au champ.
  - Chaque résultat : nom complet, numéro de carte, badge type
    (principal/ayant droit), badge discret "déjà suivi" si `deja_vu`. Clic ou
    `Enter` → navigation vers `fiche_patient_medecin`.
  - Indice de format non bloquant : si la saisie ressemble à une tentative de
    numéro de carte (regex approximative, ex. commence par des lettres/chiffres
    dans la longueur attendue) sans correspondre au format exact
    `SN-XXXXXXXXXX`, un texte discret sous le champ affiche "Format attendu :
    SN-XXXXXXXXXX". Ne bloque jamais la recherche par nom/prénom.
  - Aucun jeton CSRF nécessaire (endpoint en lecture seule, GET).
- Le widget dashboard et la barre "Mes patients" ont un balisage et un script
  identiques (copiés-collés), chacun avec ses propres IDs DOM pour éviter
  toute collision si les deux venaient à apparaître un jour sur une même
  page.

## Sécurité

- Les deux nouvelles routes sont protégées par `@role_required(User.Role.MEDECIN)`,
  identique au reste des vues médecin (aucun accès anonyme ou autre rôle).
- L'endpoint JSON ne renvoie que des données d'identification, jamais de
  diagnostic/traitement/ordonnance.
- Limite de résultats (8) et seuil minimal (2 caractères) : hygiène standard
  contre l'énumération/la charge, même si l'endpoint est déjà authentifié et
  restreint au rôle médecin.
- Aucune nouvelle route d'écriture. Le seul changement sur une vue existante
  (`ajouter_consultation_medecin`) est un pré-remplissage optionnel en
  lecture, rétrocompatible.

## Tests (`Plateform_medicale/tests.py`)

- Permissions : anonyme / assuré / pharmacien / admin reçoivent une
  redirection (pas d'accès) sur `rechercher_patients_medecin` et
  `fiche_patient_medecin` ; un médecin y accède normalement.
- Recherche : correspondance exacte sur numéro de carte, correspondance
  partielle sur nom/prénom, insensibilité à la casse, aucune requête DB
  déclenchée sous 2 caractères, plafond de 8 résultats respecté, aucun champ
  médical dans la réponse JSON.
- Fiche patient : `historique` ne contient que les consultations du médecin
  connecté (pas celles d'un autre médecin avec le même patient), 404 sur un
  `pk` inexistant, `ayants_droit` vide pour un ayant droit / peuplé pour un
  principal.
- Pré-remplissage : `ajouter_consultation_medecin?patient=<pk>` pré-sélectionne
  le bon patient dans le formulaire ; sans paramètre ou avec un paramètre
  invalide, comportement identique à l'existant (test de non-régression
  explicite).
- Suite complète (`python manage.py test Plateform_medicale`) toujours verte,
  y compris les tests existants sur `mes_patients`, `historique_consultations`,
  `ajouter_consultation_medecin`.

## Hors périmètre de cette étape (volontairement différé)

- Carte d'assurance visuelle (Étape 2) — la fiche patient créée ici reste
  volontairement sobre (tableau/panneaux existants), pas de nouveau design de
  carte.
- QR sécurisé (Étape 3) — `fiche_patient_medecin` est cependant conçue comme
  la cible naturelle d'un futur scan QR (même URL), sans rien construire de
  spécifique au QR maintenant.
- Aucune notion de "multi-tenant" / logo d'entreprise introduite ici (voir
  remarque à traiter explicitement au moment de l'Étape 2 : ce concept
  n'existe pas du tout dans le modèle de données actuel).
