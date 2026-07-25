# Recherche rapide de patients (médecin) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Donner au médecin une barre de recherche instantanée de patients (numéro de carte / nom / prénom / id), débouchant sur une fiche patient dédiée (historique limité au médecin connecté) avec création de consultation pré-remplie.

**Architecture:** Deux nouvelles routes Django additives (`rechercher_patients_medecin` en JSON, `fiche_patient_medecin` en HTML) protégées par le décorateur `role_required(User.Role.MEDECIN)` déjà existant ; un paramètre GET optionnel ajouté à la vue existante `ajouter_consultation_medecin` pour la pré-sélection ; un widget de recherche (HTML + JS vanilla, dupliqué sur deux templates faute de partiels dans ce projet) qui interroge le premier endpoint en direct.

**Tech Stack:** Django (vues fonction, ORM), templates Django, JS vanilla ES5-style (IIFE, `var`/`function`), `fetch`/`AbortController`. Aucune nouvelle dépendance.

## Global Constraints

- Une seule app Django (`Plateform_medicale`) — ne jamais créer de nouvelle app.
- Ne jamais casser une route, une permission ou une fonctionnalité existante : toutes les vues/URLs listées ici sont **nouvelles** ; la seule vue existante modifiée (`ajouter_consultation_medecin`) ne doit rien changer à son comportement en l'absence du nouveau paramètre GET.
- Toutes les nouvelles routes protégées par `@role_required(User.Role.MEDECIN)`, identique au reste des vues médecin.
- **Pas de template partiel** (`{% include %}`) — convention documentée dans `FONCTIONNEMENT.txt` (précédent : bloc Leaflet dupliqué sur 3 templates). Le widget de recherche est dupliqué à l'identique sur `mes_patients.html` et `dashboard_medecin.html`.
- Recherche : porte sur **tous les patients du système** (pas de restriction à `_patients_du_medecin`), au moins 2 caractères, plafonnée à 8 résultats, correspondance exacte du numéro de carte toujours en tête.
- L'endpoint JSON de recherche ne renvoie **jamais de donnée médicale** (diagnostic/traitement/ordonnance) — uniquement des champs d'identification.
- Historique affiché sur la fiche patient : **uniquement les consultations du médecin connecté avec ce patient précis** (`Consultation.objects.filter(medecin=medecin, patient=patient)`), jamais une vue transversale multi-médecins.
- Réutiliser les classes CSS existantes (`.panel`, `.panel-header`, `.badge`, `.dash-pill`, `.etat-vide`, `.admin-layout`, `table`) — n'ajouter à `base.html` que le CSS strictement nécessaire au nouveau composant de recherche (rien n'existe encore pour ça).
- Style JS du projet : IIFE `(function () { ... })();`, `var`/`function` (pas de `const`/`let`/arrow functions), noms de variables en français, `fetch().then().catch()` — voir `ajouter_prestataire.html`.
- `python manage.py check` et `python manage.py test Plateform_medicale` doivent rester verts après **chaque** tâche.
- Spec de référence : `docs/superpowers/specs/2026-07-25-recherche-rapide-patients-design.md`.

---

### Task 1: Endpoint de recherche live (JSON)

