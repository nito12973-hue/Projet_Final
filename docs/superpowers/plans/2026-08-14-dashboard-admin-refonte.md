# Refonte du Dashboard Administrateur — plan d'implémentation

> **Pour les agents :** SOUS-COMPÉTENCE REQUISE : utiliser
> superpowers:subagent-driven-development (recommandé) ou
> superpowers:executing-plans pour implémenter ce plan tâche par tâche.
> Les étapes utilisent la syntaxe case à cocher (`- [ ]`).

**Goal :** transformer le Dashboard Administrateur en poste de pilotage qui
ouvre sur les files d'attente réelles, avec une barre supérieure, et ajouter
les deux pages admin manquantes (rendez-vous, ordonnances) sans lesquelles
deux de ses indicateurs ne mèneraient nulle part.

**Architecture :** direction « Clinique claire » — fond de page clair,
sidebar navy conservée, un seul bandeau sombre pour l'urgence. Tout le CSS
reste inline dans `base.html` (convention du projet, aucun fichier statique).
Les deux nouvelles vues suivent exactement le patron des listes admin
existantes (`_trier`, `_paginer`, template avec `.filtres` + `entete_tri`).

**Tech Stack :** Django 6, SQLite en développement, Chart.js 4.4.7 via CDN
avec intégrité SRI (déjà en place), aucune nouvelle dépendance.

## Global Constraints

- Spec de référence : `docs/superpowers/specs/2026-08-14-dashboard-admin-refonte-design.md`.
- Structure du projet figée : une seule app `Plateform_medicale`, templates à
  plat, **aucun nouveau fichier Python** dans l'app (pas de
  `context_processors.py`).
- Aucune migration, aucun changement de modèle.
- Toutes les routes existantes sont conservées ; seules deux routes sont
  ajoutées (`liste_rendez_vous`, `liste_ordonnances`).
- Les deux nouvelles pages sont en **lecture seule** : aucune action
  d'écriture sur `RendezVous` ni sur `Ordonnance` depuis l'admin.
- Aucun émoji nulle part. Les icônes viennent de `templatetags/icones.py`
  via `{% icone "nom" %}` ; réutiliser une icône existante avant d'en ajouter.
- Palette : uniquement les jetons SantéSN existants
  (`--primary #0e7c86`, `--primary-dark #0b2027`, `--primary-accent #4fb8ae`,
  `--accent #e0824f`) plus les 4 couples sémantiques définis dans la spec §5.
- Tous les nombres en `font-variant-numeric: tabular-nums`.
- Suite de tests exécutée **en synchrone** (jamais en arrière-plan) :
  `python manage.py test Plateform_medicale`.
- Chaque tâche se termine par un commit en français, préfixe
  `feat(...)` / `style(...)` / `test(...)`.

---

### Task 1 : Page admin « Rendez-vous » (lecture seule)

**Files:**
- Modify: `Plateform_medicale/views.py` (nouvelle vue après `liste_prises_en_charge`)
- Modify: `Plateform_medicale/urls.py` (après la ligne `prises-en-charge/...`)
- Create: `Plateform_medicale/templates/liste_rendez_vous.html`
- Modify: `Plateform_medicale/templates/base.html:2294` (entrée sidebar)
- Test: `Plateform_medicale/tests.py`

**Interfaces:**
- Consumes : `_trier`, `_paginer`, `admin_required` (déjà dans `views.py`) ;
  helpers de test `creer_utilisateur`, `creer_medecin`, `creer_patient`.
- Produces : route nommée **`liste_rendez_vous`**, acceptant les paramètres
  GET `statut` (valeurs `RendezVous.Statut`), `q`, `tri`, `page`. La Task 4
  y renverra depuis la tuile « Rendez-vous à confirmer » avec
  `?statut=DEMANDE`.

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter à la fin de `Plateform_medicale/tests.py` :

```python
class ListeRendezVousAdminTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin-rdv@santesn.sn')
        self.medecin = creer_medecin('medecin-rdv@santesn.sn')
        self.patient = creer_patient(nom='Sarr', prenom='Mariama')
        self.autre_patient = creer_patient(nom='Fall', prenom='Ousmane')
        maintenant = timezone.now()
        self.demande = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date_heure=maintenant + datetime.timedelta(days=1),
            statut=RendezVous.Statut.DEMANDE,
        )
        self.confirme = RendezVous.objects.create(
            patient=self.autre_patient,
            medecin=self.medecin,
            date_heure=maintenant + datetime.timedelta(days=2),
            statut=RendezVous.Statut.CONFIRME,
        )
        self.client.login(username='admin-rdv@santesn.sn', password=PASSWORD)

    def test_liste_accessible_a_l_admin(self):
        reponse = self.client.get(reverse('liste_rendez_vous'))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'Mariama')
        self.assertContains(reponse, 'Ousmane')

    def test_filtre_par_statut(self):
        reponse = self.client.get(reverse('liste_rendez_vous'), {'statut': 'DEMANDE'})
        rendez_vous = list(reponse.context['rendez_vous'])
        self.assertEqual(rendez_vous, [self.demande])

    def test_recherche_par_nom_de_patient(self):
        reponse = self.client.get(reverse('liste_rendez_vous'), {'q': 'Mariama'})
        self.assertEqual(list(reponse.context['rendez_vous']), [self.demande])

    def test_role_non_admin_refuse(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'autre-medecin@santesn.sn')
        self.client.login(username='autre-medecin@santesn.sn', password=PASSWORD)
        reponse = self.client.get(reverse('liste_rendez_vous'))
        self.assertEqual(reponse.status_code, 403)

    def test_anonyme_redirige_vers_connexion(self):
        self.client.logout()
        reponse = self.client.get(reverse('liste_rendez_vous'))
        self.assertEqual(reponse.status_code, 302)
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```
python manage.py test Plateform_medicale.tests.ListeRendezVousAdminTests
```

Attendu : ÉCHEC avec `NoReverseMatch: Reverse for 'liste_rendez_vous' not found`.

- [ ] **Step 3 : Écrire la vue**

Dans `Plateform_medicale/views.py`, juste après la fonction
`liste_prises_en_charge` :

```python
@admin_required
def liste_rendez_vous(request):
    """Liste administrateur des rendez-vous, en lecture seule.

    L'administrateur suit le flux sans y intervenir : confirmer ou annuler
    un rendez-vous reste l'affaire du medecin (changer_statut_rendez_vous)
    et de l'assure (annuler_rendez_vous_assure).
    """
    rendez_vous = RendezVous.objects.select_related("patient", "medecin", "prestataire")

    recherche = request.GET.get("q", "").strip()
    if recherche:
        rendez_vous = rendez_vous.filter(
            Q(patient__nom__icontains=recherche)
            | Q(patient__prenom__icontains=recherche)
            | Q(medecin__nom__icontains=recherche)
            | Q(medecin__prenom__icontains=recherche)
        )

    statut = request.GET.get("statut", "")
    if statut:
        rendez_vous = rendez_vous.filter(statut=statut)

    rendez_vous = _trier(
        request,
        rendez_vous,
        ["date_heure", "patient__nom", "medecin__nom", "statut"],
        "-date_heure",
    )
    return render(
        request,
        "liste_rendez_vous.html",
        {
            "rendez_vous": _paginer(request, rendez_vous),
            "recherche": recherche,
            "statut_choisi": statut,
            "statuts": RendezVous.Statut.choices,
        },
    )