**Files:**
- Modify: `Plateform_medicale/views.py:23` (import), et ajout d'une nouvelle vue juste après `mes_patients` (actuellement `views.py:1467-1471`)
- Modify: `Plateform_medicale/urls.py:73` (ajout d'une route juste après `medecin/patients/`)
- Test: `Plateform_medicale/tests.py` (nouvelle classe `RecherchePatientsMedecinTests`, à la suite de `EspaceMedecinTests`, après la ligne 574)

**Interfaces:**
- Consumes : `role_required`, `_medecin_courant`, `_patients_du_medecin` (déjà définis dans `views.py`), modèle `Patient` (champs `numero_carte`, `nom`, `prenom`, `type_beneficiaire`, `date_naissance`).
- Produces : route nommée `rechercher_patients_medecin` (`GET /medecin/patients/recherche/?q=<texte>`), réponse JSON `{"resultats": [{"id": int, "nom": str, "prenom": str, "numero_carte": str, "type_beneficiaire": str, "date_naissance": "YYYY-MM-DD", "deja_vu": bool}, ...]}`. Consommé par les Tasks 4 et 5 (widget JS) via l'URL Django `{% url "rechercher_patients_medecin" %}`.

- [ ] **Step 1: Écrire les tests (échoueront : route inexistante)**

Ajouter dans `Plateform_medicale/tests.py`, juste après la fin de la classe `EspaceMedecinTests` (après la ligne `self.assertEqual(self.medecin.email, 'medecin1@santesn.sn')`, avant `class HistoriqueConsultationsTests`) :

```python
class RecherchePatientsMedecinTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin1@santesn.sn')
        self.autre_medecin = creer_medecin('medecin2@santesn.sn')
        self.patient = creer_patient(nom='Diop', prenom='Awa')
        self.client.login(username='medecin1@santesn.sn', password=PASSWORD)

    def test_recherche_interdite_aux_non_medecins(self):
        self.client.logout()
        creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        self.assertEqual(response.status_code, 403)

    def test_recherche_interdite_a_l_anonyme(self):
        self.client.logout()
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        self.assertEqual(response.status_code, 302)

    def test_recherche_moins_de_deux_caracteres_ne_renvoie_rien(self):
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'D'})
        self.assertEqual(response.json(), {'resultats': []})

    def test_recherche_par_nom_partiel_insensible_a_la_casse(self):
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'dio'})
        resultats = response.json()['resultats']
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0]['id'], self.patient.pk)
        self.assertEqual(resultats[0]['numero_carte'], self.patient.numero_carte)

    def test_recherche_par_numero_de_carte_exact(self):
        response = self.client.get(
            reverse('rechercher_patients_medecin'), {'q': self.patient.numero_carte}
        )
        resultats = response.json()['resultats']
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0]['id'], self.patient.pk)

    def test_recherche_plafonnee_a_huit_resultats(self):
        for i in range(10):
            creer_patient(nom='Diop%s' % i, prenom='Test')
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        self.assertEqual(len(response.json()['resultats']), 8)

    def test_recherche_priorise_toujours_la_correspondance_exacte_de_carte(self):
        carte_recherchee = 'SN-TESTPRIOR01'
        patient_carte = creer_patient(nom='Zzz', prenom='Zzz')
        patient_carte.numero_carte = carte_recherchee
        patient_carte.save()
        # 8 patients dont le nom contient litteralement le numero recherche,
        # tries alphabetiquement avant "Zzz" : sans priorisation explicite,
        # la correspondance exacte serait evincee du top 8 par le tri nom/prenom.
        for i in range(8):
            creer_patient(nom='Aaa%s%s' % (carte_recherchee, i), prenom='Test')
        response = self.client.get(
            reverse('rechercher_patients_medecin'), {'q': carte_recherchee}
        )
        resultats = response.json()['resultats']
        self.assertEqual(len(resultats), 8)
        self.assertEqual(resultats[0]['id'], patient_carte.pk)

    def test_recherche_ne_renvoie_aucune_donnee_medicale(self):
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        resultat = response.json()['resultats'][0]
        self.assertEqual(
            set(resultat.keys()),
            {'id', 'nom', 'prenom', 'numero_carte', 'type_beneficiaire', 'date_naissance', 'deja_vu'},
        )

    def test_recherche_indique_deja_vu(self):
        Consultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_consultation=timezone.now(), diagnostic='RAS',
        )
        autre_patient = creer_patient(nom='Diopsy', prenom='Fatou')
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        resultats = {r['id']: r['deja_vu'] for r in response.json()['resultats']}
        self.assertTrue(resultats[self.patient.pk])
        self.assertFalse(resultats[autre_patient.pk])

    def test_recherche_trouve_un_patient_non_suivi_par_ce_medecin(self):
        """Portee actee dans la spec : tous les patients, pas seulement ceux du medecin connecte."""
        Consultation.objects.create(
            patient=self.patient, medecin=self.autre_medecin,
            date_consultation=timezone.now(), diagnostic='RAS',
        )
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        resultats = response.json()['resultats']
        self.assertEqual(len(resultats), 1)
        self.assertFalse(resultats[0]['deja_vu'])

    def test_medecin_sans_fiche_recoit_une_liste_vide(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'orphelin@santesn.sn')
        self.client.login(username='orphelin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('rechercher_patients_medecin'), {'q': 'Diop'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'resultats': []})
```

- [ ] **Step 2: Lancer les tests pour confirmer l'échec**

Run: `python manage.py test Plateform_medicale.tests.RecherchePatientsMedecinTests -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'rechercher_patients_medecin' not found.`

- [ ] **Step 3: Ajouter l'import nécessaire**

Dans `Plateform_medicale/views.py`, ligne 23, remplacer :

```python
from django.db.models import Count, Q, Sum
```

par :

```python
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
```

- [ ] **Step 4: Ajouter la route**

Dans `Plateform_medicale/urls.py`, ligne 73, remplacer :

```python
    path('medecin/patients/', views.mes_patients, name='mes_patients'),
```

par :

```python
    path('medecin/patients/', views.mes_patients, name='mes_patients'),
    path('medecin/patients/recherche/', views.rechercher_patients_medecin, name='rechercher_patients_medecin'),
```

- [ ] **Step 5: Ajouter la vue**

Dans `Plateform_medicale/views.py`, juste après la fonction `mes_patients` (après la ligne `return render(request, "mes_patients.html", {"patients": _patients_du_medecin(medecin)})`, avant `@role_required(User.Role.MEDECIN)\ndef historique_consultations`), insérer :

```python
@role_required(User.Role.MEDECIN)
def rechercher_patients_medecin(request):
    """
    Recherche live pour la barre de recherche rapide du medecin (numero de
    carte, nom, prenom, identifiant numerique). Renvoie du JSON, jamais de
    donnee medicale : seulement de quoi identifier le bon patient avant
    d'ouvrir sa fiche (voir fiche_patient_medecin).
    """
    medecin = _medecin_courant(request)
    if medecin is None:
        return JsonResponse({"resultats": []})

    requete = request.GET.get("q", "").strip()
    if len(requete) < 2:
        return JsonResponse({"resultats": []})

    filtre = (
        Q(numero_carte__icontains=requete)
        | Q(nom__icontains=requete)
        | Q(prenom__icontains=requete)
    )
    if requete.isdigit():
        filtre |= Q(pk=requete)

    patients_lies = set(_patients_du_medecin(medecin).values_list("pk", flat=True))

    patients = (
        Patient.objects.filter(filtre)
        .select_related("assure_principal", "plan_couverture")
        .annotate(
            priorite=Case(
                When(numero_carte__iexact=requete, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("priorite", "nom", "prenom")[:8]
    )

    resultats = [
        {
            "id": patient.pk,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "numero_carte": patient.numero_carte,
            "type_beneficiaire": patient.get_type_beneficiaire_display(),
            "date_naissance": patient.date_naissance.isoformat(),
            "deja_vu": patient.pk in patients_lies,
        }
        for patient in patients
    ]
    return JsonResponse({"resultats": resultats})


```

- [ ] **Step 6: Lancer les tests pour confirmer le succès**

Run: `python manage.py test Plateform_medicale.tests.RecherchePatientsMedecinTests -v 2`
Expected: PASS (11 tests)

- [ ] **Step 7: Vérifier l'absence de régression globale**

Run: `python manage.py check && python manage.py test Plateform_medicale`
Expected: `System check identified no issues` puis tous les tests existants toujours au vert.

- [ ] **Step 8: Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/urls.py Plateform_medicale/tests.py
git commit -m "feat(medecin): endpoint de recherche live de patients (etape 1, 1/5)"
```

---

### Task 2: Pré-remplissage du formulaire de consultation

**Files:**
- Modify: `Plateform_medicale/views.py:1507-1523` (vue `ajouter_consultation_medecin`)
- Test: `Plateform_medicale/tests.py` (nouvelle classe `PreRemplissagePatientConsultationTests`, à la suite de `RecherchePatientsMedecinTests`)

**Interfaces:**
- Consumes : `ConsultationForm` (déjà défini dans `forms.py`, champ `patient` non restreint), modèle `Patient`.
- Produces : `ajouter_consultation_medecin` accepte désormais `?patient=<pk>` en GET et pré-sélectionne ce patient dans le formulaire. Consommé par le bouton "Nouvelle consultation" de la fiche patient (Task 3).

- [ ] **Step 1: Écrire les tests (échoueront : pas de pré-remplissage)**

Ajouter dans `Plateform_medicale/tests.py`, après la classe `RecherchePatientsMedecinTests` :

```python
class PreRemplissagePatientConsultationTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin1@santesn.sn')
        self.patient = creer_patient(nom='Diop', prenom='Awa')
        self.client.login(username='medecin1@santesn.sn', password=PASSWORD)

    def test_patient_preselectionne_si_parametre_valide(self):
        response = self.client.get(
            reverse('ajouter_consultation_medecin'), {'patient': self.patient.pk}
        )
        self.assertEqual(response.context['form'].initial.get('patient'), str(self.patient.pk))

    def test_formulaire_vide_sans_parametre(self):
        response = self.client.get(reverse('ajouter_consultation_medecin'))
        self.assertNotIn('patient', response.context['form'].initial)

    def test_parametre_non_numerique_ignore_silencieusement(self):
        response = self.client.get(
            reverse('ajouter_consultation_medecin'), {'patient': 'abc'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('patient', response.context['form'].initial)

    def test_parametre_patient_inexistant_ignore_silencieusement(self):
        response = self.client.get(
            reverse('ajouter_consultation_medecin'), {'patient': '999999'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('patient', response.context['form'].initial)

    def test_soumission_post_inchangee_avec_parametre_dans_l_url(self):
        """Non-regression : le POST ignore le query-string, comme avant."""
        response = self.client.post(
            reverse('ajouter_consultation_medecin') + '?patient=%s' % self.patient.pk,
            {
                'patient': self.patient.pk,
                'service': '',
                'prise_en_charge': '',
                'date_consultation': '2026-08-01T10:00',
                'diagnostic': 'RAS',
                'traitement': '',
            },
        )
        consultation = Consultation.objects.get(patient=self.patient)
        self.assertRedirects(
            response, reverse('ajouter_ordonnance_medecin', args=[consultation.pk])
        )
```

- [ ] **Step 2: Lancer les tests pour confirmer l'échec**

Run: `python manage.py test Plateform_medicale.tests.PreRemplissagePatientConsultationTests -v 2`
Expected: FAIL sur `test_patient_preselectionne_si_parametre_valide` (`initial.get('patient')` vaut `None`).

- [ ] **Step 3: Modifier la vue**

Dans `Plateform_medicale/views.py`, remplacer (bloc actuel `ajouter_consultation_medecin`, lignes 1507-1523) :

```python
@role_required(User.Role.MEDECIN)
def ajouter_consultation_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    if request.method == "POST":
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.medecin = medecin
            consultation.save()
            Paiement.calculer_pour(consultation).save()
            messages.success(request, "Consultation enregistree.")
            return redirect("ajouter_ordonnance_medecin", consultation_pk=consultation.pk)
    else:
        form = ConsultationForm()
    return render(request, "ajouter_consultation_medecin.html", {"form": form})
```

par :

```python
@role_required(User.Role.MEDECIN)
def ajouter_consultation_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    if request.method == "POST":
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.medecin = medecin
            consultation.save()
            Paiement.calculer_pour(consultation).save()
            messages.success(request, "Consultation enregistree.")
            return redirect("ajouter_ordonnance_medecin", consultation_pk=consultation.pk)
    else:
        patient_id = request.GET.get("patient", "")
        initial = {}
        if patient_id.isdigit() and Patient.objects.filter(pk=patient_id).exists():
            initial["patient"] = patient_id
        form = ConsultationForm(initial=initial)
    return render(request, "ajouter_consultation_medecin.html", {"form": form})
```

- [ ] **Step 4: Lancer les tests pour confirmer le succès**

Run: `python manage.py test Plateform_medicale.tests.PreRemplissagePatientConsultationTests -v 2`
Expected: PASS (5 tests)

- [ ] **Step 5: Vérifier l'absence de régression globale**

Run: `python manage.py check && python manage.py test Plateform_medicale`
Expected: tout au vert, y compris `EspaceMedecinTests.test_creation_consultation_et_ordonnance_avec_qr` (non affecté, aucun paramètre GET dans ce test).

- [ ] **Step 6: Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/tests.py
git commit -m "feat(medecin): pre-remplissage du patient sur le formulaire de consultation (etape 1, 2/5)"
```

---

### Task 3: Fiche patient médecin

**Files:**
- Modify: `Plateform_medicale/views.py:23` (import `RendezVous` déjà présent — pas de nouveau import), ajout d'une nouvelle vue juste après `rechercher_patients_medecin` (créée en Task 1)
- Modify: `Plateform_medicale/urls.py` (ajout d'une route juste après `rechercher_patients_medecin`)
- Create: `Plateform_medicale/templates/fiche_patient_medecin.html`
- Test: `Plateform_medicale/tests.py` (nouvelle classe `FichePatientMedecinTests`, à la suite de `PreRemplissagePatientConsultationTests`)

**Interfaces:**
- Consumes : `role_required`, `_medecin_courant`, `_patients_du_medecin`, modèles `Patient`, `Consultation`, `RendezVous` ; route `ajouter_consultation_medecin` (produite par Task 2, avec pré-remplissage).
- Produces : route nommée `fiche_patient_medecin` (`GET /medecin/patients/<int:pk>/`). Consommée par le clic sur un résultat de recherche (Tasks 4 et 5).

- [ ] **Step 1: Écrire les tests (échoueront : route inexistante)**

Ajouter dans `Plateform_medicale/tests.py`, après la classe `PreRemplissagePatientConsultationTests` :

```python
class FichePatientMedecinTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin1@santesn.sn')
        self.autre_medecin = creer_medecin('medecin2@santesn.sn')
        self.patient = creer_patient(nom='Diop', prenom='Awa')
        self.client.login(username='medecin1@santesn.sn', password=PASSWORD)

    def test_fiche_interdite_aux_non_medecins(self):
        self.client.logout()
        creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        self.assertEqual(response.status_code, 403)

    def test_fiche_interdite_a_l_anonyme(self):
        self.client.logout()
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        self.assertEqual(response.status_code, 302)

    def test_fiche_patient_inexistant_donne_404(self):
        response = self.client.get(reverse('fiche_patient_medecin', args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_fiche_accessible_pour_un_patient_jamais_vu(self):
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient.numero_carte)

    def test_historique_limite_aux_consultations_du_medecin_connecte(self):
        Consultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_consultation=timezone.now(), diagnostic='Vue par moi',
        )
        Consultation.objects.create(
            patient=self.patient, medecin=self.autre_medecin,
            date_consultation=timezone.now(), diagnostic='ConfidentielAutreMedecin',
        )
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        historique = list(response.context['historique'])
        self.assertEqual(len(historique), 1)
        self.assertEqual(historique[0].diagnostic, 'Vue par moi')
        self.assertNotContains(response, 'ConfidentielAutreMedecin')

    def test_bouton_nouvelle_consultation_pre_remplit_le_patient(self):
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        url_attendue = reverse('ajouter_consultation_medecin') + '?patient=%s' % self.patient.pk
        self.assertContains(response, url_attendue)

    def test_ayants_droit_affiches_pour_un_assure_principal(self):
        ayant_droit = creer_patient(nom='Diop', prenom='Petit')
        ayant_droit.type_beneficiaire = Patient.TypeBeneficiaire.AYANT_DROIT
        ayant_droit.assure_principal = self.patient
        ayant_droit.save()
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        self.assertContains(response, ayant_droit.numero_carte)

    def test_pas_d_ayants_droit_pour_un_ayant_droit(self):
        ayant_droit = creer_patient(nom='Diop', prenom='Petit')
        ayant_droit.type_beneficiaire = Patient.TypeBeneficiaire.AYANT_DROIT
        ayant_droit.assure_principal = self.patient
        ayant_droit.save()
        response = self.client.get(reverse('fiche_patient_medecin', args=[ayant_droit.pk]))
        self.assertEqual(len(response.context['ayants_droit']), 0)

    def test_badge_deja_suivi_si_relation_existante(self):
        Consultation.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_consultation=timezone.now(), diagnostic='RAS',
        )
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        self.assertTrue(response.context['deja_vu'])
        self.assertContains(response, 'Deja suivi')

    def test_pas_de_badge_deja_suivi_sans_relation(self):
        response = self.client.get(reverse('fiche_patient_medecin', args=[self.patient.pk]))
        self.assertFalse(response.context['deja_vu'])
        self.assertNotContains(response, 'Deja suivi')
```

- [ ] **Step 2: Lancer les tests pour confirmer l'échec**

Run: `python manage.py test Plateform_medicale.tests.FichePatientMedecinTests -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'fiche_patient_medecin' not found.`

- [ ] **Step 3: Ajouter la route**

Dans `Plateform_medicale/urls.py`, remplacer la ligne ajoutée en Task 1 :

```python
    path('medecin/patients/recherche/', views.rechercher_patients_medecin, name='rechercher_patients_medecin'),
```

par :

```python
    path('medecin/patients/recherche/', views.rechercher_patients_medecin, name='rechercher_patients_medecin'),
    path('medecin/patients/<int:pk>/', views.fiche_patient_medecin, name='fiche_patient_medecin'),
```

- [ ] **Step 4: Ajouter la vue**

Dans `Plateform_medicale/views.py`, juste après la fonction `rechercher_patients_medecin` ajoutée en Task 1 (avant `@role_required(User.Role.MEDECIN)\ndef historique_consultations`), insérer :

```python
@role_required(User.Role.MEDECIN)
def fiche_patient_medecin(request, pk):
    """
    Fiche d'un patient, ouverte depuis la recherche rapide. L'historique
    n'expose que les consultations du medecin connecte avec ce patient
    (jamais celles d'un autre medecin - voir la spec, section "Decisions
    actees").
    """
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    patient = get_object_or_404(
        Patient.objects.select_related("assure_principal", "plan_couverture"), pk=pk
    )
    historique = (
        Consultation.objects.filter(medecin=medecin, patient=patient)
        .select_related("service", "prise_en_charge")
        .prefetch_related("ordonnance_set")
        .order_by("-date_consultation")
    )
    if patient.type_beneficiaire == Patient.TypeBeneficiaire.PRINCIPAL:
        ayants_droit = patient.ayants_droit.all()
    else:
        ayants_droit = Patient.objects.none()

    prochains_rendez_vous = (
        RendezVous.objects.filter(medecin=medecin, patient=patient, date_heure__gte=timezone.now())
        .exclude(statut=RendezVous.Statut.ANNULE)
        .order_by("date_heure")
    )

    contexte = {
        "patient": patient,
        "historique": historique,
        "ayants_droit": ayants_droit,
        "prochains_rendez_vous": prochains_rendez_vous,
        "deja_vu": _patients_du_medecin(medecin).filter(pk=patient.pk).exists(),
    }
    return render(request, "fiche_patient_medecin.html", contexte)


```

- [ ] **Step 5: Créer le template**

Créer `Plateform_medicale/templates/fiche_patient_medecin.html` :

```html
{% extends "base.html" %}
{% load icones %}

{% block title %}{{ patient.prenom }} {{ patient.nom }} - Fiche patient{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>{{ patient.prenom }} {{ patient.nom }}</h1>
        <p class="subtitle">
            {{ patient.numero_carte }}
            {% if deja_vu %}<span class="badge">Deja suivi</span>{% endif %}
        </p>
    </div>
    <div class="actions">
        <a class="button" href="{% url 'mes_patients' %}">{% icone "chevron-left" %} Mes patients</a>
        <a class="button primary" href="{% url 'ajouter_consultation_medecin' %}?patient={{ patient.pk }}">{% icone "plus-circle" %} Nouvelle consultation</a>
    </div>
</section>

<section class="admin-layout">
    <article class="panel" style="padding:22px 24px;">
        <div class="panel-header" style="padding:0 0 16px;">
            <h2>Identite</h2>
        </div>
        <table>
            <tbody>
                <tr><th>Date de naissance</th><td>{{ patient.date_naissance|date:"d/m/Y" }}</td></tr>
                <tr><th>Telephone</th><td>{{ patient.telephone|default:"-" }}</td></tr>
                <tr><th>Numero de carte</th><td>{{ patient.numero_carte }}</td></tr>
                <tr><th>Type</th><td><span class="badge">{{ patient.get_type_beneficiaire_display }}</span></td></tr>
                <tr><th>Plan de couverture</th><td>{{ patient.titulaire.plan_couverture|default:"-" }}</td></tr>
            </tbody>
        </table>
    </article>

    {% if ayants_droit %}
    <article class="panel" style="padding:22px 24px;">
        <div class="panel-header" style="padding:0 0 16px;">
            <h2>Ayants droit</h2>
        </div>
        <table>
            <thead><tr><th>Nom complet</th><th>Lien</th><th>Numero de carte</th></tr></thead>
            <tbody>
                {% for ayant_droit in ayants_droit %}
                <tr>
                    <td>{{ ayant_droit.prenom }} {{ ayant_droit.nom }}</td>
                    <td>{{ ayant_droit.get_lien_parente_display }}</td>
                    <td>{{ ayant_droit.numero_carte }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </article>
    {% endif %}
</section>

{% if prochains_rendez_vous %}
<section class="panel" style="margin-top:18px;">
    <div class="panel-header">
        <h2>Prochains rendez-vous</h2>
    </div>
    <table>
        <thead><tr><th>Date</th><th>Motif</th><th>Statut</th></tr></thead>
        <tbody>
            {% for rdv in prochains_rendez_vous %}
            <tr>
                <td>{{ rdv.date_heure|date:"d/m/Y H:i" }}</td>
                <td>{{ rdv.motif|default:"-" }}</td>
                <td><span class="dash-pill {% if rdv.statut == 'CONFIRME' %}ok{% else %}attente{% endif %}">{{ rdv.get_statut_display }}</span></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% endif %}

<section class="panel" style="margin-top:18px;">
    <div class="panel-header">
        <h2>Historique des consultations (avec vous)</h2>
    </div>
    {% if historique %}
    <table>
        <thead>
            <tr><th>Date</th><th>Diagnostic</th><th>Traitement</th><th>Ordonnance</th></tr>
        </thead>
        <tbody>
            {% for consultation in historique %}
            <tr>
                <td>{{ consultation.date_consultation|date:"d/m/Y H:i" }}</td>
                <td>{{ consultation.diagnostic }}</td>
                <td>{{ consultation.traitement|default:"-" }}</td>
                <td>
                    {% with ordonnance=consultation.ordonnance_set.first %}
                    {% if ordonnance %}
                    <a class="button primary btn btn-sm" href="{% url 'voir_ordonnance_medecin' ordonnance.pk %}">{% icone "qr-scan" %} Voir</a>
                    {% else %}
                    <a class="button btn btn-sm" href="{% url 'ajouter_ordonnance_medecin' consultation.pk %}">{% icone "plus-circle" %} Creer</a>
                    {% endif %}
                    {% endwith %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="etat-vide">
        {% illustration_vide "clipboard-list" %}
        <p>Aucune consultation avec ce patient pour le moment.</p>
    </div>
    {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 6: Lancer les tests pour confirmer le succès**

Run: `python manage.py test Plateform_medicale.tests.FichePatientMedecinTests -v 2`
Expected: PASS (10 tests)

- [ ] **Step 7: Vérifier l'absence de régression globale**

Run: `python manage.py check && python manage.py test Plateform_medicale`
Expected: tout au vert.

- [ ] **Step 8: Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/urls.py Plateform_medicale/templates/fiche_patient_medecin.html Plateform_medicale/tests.py
git commit -m "feat(medecin): fiche patient dediee avec historique limite au medecin connecte (etape 1, 3/5)"
```

---

### Task 4: CSS du composant recherche + widget sur "Mes patients"

**Files:**
- Modify: `Plateform_medicale/templates/base.html` (ajout de CSS après le bloc `form.action-ligne`)
- Modify: `Plateform_medicale/templates/mes_patients.html`
- Test: `Plateform_medicale/tests.py` (nouvelle classe `WidgetRecherchePatientsTests`, à la suite de `FichePatientMedecinTests`)

**Interfaces:**
- Consumes : route `rechercher_patients_medecin` (Task 1), route `fiche_patient_medecin` (Task 3), classes CSS existantes `.panel`, `.badge`.
- Produces : classes CSS réutilisables `.recherche-patients`, `.recherche-patients-resultats`, `.recherche-patients-item`, `.recherche-patients-vide` (dans `base.html`, donc disponibles pour Task 5 sans dupliquer le CSS).

- [ ] **Step 1: Écrire le test (échouera : widget absent)**

Ajouter dans `Plateform_medicale/tests.py`, après la classe `FichePatientMedecinTests` :

```python
class WidgetRecherchePatientsTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin1@santesn.sn')
        self.client.login(username='medecin1@santesn.sn', password=PASSWORD)

    def test_widget_present_sur_mes_patients(self):
        response = self.client.get(reverse('mes_patients'))
        self.assertContains(response, 'id="recherche-patients-champ"')
        self.assertContains(response, reverse('rechercher_patients_medecin'))
```

- [ ] **Step 2: Lancer le test pour confirmer l'échec**

Run: `python manage.py test Plateform_medicale.tests.WidgetRecherchePatientsTests -v 2`
Expected: FAIL — `id="recherche-patients-champ"` absent de la réponse.

- [ ] **Step 3: Ajouter le CSS dans `base.html`**

Dans `Plateform_medicale/templates/base.html`, remplacer :

```css
        form.action-ligne {
            display: inline;
            max-width: none;
            padding: 0;
            border: 0;
            background: transparent;
            box-shadow: none;
        }

        /* Pagination des listes (Django Paginator) : precedent/suivant +
```

par :

```css
        form.action-ligne {
            display: inline;
            max-width: none;
            padding: 0;
            border: 0;
            background: transparent;
            box-shadow: none;
        }

        /* Recherche rapide de patients (medecin) : champ + liste de resultats
           en direct (AJAX). Dupliquee a l'identique sur "Mes patients" et le
           dashboard medecin (pas de template partiel dans ce projet, voir
           FONCTIONNEMENT.txt). */
        .recherche-patients {
            position: relative;
            max-width: 480px;
        }

        .recherche-patients-resultats {
            position: absolute;
            top: calc(100% + 6px);
            left: 0;
            right: 0;
            z-index: 20;
            margin: 0;
            padding: 6px;
            list-style: none;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 12px 32px rgba(11, 32, 39, 0.16);
            max-height: 320px;
            overflow-y: auto;
        }

        .recherche-patients-item {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            color: var(--text);
        }

        .recherche-patients-item strong {
            flex: 1 0 auto;
        }

        .recherche-patients-item span {
            font-size: 13px;
            color: var(--muted);
        }

        .recherche-patients-item:hover,
        .recherche-patients-item.actif {
            background: var(--primary-soft);
        }

        .recherche-patients-vide {
            padding: 10px 12px;
            color: var(--muted);
            font-size: 14px;
        }

        /* Pagination des listes (Django Paginator) : precedent/suivant +
```

- [ ] **Step 4: Ajouter le widget dans `mes_patients.html`**

Dans `Plateform_medicale/templates/mes_patients.html`, remplacer le fichier entier par :

```html
{% extends "base.html" %}
{% load icones %}

{% block title %}Mes patients{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Mes patients</h1>
        <p class="subtitle">Patients vus en consultation ou avec un rendez-vous.</p>
    </div>
</section>

<section class="panel" style="padding:18px 22px;margin-bottom:18px;">
    <label for="recherche-patients-champ">Recherche rapide</label>
    <div class="recherche-patients">
        <input type="search" id="recherche-patients-champ" name="q" autocomplete="off"
               placeholder="Numero de carte, nom ou prenom..."
               aria-expanded="false" aria-controls="recherche-patients-resultats"
               aria-haspopup="listbox" role="combobox" aria-autocomplete="list">
        <p id="recherche-patients-indice" class="subtitle" style="margin:6px 0 0;" hidden></p>
        <ul id="recherche-patients-resultats" class="recherche-patients-resultats" role="listbox"
            aria-live="polite" hidden></ul>
    </div>
</section>

{% if patients %}
<section class="panel">
    <table>
        <thead>
            <tr>
                <th>Nom complet</th>
                <th>Telephone</th>
                <th>Numero de carte</th>
                <th>Type</th>
            </tr>
        </thead>
        <tbody>
            {% for patient in patients %}
            <tr>
                <td>{{ patient.prenom }} {{ patient.nom }}</td>
                <td>{{ patient.telephone }}</td>
                <td>{{ patient.numero_carte }}</td>
                <td>{{ patient.get_type_beneficiaire_display }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% else %}
<div class="etat-vide">
    {% illustration_vide "users" %}
    <p>Aucun patient pour le moment.</p>
</div>
{% endif %}

<script>
    (function () {
        var champ = document.getElementById('recherche-patients-champ');
        var conteneurResultats = document.getElementById('recherche-patients-resultats');
        var indiceFormat = document.getElementById('recherche-patients-indice');
        if (!champ) { return; }

        var URL_RECHERCHE = '{% url "rechercher_patients_medecin" %}';
        var GABARIT_URL_FICHE = '{% url "fiche_patient_medecin" pk=0 %}';
        var FORMAT_CARTE = /^SN-[0-9A-Fa-f]{10}$/;
        var minuteur = null;
        var requeteEnCours = null;
        var indexActif = -1;

        function formatRessembleCarte(valeur) {
            return /^SN-/i.test(valeur) && !FORMAT_CARTE.test(valeur);
        }

        function fermerResultats() {
            conteneurResultats.hidden = true;
            conteneurResultats.innerHTML = '';
            champ.setAttribute('aria-expanded', 'false');
            champ.removeAttribute('aria-activedescendant');
            indexActif = -1;
        }

        function afficherResultats(resultats) {
            conteneurResultats.innerHTML = '';
            if (!resultats.length) {
                var vide = document.createElement('li');
                vide.className = 'recherche-patients-vide';
                vide.textContent = 'Aucun patient trouve.';
                conteneurResultats.appendChild(vide);
                conteneurResultats.hidden = false;
                champ.setAttribute('aria-expanded', 'true');
                return;
            }
            resultats.forEach(function (patient, index) {
                var item = document.createElement('li');
                item.className = 'recherche-patients-item';
                item.id = 'recherche-patients-item-' + index;
                item.setAttribute('role', 'option');

                var nom = document.createElement('strong');
                nom.textContent = patient.prenom + ' ' + patient.nom;
                var details = document.createElement('span');
                details.textContent = patient.numero_carte + ' - ' + patient.type_beneficiaire;
                item.appendChild(nom);
                item.appendChild(details);

                if (patient.deja_vu) {
                    var badge = document.createElement('span');
                    badge.className = 'badge';
                    badge.textContent = 'Deja suivi';
                    item.appendChild(badge);
                }

                item.addEventListener('click', function () {
                    window.location.href = GABARIT_URL_FICHE.replace(/0\/$/, patient.id + '/');
                });
                conteneurResultats.appendChild(item);
            });
            conteneurResultats.hidden = false;
            champ.setAttribute('aria-expanded', 'true');
        }

        function lancerRecherche(valeur) {
            if (requeteEnCours) { requeteEnCours.abort(); }
            var controleur = new AbortController();
            requeteEnCours = controleur;
            fetch(URL_RECHERCHE + '?q=' + encodeURIComponent(valeur), {
                headers: { 'Accept': 'application/json' },
                signal: controleur.signal,
            })
                .then(function (reponse) { return reponse.json(); })
                .then(function (donnees) { afficherResultats(donnees.resultats || []); })
                .catch(function (erreur) {
                    if (erreur.name !== 'AbortError') { fermerResultats(); }
                });
        }

        champ.addEventListener('input', function () {
            var valeur = champ.value.trim();
            window.clearTimeout(minuteur);

            if (indiceFormat) {
                if (formatRessembleCarte(valeur)) {
                    indiceFormat.textContent = 'Format attendu : SN-XXXXXXXXXX';
                    indiceFormat.hidden = false;
                } else {
                    indiceFormat.hidden = true;
                }
            }

            if (valeur.length < 2) {
                fermerResultats();
                return;
            }
            minuteur = window.setTimeout(function () { lancerRecherche(valeur); }, 300);
        });

        champ.addEventListener('keydown', function (evenement) {
            var items = conteneurResultats.querySelectorAll('.recherche-patients-item');
            if (!items.length || conteneurResultats.hidden) { return; }

            if (evenement.key === 'ArrowDown') {
                evenement.preventDefault();
                indexActif = Math.min(indexActif + 1, items.length - 1);
            } else if (evenement.key === 'ArrowUp') {
                evenement.preventDefault();
                indexActif = Math.max(indexActif - 1, 0);
            } else if (evenement.key === 'Enter') {
                if (indexActif >= 0) {
                    evenement.preventDefault();
                    items[indexActif].click();
                }
                return;
            } else if (evenement.key === 'Escape') {
                fermerResultats();
                return;
            } else {
                return;
            }

            items.forEach(function (item, index) {
                item.classList.toggle('actif', index === indexActif);
            });
            champ.setAttribute('aria-activedescendant', items[indexActif].id);
        });

        document.addEventListener('click', function (evenement) {
            if (!champ.contains(evenement.target) && !conteneurResultats.contains(evenement.target)) {
                fermerResultats();
            }
        });
    })();
</script>
{% endblock %}
```

- [ ] **Step 5: Lancer le test pour confirmer le succès**

Run: `python manage.py test Plateform_medicale.tests.WidgetRecherchePatientsTests -v 2`
Expected: PASS (1 test)

- [ ] **Step 6: Vérifier l'absence de régression globale**

Run: `python manage.py check && python manage.py test Plateform_medicale`
Expected: tout au vert, y compris `test_mes_patients_scope_au_medecin_connecte` (le tableau existant n'a pas changé).

- [ ] **Step 7: Test manuel**

Run: `python manage.py runserver`, se connecter en médecin, aller sur "Mes patients", taper un nom/numéro de carte dans le champ, vérifier : apparition des résultats après 2 caractères, navigation clavier (flèches + Entrée), clic ouvre bien la fiche patient.

- [ ] **Step 8: Commit**

```bash
git add Plateform_medicale/templates/base.html Plateform_medicale/templates/mes_patients.html Plateform_medicale/tests.py
git commit -m "feat(medecin): widget de recherche rapide sur Mes patients (etape 1, 4/5)"
```

---

### Task 5: Widget de recherche sur le dashboard médecin

**Files:**
- Modify: `Plateform_medicale/templates/dashboard_medecin.html`
- Test: `Plateform_medicale/tests.py` (ajout d'une méthode à `WidgetRecherchePatientsTests`)

**Interfaces:**
- Consumes : mêmes routes que Task 4 (`rechercher_patients_medecin`, `fiche_patient_medecin`), même CSS (`base.html`, déjà en place depuis Task 4).
- Produces : rien de consommé par une tâche ultérieure — dernier point d'entrée du widget.

- [ ] **Step 1: Écrire le test (échouera : widget absent du dashboard)**

Dans `Plateform_medicale/tests.py`, ajouter à la classe `WidgetRecherchePatientsTests` (créée en Task 4) :

```python
    def test_widget_present_sur_dashboard_medecin(self):
        response = self.client.get(reverse('dashboard_medecin'))
        self.assertContains(response, 'id="recherche-patients-champ"')
        self.assertContains(response, reverse('rechercher_patients_medecin'))
```

- [ ] **Step 2: Lancer le test pour confirmer l'échec**

Run: `python manage.py test Plateform_medicale.tests.WidgetRecherchePatientsTests.test_widget_present_sur_dashboard_medecin -v 2`
Expected: FAIL — `id="recherche-patients-champ"` absent de la réponse.

- [ ] **Step 3: Ajouter le widget dans `dashboard_medecin.html`**

Dans `Plateform_medicale/templates/dashboard_medecin.html`, remplacer :

```html
<section class="dash-grid">
    <a class="dash-stat" href="{% url 'agenda_medecin' %}">
```

par :

```html
<section class="panel" style="padding:18px 22px;margin-bottom:18px;">
    <label for="recherche-patients-champ">Recherche rapide</label>
    <div class="recherche-patients">
        <input type="search" id="recherche-patients-champ" name="q" autocomplete="off"
               placeholder="Numero de carte, nom ou prenom..."
               aria-expanded="false" aria-controls="recherche-patients-resultats"
               aria-haspopup="listbox" role="combobox" aria-autocomplete="list">
        <p id="recherche-patients-indice" class="subtitle" style="margin:6px 0 0;" hidden></p>
        <ul id="recherche-patients-resultats" class="recherche-patients-resultats" role="listbox"
            aria-live="polite" hidden></ul>
    </div>
</section>

<section class="dash-grid">
    <a class="dash-stat" href="{% url 'agenda_medecin' %}">
```

Puis, juste avant `{% endblock %}` en toute fin de fichier, remplacer :

```html
{% endif %}
</section>
{% endblock %}
```

par :

```html
{% endif %}
</section>

<script>
    (function () {
        var champ = document.getElementById('recherche-patients-champ');
        var conteneurResultats = document.getElementById('recherche-patients-resultats');
        var indiceFormat = document.getElementById('recherche-patients-indice');
        if (!champ) { return; }

        var URL_RECHERCHE = '{% url "rechercher_patients_medecin" %}';
        var GABARIT_URL_FICHE = '{% url "fiche_patient_medecin" pk=0 %}';
        var FORMAT_CARTE = /^SN-[0-9A-Fa-f]{10}$/;
        var minuteur = null;
        var requeteEnCours = null;
        var indexActif = -1;

        function formatRessembleCarte(valeur) {
            return /^SN-/i.test(valeur) && !FORMAT_CARTE.test(valeur);
        }

        function fermerResultats() {
            conteneurResultats.hidden = true;
            conteneurResultats.innerHTML = '';
            champ.setAttribute('aria-expanded', 'false');
            champ.removeAttribute('aria-activedescendant');
            indexActif = -1;
        }

        function afficherResultats(resultats) {
            conteneurResultats.innerHTML = '';
            if (!resultats.length) {
                var vide = document.createElement('li');
                vide.className = 'recherche-patients-vide';
                vide.textContent = 'Aucun patient trouve.';
                conteneurResultats.appendChild(vide);
                conteneurResultats.hidden = false;
                champ.setAttribute('aria-expanded', 'true');
                return;
            }
            resultats.forEach(function (patient, index) {
                var item = document.createElement('li');
                item.className = 'recherche-patients-item';
                item.id = 'recherche-patients-item-' + index;
                item.setAttribute('role', 'option');

                var nom = document.createElement('strong');
                nom.textContent = patient.prenom + ' ' + patient.nom;
                var details = document.createElement('span');
                details.textContent = patient.numero_carte + ' - ' + patient.type_beneficiaire;
                item.appendChild(nom);
                item.appendChild(details);

                if (patient.deja_vu) {
                    var badge = document.createElement('span');
                    badge.className = 'badge';
                    badge.textContent = 'Deja suivi';
                    item.appendChild(badge);
                }

                item.addEventListener('click', function () {
                    window.location.href = GABARIT_URL_FICHE.replace(/0\/$/, patient.id + '/');
                });
                conteneurResultats.appendChild(item);
            });
            conteneurResultats.hidden = false;
            champ.setAttribute('aria-expanded', 'true');
        }

        function lancerRecherche(valeur) {
            if (requeteEnCours) { requeteEnCours.abort(); }
            var controleur = new AbortController();
            requeteEnCours = controleur;
            fetch(URL_RECHERCHE + '?q=' + encodeURIComponent(valeur), {
                headers: { 'Accept': 'application/json' },
                signal: controleur.signal,
            })
                .then(function (reponse) { return reponse.json(); })
                .then(function (donnees) { afficherResultats(donnees.resultats || []); })
                .catch(function (erreur) {
                    if (erreur.name !== 'AbortError') { fermerResultats(); }
                });
        }

        champ.addEventListener('input', function () {
            var valeur = champ.value.trim();
            window.clearTimeout(minuteur);

            if (indiceFormat) {
                if (formatRessembleCarte(valeur)) {
                    indiceFormat.textContent = 'Format attendu : SN-XXXXXXXXXX';
                    indiceFormat.hidden = false;
                } else {
                    indiceFormat.hidden = true;
                }
            }

            if (valeur.length < 2) {
                fermerResultats();
                return;
            }
            minuteur = window.setTimeout(function () { lancerRecherche(valeur); }, 300);
        });

        champ.addEventListener('keydown', function (evenement) {
            var items = conteneurResultats.querySelectorAll('.recherche-patients-item');
            if (!items.length || conteneurResultats.hidden) { return; }

            if (evenement.key === 'ArrowDown') {
                evenement.preventDefault();
                indexActif = Math.min(indexActif + 1, items.length - 1);
            } else if (evenement.key === 'ArrowUp') {
                evenement.preventDefault();
                indexActif = Math.max(indexActif - 1, 0);
            } else if (evenement.key === 'Enter') {
                if (indexActif >= 0) {
                    evenement.preventDefault();
                    items[indexActif].click();
                }
                return;
            } else if (evenement.key === 'Escape') {
                fermerResultats();
                return;
            } else {
                return;
            }

            items.forEach(function (item, index) {
                item.classList.toggle('actif', index === indexActif);
            });
            champ.setAttribute('aria-activedescendant', items[indexActif].id);
        });

        document.addEventListener('click', function (evenement) {
            if (!champ.contains(evenement.target) && !conteneurResultats.contains(evenement.target)) {
                fermerResultats();
            }
        });
    })();
</script>
{% endblock %}
```

- [ ] **Step 4: Lancer le test pour confirmer le succès**

Run: `python manage.py test Plateform_medicale.tests.WidgetRecherchePatientsTests -v 2`
Expected: PASS (2 tests)

- [ ] **Step 5: Vérifier l'absence de régression globale**

Run: `python manage.py check && python manage.py test Plateform_medicale`
Expected: tout au vert, y compris `test_dashboard_accessible_au_medecin` et `test_medecin_sans_fiche_voit_message_dedie`.

- [ ] **Step 6: Test manuel**

Run: `python manage.py runserver`, se connecter en médecin, vérifier sur le tableau de bord que le widget fonctionne de la même façon que sur "Mes patients", et que les cartes `.dash-stat` existantes ne sont pas décalées/cassées visuellement.

- [ ] **Step 7: Commit**

```bash
git add Plateform_medicale/templates/dashboard_medecin.html Plateform_medicale/tests.py
git commit -m "feat(medecin): widget de recherche rapide sur le dashboard (etape 1, 5/5)"
```

---

### Task 6: Clôture — documentation et nettoyage

**Files:**
- Modify: `FONCTIONNEMENT.txt`
- Delete (une fois ce plan et la spec lus/validés) : rien à ce stade — le nettoyage de `docs/superpowers/` pour cette fonctionnalité précise se fait après validation finale par l'utilisateur, pas automatiquement dans cette tâche.

**Interfaces:**
- Consumes : rien (tâche documentaire, aucun code).
- Produces : rien consommé ailleurs.

- [ ] **Step 1: Documenter la fonctionnalité dans `FONCTIONNEMENT.txt`**

Dans `FONCTIONNEMENT.txt`, section design system (juste après le paragraphe sur Leaflet, avant la section "6. TESTS"), ajouter :

```
- Recherche rapide de patients (medecin, plan direction commerciale premium,
  etape 1) : widget de recherche live (AJAX) duplique sur mes_patients.html
  et dashboard_medecin.html (pas de template partiel dans ce projet, meme
  raison que pour Leaflet ci-dessus). Endpoint JSON
  rechercher_patients_medecin (numero de carte / nom / prenom / id, min 2
  caracteres, plafond 8 resultats, correspondance exacte de carte toujours
  en tete via annotate(Case/When)) ; ne renvoie jamais de donnee medicale.
  Nouvelle page fiche_patient_medecin : historique limite aux consultations
  du medecin connecte avec ce patient (jamais une vue transversale
  multi-medecins - choix de confidentialite delibere). La recherche porte
  sur tous les patients du systeme (pas seulement _patients_du_medecin) car
  ConsultationForm.patient n'a jamais ete restreint : ce n'est donc pas une
  extension de permission, seulement une meilleure UX pour une capacite qui
  existait deja. ajouter_consultation_medecin accepte desormais
  ?patient=<pk> en GET pour pre-selectionner le patient.
```

- [ ] **Step 2: Vérifier la suite complète une dernière fois**

Run: `python manage.py check && python manage.py test Plateform_medicale`
Expected: `System check identified no issues`, tous les tests au vert (dont les 28 nouveaux tests de ce plan).

- [ ] **Step 3: Commit**

```bash
git add FONCTIONNEMENT.txt
git commit -m "docs: documente la recherche rapide de patients dans FONCTIONNEMENT.txt (etape 1, cloture)"
```

---

## Self-Review (effectué avant remise du plan)

**Couverture de la spec :** recherche live AJAX → Task 4/5 ; portée tous patients → Task 1 ; historique limité au médecin → Task 3 ; deux points d'entrée (Mes patients + dashboard) → Tasks 4 et 5 ; pré-remplissage consultation → Task 2 ; validation de format non bloquante → Task 4/5 (JS `formatRessembleCarte`) ; aucune donnée médicale dans le JSON → Task 1 (test dédié) ; pas de template partiel → respecté explicitement dans Tasks 4/5 ; documentation finale → Task 6. Aucun écart identifié.

**Placeholders :** aucun "TBD"/"TODO" — recherche vérifiée, seules occurrences du gabarit `SN-XXXXXXXXXX` sont le texte d'aide affiché à l'utilisateur (intentionnel).

**Cohérence des types/noms :** `rechercher_patients_medecin` (URL et vue) utilisé de façon identique dans Tasks 1, 4, 5 ; `fiche_patient_medecin` (URL et vue) identique dans Tasks 3, 4, 5 ; clés JSON (`id`, `nom`, `prenom`, `numero_carte`, `type_beneficiaire`, `date_naissance`, `deja_vu`) identiques entre la vue (Task 1) et le JS qui les consomme (Tasks 4, 5) ; IDs DOM (`recherche-patients-champ`, `recherche-patients-resultats`, `recherche-patients-indice`) identiques entre CSS (Task 4), HTML et JS (Tasks 4, 5) et les tests (`WidgetRecherchePatientsTests`).