```

- [ ] **Step 4 : Déclarer la route**

Dans `Plateform_medicale/urls.py`, après la ligne
`path('prises-en-charge/<int:pk>/supprimer/', ...)` :

```python
    path('rendez-vous/', views.liste_rendez_vous, name='liste_rendez_vous'),
```

- [ ] **Step 5 : Créer le template**

Créer `Plateform_medicale/templates/liste_rendez_vous.html` :

```html
{% extends "base.html" %}
{% load formats icones %}

{% block title %}Rendez-vous{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Rendez-vous</h1>
        <p class="subtitle">Suivi des rendez-vous de la plateforme, en lecture seule.</p>
    </div>
</section>

<form method="get" class="filtres">
    <div style="min-width:220px;flex:1;">
        <label for="q">Recherche</label>
        <div class="champ-recherche">
            {% icone "search" %}
            <input id="q" type="text" name="q" placeholder="Nom du patient ou du médecin" value="{{ recherche }}" style="margin-bottom:0;">
        </div>
    </div>
    <div style="min-width:220px;">
        <label for="statut">Statut</label>
        <select id="statut" name="statut" style="margin-bottom:0;">
            <option value="">Tous</option>
            {% for value, label in statuts %}
            <option value="{{ value }}" {% if value == statut_choisi %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
        </select>
    </div>
    <button type="submit" class="button primary btn">Filtrer</button>
    {% if recherche or statut_choisi %}
    <a href="{% url 'liste_rendez_vous' %}" class="button btn">Réinitialiser</a>
    {% endif %}
</form>

{% if rendez_vous %}
<section class="panel">
    <table>
        <thead>
            <tr>
                {% entete_tri request.GET "date_heure" "Date et heure" %}
                {% entete_tri request.GET "patient__nom" "Patient" %}
                {% entete_tri request.GET "medecin__nom" "Médecin" %}
                <th scope="col">Prestataire</th>
                <th scope="col">Motif</th>
                {% entete_tri request.GET "statut" "Statut" %}
            </tr>
        </thead>
        <tbody>
            {% for rdv in rendez_vous %}
            <tr>
                <td>{{ rdv.date_heure|date:"d/m/Y H:i" }}</td>
                <td>{{ rdv.patient }}</td>
                <td>{{ rdv.medecin }}</td>
                <td>{{ rdv.prestataire|default:"—" }}</td>
                <td>{{ rdv.motif|default:"—" }}</td>
                <td><span class="badge {% if rdv.statut == 'CONFIRME' %}validee{% elif rdv.statut == 'ANNULE' %}refusee{% elif rdv.statut == 'DEMANDE' %}en_attente{% endif %}">{{ rdv.get_statut_display }}</span></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% if rendez_vous.paginator.num_pages > 1 %}
<nav class="pagination" aria-label="Pagination">
    {% if rendez_vous.has_previous %}
    <a href="?{% prefixe_pagination request.GET %}page={{ rendez_vous.previous_page_number }}" class="button btn btn-sm">{% icone "chevron-left" %} Précédent</a>
    {% endif %}
    <span class="pagination-info">Page {{ rendez_vous.number }} sur {{ rendez_vous.paginator.num_pages }}</span>
    {% if rendez_vous.has_next %}
    <a href="?{% prefixe_pagination request.GET %}page={{ rendez_vous.next_page_number }}" class="button btn btn-sm">Suivant {% icone "chevron-right" %}</a>
    {% endif %}
</nav>
{% endif %}
{% else %}
<div class="etat-vide">
    {% illustration_vide "calendar" %}
    <p>{% if recherche or statut_choisi %}Aucun rendez-vous ne correspond à ces critères.{% else %}Aucun rendez-vous enregistré.{% endif %}</p>
</div>
{% endif %}
{% endblock %}
```

Vérifier que `illustration_vide "calendar"` existe dans
`templatetags/icones.py` ; sinon utiliser une clé présente dans `_ICONES`.

- [ ] **Step 6 : Ajouter l'entrée de sidebar**

Dans `Plateform_medicale/templates/base.html`, juste après la ligne
`liste_prises_en_charge` (≈ 2294) :

```html
                <a href="{% url 'liste_rendez_vous' %}" aria-label="Rendez-vous" data-tooltip="Rendez-vous" class="{% if url_name == 'liste_rendez_vous' %}active{% endif %}">{% icone "calendar" %} <span class="nav-texte">Rendez-vous</span></a>
```

- [ ] **Step 7 : Lancer les tests**

```
python manage.py check
python manage.py test Plateform_medicale
```

Attendu : la suite complète passe, `ListeRendezVousAdminTests` compris.

- [ ] **Step 8 : Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/urls.py \
        Plateform_medicale/templates/liste_rendez_vous.html \
        Plateform_medicale/templates/base.html Plateform_medicale/tests.py
git commit -m "feat(admin): liste des rendez-vous en lecture seule"
```

---

### Task 2 : Page admin « Ordonnances » (lecture seule)

**Files:**
- Modify: `Plateform_medicale/views.py` (après `liste_rendez_vous`)
- Modify: `Plateform_medicale/urls.py`
- Create: `Plateform_medicale/templates/liste_ordonnances.html`
- Modify: `Plateform_medicale/templates/base.html` (entrée sidebar)
- Test: `Plateform_medicale/tests.py`

**Interfaces:**
- Consumes : `_trier`, `_paginer`, `admin_required`, helper de test
  `creer_ordonnance(patient, medecin)` et `creer_pharmacien(email)`.
- Produces : route nommée **`liste_ordonnances`**, paramètres GET
  `delivrance` (`oui` / `non`), `q`, `tri`, `page`. La Task 4 y renverra
  avec `?delivrance=non`.

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter à `Plateform_medicale/tests.py` :

```python
class ListeOrdonnancesAdminTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin-ord@santesn.sn')
        self.medecin = creer_medecin('medecin-ord@santesn.sn')
        self.patient = creer_patient(nom='Ba', prenom='Aminata')
        self.pharmacien = creer_pharmacien('pharmacien-ord@santesn.sn')
        self.non_delivree = creer_ordonnance(self.patient, self.medecin)
        self.delivree = creer_ordonnance(self.patient, self.medecin, medicaments='Ibuprofene')
        Delivrance.objects.create(ordonnance=self.delivree, pharmacien=self.pharmacien)
        self.client.login(username='admin-ord@santesn.sn', password=PASSWORD)

    def test_liste_accessible_a_l_admin(self):
        reponse = self.client.get(reverse('liste_ordonnances'))
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.context['ordonnances']), 2)

    def test_filtre_non_delivrees(self):
        reponse = self.client.get(reverse('liste_ordonnances'), {'delivrance': 'non'})
        self.assertEqual(list(reponse.context['ordonnances']), [self.non_delivree])

    def test_filtre_delivrees(self):
        reponse = self.client.get(reverse('liste_ordonnances'), {'delivrance': 'oui'})
        self.assertEqual(list(reponse.context['ordonnances']), [self.delivree])

    def test_recherche_par_code_qr(self):
        reponse = self.client.get(
            reverse('liste_ordonnances'), {'q': self.non_delivree.code_qr}
        )
        self.assertEqual(list(reponse.context['ordonnances']), [self.non_delivree])

    def test_role_non_admin_refuse(self):
        self.client.logout()
        self.client.login(username='pharmacien-ord@santesn.sn', password=PASSWORD)
        reponse = self.client.get(reverse('liste_ordonnances'))
        self.assertEqual(reponse.status_code, 403)
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```
python manage.py test Plateform_medicale.tests.ListeOrdonnancesAdminTests
```

Attendu : ÉCHEC `NoReverseMatch: Reverse for 'liste_ordonnances' not found`.

- [ ] **Step 3 : Écrire la vue**

Dans `Plateform_medicale/views.py`, après `liste_rendez_vous` :

```python
@admin_required
def liste_ordonnances(request):
    """Liste administrateur des ordonnances, en lecture seule.

    Le filtre "delivrance" repond a un angle mort : une ordonnance emise mais
    jamais retiree en pharmacie n'apparaissait sur aucun ecran. La validation
    d'une delivrance reste l'affaire du pharmacien (valider_delivrance) ; le
    QR n'est pas affiche ici, il n'a de sens qu'au comptoir.
    """
    ordonnances = Ordonnance.objects.select_related(
        "consultation__patient", "consultation__medecin", "delivrance__pharmacien"
    )

    recherche = request.GET.get("q", "").strip()
    if recherche:
        ordonnances = ordonnances.filter(
            Q(consultation__patient__nom__icontains=recherche)
            | Q(consultation__patient__prenom__icontains=recherche)
            | Q(code_qr__icontains=recherche)
        )

    delivrance = request.GET.get("delivrance", "")
    if delivrance == "non":
        ordonnances = ordonnances.filter(delivrance__isnull=True)
    elif delivrance == "oui":
        ordonnances = ordonnances.filter(delivrance__isnull=False)

    ordonnances = _trier(
        request,
        ordonnances,
        ["date_creation", "consultation__patient__nom", "code_qr"],
        "-date_creation",
    )
    return render(
        request,
        "liste_ordonnances.html",
        {
            "ordonnances": _paginer(request, ordonnances),
            "recherche": recherche,
            "delivrance_choisie": delivrance,
        },
    )
```

- [ ] **Step 4 : Déclarer la route**

Dans `Plateform_medicale/urls.py`, juste après la ligne `rendez-vous/` :

```python
    path('ordonnances/', views.liste_ordonnances, name='liste_ordonnances'),
```

- [ ] **Step 5 : Créer le template**

Créer `Plateform_medicale/templates/liste_ordonnances.html` :

```html
{% extends "base.html" %}
{% load formats icones %}

{% block title %}Ordonnances{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Ordonnances</h1>
        <p class="subtitle">Suivi des ordonnances émises et de leur délivrance en pharmacie.</p>
    </div>
</section>

<form method="get" class="filtres">
    <div style="min-width:220px;flex:1;">
        <label for="q">Recherche</label>
        <div class="champ-recherche">
            {% icone "search" %}
            <input id="q" type="text" name="q" placeholder="Nom du patient ou code de vérification" value="{{ recherche }}" style="margin-bottom:0;">
        </div>
    </div>
    <div style="min-width:220px;">
        <label for="delivrance">Délivrance</label>
        <select id="delivrance" name="delivrance" style="margin-bottom:0;">
            <option value="">Toutes</option>
            <option value="non" {% if delivrance_choisie == "non" %}selected{% endif %}>Non délivrées</option>
            <option value="oui" {% if delivrance_choisie == "oui" %}selected{% endif %}>Délivrées</option>
        </select>
    </div>
    <button type="submit" class="button primary btn">Filtrer</button>
    {% if recherche or delivrance_choisie %}
    <a href="{% url 'liste_ordonnances' %}" class="button btn">Réinitialiser</a>
    {% endif %}
</form>

{% if ordonnances %}
<section class="panel">
    <table>
        <thead>
            <tr>
                {% entete_tri request.GET "date_creation" "Émise le" %}
                {% entete_tri request.GET "consultation__patient__nom" "Patient" %}
                <th scope="col">Médecin</th>
                {% entete_tri request.GET "code_qr" "Code" %}
                <th scope="col">Délivrance</th>
            </tr>
        </thead>
        <tbody>
            {% for ordonnance in ordonnances %}
            <tr>
                <td>{{ ordonnance.date_creation|date:"d/m/Y" }}</td>
                <td>{{ ordonnance.consultation.patient }}</td>
                <td>{{ ordonnance.consultation.medecin }}</td>
                <td class="code">{{ ordonnance.code_qr }}</td>
                <td>
                    {% if ordonnance.delivrance %}
                    <span class="badge validee">Délivrée le {{ ordonnance.delivrance.date_delivrance|date:"d/m/Y" }}</span>
                    {% else %}
                    <span class="badge en_attente">Non délivrée</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% if ordonnances.paginator.num_pages > 1 %}
<nav class="pagination" aria-label="Pagination">
    {% if ordonnances.has_previous %}
    <a href="?{% prefixe_pagination request.GET %}page={{ ordonnances.previous_page_number }}" class="button btn btn-sm">{% icone "chevron-left" %} Précédent</a>
    {% endif %}
    <span class="pagination-info">Page {{ ordonnances.number }} sur {{ ordonnances.paginator.num_pages }}</span>
    {% if ordonnances.has_next %}
    <a href="?{% prefixe_pagination request.GET %}page={{ ordonnances.next_page_number }}" class="button btn btn-sm">Suivant {% icone "chevron-right" %}</a>
    {% endif %}
</nav>
{% endif %}
{% else %}
<div class="etat-vide">
    {% illustration_vide "qr-scan" %}
    <p>{% if recherche or delivrance_choisie %}Aucune ordonnance ne correspond à ces critères.{% else %}Aucune ordonnance enregistrée.{% endif %}</p>
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 6 : Ajouter l'entrée de sidebar**

Dans `base.html`, après l'entrée `liste_rendez_vous` ajoutée en Task 1 :

```html
                <a href="{% url 'liste_ordonnances' %}" aria-label="Ordonnances" data-tooltip="Ordonnances" class="{% if url_name == 'liste_ordonnances' %}active{% endif %}">{% icone "qr-scan" %} <span class="nav-texte">Ordonnances</span></a>
```

- [ ] **Step 7 : Lancer les tests**

```
python manage.py check
python manage.py test Plateform_medicale
```

- [ ] **Step 8 : Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/urls.py \
        Plateform_medicale/templates/liste_ordonnances.html \
        Plateform_medicale/templates/base.html Plateform_medicale/tests.py
git commit -m "feat(admin): liste des ordonnances avec filtre de delivrance"
```

---

### Task 3 : Barre supérieure dans le shell

**Files:**
- Modify: `Plateform_medicale/views.py:138-147` (fonction `user_role`)
- Modify: `Plateform_medicale/templates/base.html` (HTML du shell + CSS)
- Test: `Plateform_medicale/tests.py`

**Interfaces:**
- Consumes : routes `liste_utilisateurs`, `mes_notifications`,
  `changer_mot_de_passe`, `logout` (toutes existantes).
- Produces : clés de contexte **`nb_prises_en_charge_attente`**,
  **`nb_paiements_non_regles`** (ADMIN uniquement) ajoutées par `user_role`,
  et un bloc `<header class="topbar">` dans `base.html` utilisable par les
  quatre rôles.

**Note :** le processeur de contexte `user_role` **existe déjà** (views.py:138)
et fournit déjà `notifications_non_lues`. Il est **étendu**, pas remplacé, et
il est déjà enregistré dans `config/settings.py:70` — ne pas y toucher.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
class ContexteShellTests(TestCase):
    def test_admin_recoit_les_compteurs_de_file(self):
        creer_utilisateur(User.Role.ADMIN, 'admin-shell@santesn.sn')
        patient = creer_patient(nom='Ndour', prenom='Khady')
        PriseEnCharge.objects.create(patient=patient, motif='Test', statut='en_attente')
        self.client.login(username='admin-shell@santesn.sn', password=PASSWORD)
        reponse = self.client.get(reverse('dashboard'))
        self.assertEqual(reponse.context['nb_prises_en_charge_attente'], 1)
        self.assertEqual(reponse.context['nb_paiements_non_regles'], 0)

    def test_non_admin_n_a_pas_les_compteurs_admin(self):
        creer_medecin('medecin-shell@santesn.sn')
        self.client.login(username='medecin-shell@santesn.sn', password=PASSWORD)
        reponse = self.client.get(reverse('dashboard_medecin'))
        self.assertIsNone(reponse.context.get('nb_prises_en_charge_attente'))

    def test_anonyme_ne_declenche_aucune_requete_de_compteur(self):
        from .views import user_role
        requete = MagicMock()
        requete.user.is_authenticated = False
        contexte = user_role(requete)
        self.assertIsNone(contexte.get('nb_prises_en_charge_attente'))
        self.assertEqual(contexte['notifications_non_lues'], 0)
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```
python manage.py test Plateform_medicale.tests.ContexteShellTests
```

Attendu : ÉCHEC — `nb_prises_en_charge_attente` absent du contexte.

- [ ] **Step 3 : Étendre `user_role`**

Remplacer la fonction `user_role` (views.py:138-147) par :

```python
def user_role(request):
    """Context processor : role, notifications non lues, et compteurs de file
    d'attente pour les pastilles de la sidebar administrateur.

    Les compteurs admin portent sur des champs indexes (statut) et ne sont
    calcules que pour le role ADMIN : les autres roles n'ont pas ces ecrans,
    et un visiteur anonyme ne declenche aucune requete."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'current_role': None, 'current_role_label': None, 'notifications_non_lues': 0}

    contexte = {
        'current_role': user.role,
        'current_role_label': user.get_role_display(),
        'notifications_non_lues': user.notifications.filter(lue=False).count(),
    }
    if user.role == User.Role.ADMIN:
        contexte['nb_prises_en_charge_attente'] = PriseEnCharge.objects.filter(
            statut='en_attente'
        ).count()
        contexte['nb_paiements_non_regles'] = Paiement.objects.filter(
            statut=Paiement.Statut.NON_REGLE
        ).count()
    return contexte
```

- [ ] **Step 4 : Lancer les tests pour vérifier qu'ils passent**

```
python manage.py test Plateform_medicale.tests.ContexteShellTests
```

- [ ] **Step 5 : Ajouter la barre supérieure dans `base.html`**

Insérer, dans le conteneur de contenu principal, juste avant le bloc qui rend
`{% block content %}`, le balisage suivant. Repérer d'abord la structure
existante (`<main>` / `.contenu`) et poser la barre en premier enfant :

```html
<header class="topbar">
    <button type="button" class="topbar-tiroir" aria-label="Ouvrir le menu" data-ouvrir-tiroir>{% icone "menu" %}</button>
    <nav class="fil-ariane" aria-label="Fil d'ariane">
        <span>{{ current_role_label }}</span>
        <span aria-hidden="true">/</span>
        <b>{% block titre_page %}Tableau de bord{% endblock %}</b>
    </nav>
    {% if current_role == "ADMIN" %}
    <form class="topbar-recherche" method="get" action="{% url 'liste_utilisateurs' %}" role="search">
        <label class="sr-only" for="recherche-globale">Rechercher un utilisateur</label>
        {% icone "search" %}
        <input id="recherche-globale" type="search" name="q" placeholder="Rechercher un utilisateur">
    </form>
    {% endif %}
    <a class="topbar-bouton" href="{% url 'mes_notifications' %}" aria-label="Notifications{% if notifications_non_lues %} : {{ notifications_non_lues }} non lue(s){% endif %}">
        {% icone "bell" %}
        {% if notifications_non_lues %}<span class="topbar-pastille">{{ notifications_non_lues }}</span>{% endif %}
    </a>
    <a class="topbar-compte" href="{% url 'changer_mot_de_passe' %}">
        <span class="topbar-avatar" aria-hidden="true">{{ user.get_full_name|default:user.email|slice:":2"|upper }}</span>
        <span class="topbar-identite">
            <b>{{ user.get_full_name|default:user.email }}</b>
            <span>{{ current_role_label }}</span>
        </span>
    </a>
</header>
```

Contraintes de câblage à vérifier avant de valider cette étape :

- Le bouton `data-ouvrir-tiroir` doit réutiliser **le gestionnaire de tiroir
  mobile déjà présent** dans `base.html` ; si le bouton existant vit ailleurs
  dans le DOM, le déplacer ici plutôt que d'en créer un second.
- `mes_notifications` est la vue de consultation (tous rôles) ; l'entrée de
  sidebar admin pointe vers `envoyer_notification`, ne pas les confondre.
- Ajouter une classe `.sr-only` si elle n'existe pas déjà dans la feuille.

- [ ] **Step 6 : Ajouter le CSS de la barre supérieure**

Dans le `<style>` de `base.html`, à la suite des règles de shell existantes :

```css
        .topbar {
            position: sticky;
            top: 0;
            z-index: 20;
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 11px 26px;
            background: rgba(242, 246, 246, 0.92);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
        }

        .fil-ariane {
            display: flex;
            align-items: center;
            gap: 7px;
            font-size: 11.5px;
            font-weight: 600;
            color: var(--muted);
        }

        .fil-ariane b { color: var(--primary-dark); font-weight: 700; }

        .topbar-recherche {
            position: relative;
            margin-left: auto;
            width: min(300px, 34vw);
        }

        .topbar-recherche .icone-nav {
            position: absolute;
            left: 11px;
            top: 50%;
            transform: translateY(-50%);
            width: 16px;
            height: 16px;
            color: var(--muted);
            pointer-events: none;
        }

        .topbar-recherche input {
            width: 100%;
            margin-bottom: 0;
            padding-left: 34px;
            font-size: 13px;
        }

        .topbar-bouton {
            position: relative;
            display: grid;
            place-items: center;
            width: 34px;
            height: 34px;
            border: 1px solid var(--border);
            border-radius: 9px;
            background: #ffffff;
            color: var(--muted);
        }

        .topbar-bouton:hover { border-color: var(--primary); color: var(--primary); }

        .topbar-pastille {
            position: absolute;
            top: -5px;
            right: -5px;
            min-width: 17px;
            height: 17px;
            padding: 0 4px;
            border-radius: 9px;
            border: 2px solid var(--page-bg, #f2f6f6);
            background: var(--accent);
            color: #ffffff;
            font-size: 10px;
            font-weight: 800;
            line-height: 13px;
            text-align: center;
            font-variant-numeric: tabular-nums;
        }

        .topbar-compte { display: flex; align-items: center; gap: 9px; }

        .topbar-avatar {
            display: grid;
            place-items: center;
            width: 34px;
            height: 34px;
            border-radius: 9px;
            background: var(--primary-dark);
            color: #ffffff;
            font-size: 12px;
            font-weight: 800;
        }

        .topbar-identite b { display: block; font-size: 12.5px; color: var(--primary-dark); }
        .topbar-identite span { font-size: 11px; color: var(--muted); }

        .topbar-tiroir { display: none; }

        .sr-only {
            position: absolute;
            width: 1px; height: 1px;
            padding: 0; margin: -1px;
            overflow: hidden;
            clip: rect(0 0 0 0);
            white-space: nowrap;
        }

        @media (max-width: 900px) {
            .topbar { padding: 10px 16px; gap: 10px; }
            .fil-ariane, .topbar-identite { display: none; }
            .topbar-recherche { margin-left: auto; width: auto; flex: 1; }
            .topbar-tiroir {
                display: grid;
                place-items: center;
                width: 34px; height: 34px;
                border: 1px solid var(--border);
                border-radius: 9px;
                background: #ffffff;
                color: var(--primary-dark);
            }
        }
```

Adapter les noms de variables (`--border`, `--muted`, `--page-bg`) à ceux qui
existent réellement dans `base.html` : les relever avant d'écrire, ne pas en
inventer.

- [ ] **Step 7 : Vérifier le rendu réellement**

```
python manage.py test Plateform_medicale
```

puis capture visuelle sur les 4 rôles, au minimum admin et médecin :

```
cd <scratchpad> && MSYS_NO_PATHCONV=1 python capture.py /tableau-de-bord/ shell_1440.png 1440 900
cd <scratchpad> && MSYS_NO_PATHCONV=1 python capture.py /tableau-de-bord/ shell_390.png 390 800
```

Vérifier à l'œil : la barre ne recouvre pas le titre de page, le tiroir mobile
s'ouvre toujours, la pastille de notification ne déborde pas.

- [ ] **Step 8 : Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/templates/base.html \
        Plateform_medicale/tests.py
git commit -m "feat(shell): barre superieure avec recherche, notifications et compte"
```

---

### Task 4 : Refonte de `dashboard.html` et de la vue `dashboard()`

**Files:**
- Modify: `Plateform_medicale/views.py:291-390` (vue `dashboard`)
- Modify: `Plateform_medicale/templates/dashboard.html` (réécriture)
- Modify: `Plateform_medicale/templates/base.html` (CSS des nouveaux blocs)
- Test: `Plateform_medicale/tests.py`

**Interfaces:**
- Consumes : routes `liste_rendez_vous` (Task 1), `liste_ordonnances`
  (Task 2), et les routes existantes `liste_prises_en_charge`,
  `liste_paiements`, `liste_prestataires`, `liste_patients`,
  `liste_medecins`, `liste_pharmaciens`, `liste_utilisateurs`, `rapports`.
- Produces : dashboard final. Aucune tâche ultérieure n'en dépend.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
class DashboardAdminContexteTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin-dash@santesn.sn')
        self.medecin = creer_medecin('medecin-dash@santesn.sn')
        self.patient = creer_patient(nom='Diallo', prenom='Abdoulaye')
        Patient.objects.create(
            nom='Diallo', prenom='Fatou',
            date_naissance=datetime.date(2015, 5, 5),
            telephone='770000002',
            type_beneficiaire=Patient.TypeBeneficiaire.ENFANT,
            assure_principal=self.patient,
        )
        creer_ordonnance(self.patient, self.medecin)
        RendezVous.objects.create(
            patient=self.patient, medecin=self.medecin,
            date_heure=timezone.now() + datetime.timedelta(days=1),
            statut=RendezVous.Statut.DEMANDE,
        )
        Prestataire.objects.create(nom='Hopital Test', type_prestataire='HOPITAL', ville='Dakar')
        self.client.login(username='admin-dash@santesn.sn', password=PASSWORD)

    def test_nouvelles_cles_de_contexte(self):
        contexte = self.client.get(reverse('dashboard')).context
        self.assertEqual(contexte['rdv_a_confirmer'], 1)
        self.assertEqual(contexte['ordonnances_non_delivrees'], 1)
        self.assertEqual(contexte['patients_principaux'], 1)
        self.assertEqual(contexte['ayants_droit'], 1)
        self.assertEqual(contexte['assures_sans_plan'], 1)
        self.assertEqual(contexte['medecins_sans_prestataire'], 1)
        self.assertEqual(contexte['prestataires_sans_coordonnees'], 1)

    def test_base_vide_se_rend_sans_erreur(self):
        Ordonnance.objects.all().delete()
        Consultation.objects.all().delete()
        RendezVous.objects.all().delete()
        Patient.objects.all().delete()
        Medecin.objects.all().delete()
        Prestataire.objects.all().delete()
        reponse = self.client.get(reverse('dashboard'))
        self.assertEqual(reponse.status_code, 200)

    def test_non_admin_refuse(self):
        self.client.logout()
        self.client.login(username='medecin-dash@santesn.sn', password=PASSWORD)
        reponse = self.client.get(reverse('dashboard'))
        self.assertEqual(reponse.status_code, 403)
```

Vérifier les valeurs exactes de `Patient.TypeBeneficiaire` et de
`Prestataire.Type` dans `models.py` avant de figer ce test ; ajuster les
constantes si les libellés diffèrent.

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```
python manage.py test Plateform_medicale.tests.DashboardAdminContexteTests
```

Attendu : ÉCHEC — `KeyError: 'rdv_a_confirmer'`.

- [ ] **Step 3 : Enrichir la vue `dashboard()`**

Dans `Plateform_medicale/views.py`, à l'intérieur de `dashboard()`, avant la
construction de `contexte`, ajouter :

```python
    # Un seul aller-retour pour les trois comptages de Patient, plutot que
    # trois count() distincts sur la meme table.
    repartition_patients = Patient.objects.aggregate(
        total=Count("id"),
        principaux=Count("id", filter=Q(type_beneficiaire=Patient.TypeBeneficiaire.PRINCIPAL)),
        sans_plan=Count(
            "id",
            filter=Q(
                type_beneficiaire=Patient.TypeBeneficiaire.PRINCIPAL,
                plan_couverture__isnull=True,
            ),
        ),
    )
    patients_principaux = repartition_patients["principaux"]
    ayants_droit = repartition_patients["total"] - patients_principaux

    # Angle mort jusqu'ici : une ordonnance emise mais jamais retiree en
    # pharmacie n'apparaissait sur aucun ecran (cf. liste_ordonnances).
    ordonnances_non_delivrees = Ordonnance.objects.filter(delivrance__isnull=True).count()
    rdv_a_confirmer = RendezVous.objects.filter(statut=RendezVous.Statut.DEMANDE).count()
    paiements_non_regles_nb = Paiement.objects.filter(statut=Paiement.Statut.NON_REGLE).count()
    prestataires_par_type = list(
        Prestataire.objects.values("type_prestataire")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
```

Puis ajouter au dictionnaire `contexte` :

```python
        "patients_principaux": patients_principaux,
        "ayants_droit": ayants_droit,
        "assures_sans_plan": repartition_patients["sans_plan"],
        "ordonnances_non_delivrees": ordonnances_non_delivrees,
        "total_delivrances": Delivrance.objects.count(),
        "rdv_a_confirmer": rdv_a_confirmer,
        "paiements_non_regles_nb": paiements_non_regles_nb,
        "montant_total_facture": montant_total_paiements,
        "medecins_sans_prestataire": Medecin.objects.filter(prestataire__isnull=True).count(),
        "pharmaciens_sans_prestataire": Pharmacien.objects.filter(prestataire__isnull=True).count(),
        "prestataires_sans_coordonnees": Prestataire.objects.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        ).count(),
        "prestataires_par_type": prestataires_par_type,
        "file_totale": (
            total_prises_en_charge_attente + rdv_a_confirmer
            + ordonnances_non_delivrees + paiements_non_regles_nb
        ),
```

`total_prises_en_charge_attente` est aujourd'hui calculé en ligne dans le
dictionnaire : l'extraire dans une variable locale au-dessus pour pouvoir le
réutiliser dans `file_totale`.

Modifier enfin `dernieres_prises_en_charge` pour faire remonter les demandes
en attente :

```python
    dernieres_prises_en_charge = (
        PriseEnCharge.objects.select_related("patient")
        .annotate(
            priorite=Case(
                When(statut="en_attente", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("priorite", "-date_demande")[:5]
    )
```

`Case`, `When`, `Value`, `IntegerField` et `Count` sont **déjà importés** en
haut de `views.py` (ligne 24) — ne pas ajouter d'import.

- [ ] **Step 4 : Lancer les tests de contexte**

```
python manage.py test Plateform_medicale.tests.DashboardAdminContexteTests
```

Attendu : les trois tests passent.

- [ ] **Step 5 : Réécrire `dashboard.html`**

Structure imposée, de haut en bas (le détail de contenu est en spec §6) :

1. `.page-title` — titre + date du jour.
2. `<section class="file-attente">` (fond `--primary-dark`, coins arrondis) —
   4 tuiles `<a>` vers, dans l'ordre :
   `liste_prises_en_charge?statut=en_attente`,
   `liste_rendez_vous?statut=DEMANDE`,
   `liste_ordonnances?delivrance=non`,
   `liste_paiements?statut=non_regle`.
   La tuile prises en charge reçoit la classe `urgent` si
   `jours_attente_max > 7`. Si `file_totale == 0`, rendre à la place un état
   vide « Rien en attente. ».
3. `<section class="bande-couverture">` — carte Paiements (montant principal,
   « En attente », « Facturé au total » = `montant_total_facture`, sparkline
   Chart.js existante avec légende **sous** le graphique) + carte Assurés
   couverts (total, barre à deux segments `patients_principaux` /
   `ayants_droit`, légende chiffrée, alerte si `assures_sans_plan`).
4. `<section class="kpis">` — 5 cartes selon la spec §6.5.
5. `<section class="duo">` — prises en charge récentes (avec ancienneté) +
   derniers comptes créés (badge de rôle, sous-titre
   « {{ total_comptes_actifs }} actifs, {{ total_comptes_inactifs }} désactivés »).
6. `<section class="bas">` — Fiches à compléter (4 entrées, chacune masquée si
   son compteur est nul, panneau entier masqué si les 4 le sont) + Actions
   rapides (6 boutons avec icônes).

Supprimer : `.dc-hero-trace` (le tracé qui traverse le texte), la carte
`.governance-card` (absorbée par le sous-titre des derniers comptes), et le
bandeau `.dc-status` (remplacé par la file d'attente).

Conserver tel quel le bloc `<script>` de la sparkline, en corrigeant
uniquement la position de la légende.

- [ ] **Step 6 : Écrire le CSS des nouveaux blocs**

Dans `base.html`, remplacer les règles `.dash-command` devenues inutiles par
les nouvelles classes. Points de rupture imposés (spec §9) : 1180 px,
900 px, 640 px. Ajouter le bloc `prefers-reduced-motion` s'il est absent :

```css
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.001ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.001ms !important;
            }
        }
```

- [ ] **Step 7 : Vérifier visuellement et par les tests**

```
python manage.py check
python manage.py test Plateform_medicale
cd <scratchpad> && MSYS_NO_PATHCONV=1 python capture.py /tableau-de-bord/ dash_1440.png 1440 900
cd <scratchpad> && MSYS_NO_PATHCONV=1 python capture.py /tableau-de-bord/ dash_390.png 390 800
```

Lire les deux captures et vérifier : aucun élément décoratif ne croise du
texte, aucune carte n'a plus de 25 % de hauteur vide, les titres de panneau
ne se cassent pas à côté de leur bouton.

- [ ] **Step 8 : Commit**

```bash
git add Plateform_medicale/views.py Plateform_medicale/templates/dashboard.html \
        Plateform_medicale/templates/base.html Plateform_medicale/tests.py
git commit -m "feat(dashboard-admin): refonte clinique claire orientee file d'attente"
```

---

### Task 5 : Passe de finition et documentation

**Files:**
- Modify: `Plateform_medicale/templates/base.html` (contrastes, focus)
- Modify: `FONCTIONNEMENT.txt`
- Modify: `CLAUDE.md`
- Modify: `GUIDE_UTILISATEUR.md`

**Interfaces:**
- Consumes : l'état livré par les tâches 1 à 4.
- Produces : documentation à jour. Terminal.

- [ ] **Step 1 : Vérifier les contrastes**

Pour chacun des 4 couples sémantiques de la spec §5 et pour le texte discret
sur le bandeau navy, calculer le ratio :

```
cd <scratchpad> && python -c "
def lum(h):
    c=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    c=[v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4 for v in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def ratio(a,b):
    la,lb=sorted([lum(a),lum(b)],reverse=True)
    return round((la+0.05)/(lb+0.05),2)
for nom,t,f in [('regle','#1f8a5c','#e6f5ee'),('attente','#9a6a10','#fdf3e0'),
                ('refuse','#b3352b','#fbebe9'),('neutre','#6b858c','#eef3f3')]:
    print(nom, ratio(t,f))
"
```

Tout couple sous 4.5 doit être assombri jusqu'à l'atteindre. Corriger dans
`base.html`.

- [ ] **Step 2 : Vérifier le focus clavier**

Naviguer au clavier sur le dashboard et les deux nouvelles pages : chaque
lien, bouton, champ et tuile doit montrer l'anneau de focus. Corriger tout
élément qui l'a perdu.

- [ ] **Step 3 : Lancer la suite complète une dernière fois**

```
python manage.py check
python manage.py test Plateform_medicale
```

- [ ] **Step 4 : Mettre à jour `FONCTIONNEMENT.txt`**

Ajouter, dans la section consacrée au poste de pilotage : la dixième passe
(refonte « Clinique claire »), les deux nouvelles vues et leurs filtres GET,
l'extension de `user_role`, et la nouvelle organisation de la sidebar.
Vérifier qu'aucun paragraphe antérieur n'est contredit sans être corrigé —
c'est l'erreur qu'ont commise les 8ᵉ et 9ᵉ passes.

- [ ] **Step 5 : Mettre à jour `CLAUDE.md`**

Ajouter `liste_rendez_vous` et `liste_ordonnances` à la description du
Dashboard Administrateur (phase 5), et mentionner la barre supérieure dans la
section « Design system ».

- [ ] **Step 6 : Mettre à jour `GUIDE_UTILISATEUR.md`**

Décrire les deux nouveaux écrans dans la partie Administrateur.

- [ ] **Step 7 : Commit**

```bash
git add FONCTIONNEMENT.txt CLAUDE.md GUIDE_UTILISATEUR.md \
        Plateform_medicale/templates/base.html
git commit -m "docs(dashboard-admin): reporte la refonte dans la documentation"
```

- [ ] **Step 8 : Nettoyage de fin de chantier**

- Supprimer le compte de capture jetable
  (`audit-capture-jetable@santesn.local`).
- Arrêter le serveur de développement lancé pour les captures.
- Supprimer `docs/superpowers/` une fois la refonte validée (politique du
  projet : les specs et plans sont temporaires, `FONCTIONNEMENT.txt` est le
  document durable).
- Décider du sort de `stash@{0}` avec l'utilisateur.

---

## Auto-revue du plan

**Couverture de la spec :**

| Section de spec | Tâche |
|---|---|
| §6.1 barre supérieure | Task 3 |
| §6.2 bandeau « À traiter » | Task 4 step 5 |
| §6.3 carte Paiements | Task 4 step 5 |
| §6.4 carte Assurés | Task 4 steps 3+5 |
| §6.5 cartes KPI | Task 4 step 5 |
| §6.6 listes | Task 4 steps 3+5 |
| §6.7 fiches à compléter | Task 4 steps 3+5 |
| §6.8 actions rapides | Task 4 step 5 |
| §6.9 deux pages admin | Tasks 1 et 2 |
| §7 données | Task 4 step 3 |
| §8 processeur de contexte | Task 3 step 3 |
| §9 responsive | Tasks 3 step 6, 4 step 6 |
| §10 animations | Task 4 step 6 |
| §11 accessibilité | Task 5 steps 1-2 |
| §12 tests | Tasks 1, 2, 3, 4 |
| §13 vérification visuelle | Tasks 3 step 7, 4 step 7 |

**Écart assumé :** la spec §8 prévoyait quatre compteurs de sidebar
(`nb_rdv_a_confirmer` et `nb_ordonnances_non_delivrees` compris). Le plan n'en
retient que deux (prises en charge, paiements) : la spec elle-même prévoyait
ce repli si le coût devenait sensible, et deux `COUNT` sur chaque page admin
valent mieux que quatre pour un gain de lisibilité marginal. Les deux autres
chiffres restent affichés sur le dashboard.

**Correction apportée à la spec :** §8 décrivait la création d'une fonction
`contexte_global`. Le processeur `user_role` **existe déjà** (views.py:138) et
fournit déjà `notifications_non_lues` ; il est étendu au lieu d'être doublé.
Aucun enregistrement à ajouter dans `config/settings.py`.
