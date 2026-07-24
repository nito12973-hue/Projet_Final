# Scan QR par caméra — écran pharmacien — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un scan QR par caméra sur `scanner_ordonnance.html` (dashboard Pharmacien) pour honorer la promesse "scan" du landing page, sans casser la saisie manuelle/douchette existante.

**Architecture:** Changement strictement côté client (template + JS inline). Le code décodé par la caméra est écrit dans le même champ `#code_qr` que la saisie manuelle, puis le formulaire existant est soumis normalement (`requestSubmit()`) — aucun changement de `views.py`, `urls.py` ou `models.py`. Bouton "Scanner avec la caméra" masqué par défaut, affiché uniquement si le navigateur supporte `getUserMedia` et que `jsQR` a bien chargé.

**Tech Stack:** Django templates, JavaScript vanilla (IIFE, style ES5 `var`, cohérent avec `base.html`/`ajouter_prestataire.html`), librairie `jsQR` via CDN jsdelivr.

## Global Constraints

- Librairie de décodage : `jsQR` v1.4.0 via `https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js`, `integrity="sha384-b5Ya4Bq3qCyz39m2ISh+4DxjAIljdeFwK/BsXLuj9gugaNwAcj/ia15fxNZL9Nlx"`, `crossorigin="anonymous"` — valeurs vérifiées (téléchargement réel + calcul sha384 le 2026-07-24), ne pas modifier sans re-générer le hash.
- Bouton d'activation caméra **explicite** (clic requis) — jamais de démarrage automatique de la caméra au chargement de la page.
- Après détection d'un code : arrêt immédiat de la caméra puis **soumission automatique** du formulaire (`requestSubmit()`, pas `submit()` — `requestSubmit()` déclenche l'évènement `submit` global écouté par `base.html` pour la barre de chargement de navigation ; `submit()` ne le fait pas).
- Jamais d'`alert()`/`confirm()` natif : toute erreur (permission refusée, pas de caméra, contexte non sécurisé) s'affiche dans la zone de statut `role="status" aria-live="polite"` déjà utilisée comme pattern (voir `ajouter_prestataire.html`).
- Aucun changement de `Plateform_medicale/views.py`, `urls.py`, `models.py` : le contrat POST `code_qr` → vue `scanner_ordonnance` reste identique.
- Hors périmètre (YAGNI, ne pas ajouter) : sélecteur multi-caméra, lecture de codes-barres 1D, torche/flash.

---

### Task 1: Bouton de scan caméra avec détection de capacité (masqué par défaut)

**Files:**
- Modify: `Plateform_medicale/templates/scanner_ordonnance.html`
- Test: `Plateform_medicale/tests.py`

**Interfaces:**
- Consumes: rien (nouveau bouton autonome dans un template existant).
- Produces: élément `#bouton-scan-camera` (attribut `hidden` par défaut, retiré par JS si la caméra est utilisable) ; élément `#statut-scan-camera` (zone de statut, vide au chargement) — consommés par la Task 2.

- [ ] **Step 1: Écrire le test qui vérifie le script CDN et le bouton masqué**

Dans `Plateform_medicale/tests.py`, trouver la classe `EspacePharmacienTests` (contient déjà `test_scan_code_valide_affiche_ordonnance` et `test_scan_code_invalide_affiche_erreur`, autour de la ligne 630). Ajouter juste après `test_scan_code_invalide_affiche_erreur` :

```python
    def test_scan_camera_script_et_bouton_presents(self):
        """Plan de direction artistique, item 8 : scan QR par camera."""
        response = self.client.get(reverse('scanner_ordonnance'))
        self.assertContains(
            response,
            'src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"',
        )
        self.assertContains(
            response,
            'integrity="sha384-b5Ya4Bq3qCyz39m2ISh+4DxjAIljdeFwK/BsXLuj9gugaNwAcj/ia15fxNZL9Nlx"',
        )
        self.assertContains(
            response,
            '<button type="button" id="bouton-scan-camera" class="button btn" hidden>',
        )
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python manage.py test Plateform_medicale.tests.EspacePharmacienTests.test_scan_camera_script_et_bouton_presents -v 2`
Expected: FAIL (le bouton et le script n'existent pas encore dans le template)

- [ ] **Step 3: Ajouter `{% load icones %}` et le bouton dans le formulaire**

Dans `Plateform_medicale/templates/scanner_ordonnance.html`, remplacer les deux premières lignes :

```html
{% extends "base.html" %}

{% block title %}Scanner un QR Code{% endblock %}
```

par :

```html
{% extends "base.html" %}
{% load icones %}

{% block title %}Scanner un QR Code{% endblock %}
```

Puis remplacer le bloc `<form>` :

```html
<form method="post" style="max-width: 480px;">
    {% csrf_token %}
    <label for="code_qr">Code de l'ordonnance</label>
    <input id="code_qr" name="code_qr" type="text" placeholder="RX-XXXXXXXXXX" autofocus required>
    <button class="button primary" type="submit">Verifier</button>
</form>
```

par :

```html
<form method="post" style="max-width: 480px;">
    {% csrf_token %}
    <label for="code_qr">Code de l'ordonnance</label>
    <input id="code_qr" name="code_qr" type="text" placeholder="RX-XXXXXXXXXX" autofocus required>
    <button class="button primary" type="submit">Verifier</button>

    <div style="margin-top:16px;">
        <button type="button" id="bouton-scan-camera" class="button btn" hidden>{% icone "qr-scan" %} Scanner avec la camera</button>
        <p id="statut-scan-camera" class="subtitle" style="margin:8px 0 0;" role="status" aria-live="polite"></p>
    </div>
</form>
```

À la toute fin du fichier, juste avant `{% endblock %}`, ajouter le script CDN et le script de détection de capacité :

```html
<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js" integrity="sha384-b5Ya4Bq3qCyz39m2ISh+4DxjAIljdeFwK/BsXLuj9gugaNwAcj/ia15fxNZL9Nlx" crossorigin="anonymous"></script>
<script>
    (function () {
        var boutonScan = document.getElementById('bouton-scan-camera');
        var cameraDisponible = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        if (cameraDisponible && typeof jsQR === 'function' && boutonScan) {
            boutonScan.hidden = false;
        }
    })();
</script>
```

Le fichier complet doit ressembler à :

```html
{% extends "base.html" %}
{% load icones %}

{% block title %}Scanner un QR Code{% endblock %}

{% block content %}
<section class="page-title">
    <div>
        <h1>Scanner un QR Code</h1>
        <p class="subtitle">Saisissez ou scannez le code affiche sur l'ordonnance du patient.</p>
    </div>
</section>

<form method="post" style="max-width: 480px;">
    {% csrf_token %}
    <label for="code_qr">Code de l'ordonnance</label>
    <input id="code_qr" name="code_qr" type="text" placeholder="RX-XXXXXXXXXX" autofocus required>
    <button class="button primary" type="submit">Verifier</button>

    <div style="margin-top:16px;">
        <button type="button" id="bouton-scan-camera" class="button btn" hidden>{% icone "qr-scan" %} Scanner avec la camera</button>
        <p id="statut-scan-camera" class="subtitle" style="margin:8px 0 0;" role="status" aria-live="polite"></p>
    </div>
</form>

{% if ordonnance %}
<section class="admin-layout" style="margin-top: 22px;">
    <article class="panel" style="padding: 24px;">
        <h2 style="margin-top:0;color:var(--primary-dark);">Ordonnance {{ ordonnance.code_qr }}</h2>
        <p><strong>Patient :</strong> {{ ordonnance.consultation.patient }}</p>
        <p><strong>Medecin :</strong> {{ ordonnance.consultation.medecin }}</p>
        <p><strong>Date :</strong> {{ ordonnance.date_creation|date:"d/m/Y H:i" }}</p>
        <p><strong>Medicaments :</strong></p>
        <p style="white-space: pre-line;">{{ ordonnance.medicaments }}</p>
    </article>

    <aside class="panel governance-card">
        {% if ordonnance.delivrance %}
        <h2>Deja delivree</h2>
        <p class="subtitle">Le {{ ordonnance.delivrance.date_delivrance|date:"d/m/Y H:i" }} par {{ ordonnance.delivrance.pharmacien }}.</p>
        <span class="badge terminee">Delivree</span>
        {% else %}
        <h2>Valider la delivrance</h2>
        <p class="subtitle">Confirmez que les medicaments ont ete remis au patient.</p>
        <form method="post" action="{% url 'valider_delivrance' ordonnance.pk %}">
            {% csrf_token %}
            <input type="hidden" name="code_qr" value="{{ ordonnance.code_qr }}">
            <button class="button primary" type="submit">Valider la delivrance</button>
        </form>
        {% endif %}
    </aside>
</section>
{% endif %}

<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js" integrity="sha384-b5Ya4Bq3qCyz39m2ISh+4DxjAIljdeFwK/BsXLuj9gugaNwAcj/ia15fxNZL9Nlx" crossorigin="anonymous"></script>
<script>
    (function () {
        var boutonScan = document.getElementById('bouton-scan-camera');
        var cameraDisponible = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        if (cameraDisponible && typeof jsQR === 'function' && boutonScan) {
            boutonScan.hidden = false;
        }
    })();
</script>
{% endblock %}
```

- [ ] **Step 4: Lancer le test pour vérifier qu'il passe**

Run: `python manage.py test Plateform_medicale.tests.EspacePharmacienTests.test_scan_camera_script_et_bouton_presents -v 2`
Expected: PASS

- [ ] **Step 5: Vérifier que `manage.py check` reste propre**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Commit**

```bash
git add Plateform_medicale/templates/scanner_ordonnance.html Plateform_medicale/tests.py
git commit -m "feat(pharmacien): bouton scan camera avec detection de capacite (plan direction artistique #8, 1/2)"
```

---

### Task 2: Panneau caméra, décodage jsQR et soumission automatique

**Files:**
- Modify: `Plateform_medicale/templates/scanner_ordonnance.html`
- Test: `Plateform_medicale/tests.py`

**Interfaces:**
- Consumes: `#bouton-scan-camera`, `#statut-scan-camera`, `#code_qr` (produits par la Task 1) ; global `jsQR(imageData.data, width, height)` fourni par le script CDN chargé en Task 1 (retourne `null` ou `{ data: string, ... }`).
- Produces: rien de consommé par une tâche ultérieure — c'est la dernière brique fonctionnelle. Task 3 ne fait que vérifier/nettoyer.

- [ ] **Step 1: Écrire le test qui vérifie le panneau caméra et les messages d'erreur**

Dans `Plateform_medicale/tests.py`, juste après `test_scan_camera_script_et_bouton_presents` (ajoutée en Task 1) :

```python
    def test_scan_camera_panneau_et_gestion_erreurs(self):
        """Plan de direction artistique, item 8 : panneau video + repli si camera indisponible."""
        response = self.client.get(reverse('scanner_ordonnance'))
        self.assertContains(response, 'id="panneau-scan-camera"')
        self.assertContains(response, 'id="video-scan-camera"')
        self.assertContains(response, 'id="canvas-scan-camera"')
        self.assertContains(response, 'id="bouton-fermer-scan-camera"')
        self.assertContains(response, 'function demarrerScan')
        self.assertContains(response, 'function arreterScan')
        self.assertContains(response, "NotAllowedError")
        self.assertContains(response, "NotFoundError")
        self.assertContains(response, 'requestSubmit')
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python manage.py test Plateform_medicale.tests.EspacePharmacienTests.test_scan_camera_panneau_et_gestion_erreurs -v 2`
Expected: FAIL (le panneau et la logique de scan n'existent pas encore)

- [ ] **Step 3: Ajouter le panneau caméra au formulaire**

Dans `Plateform_medicale/templates/scanner_ordonnance.html`, remplacer :

```html
    <div style="margin-top:16px;">
        <button type="button" id="bouton-scan-camera" class="button btn" hidden>{% icone "qr-scan" %} Scanner avec la camera</button>
        <p id="statut-scan-camera" class="subtitle" style="margin:8px 0 0;" role="status" aria-live="polite"></p>
    </div>
</form>
```

par :

```html
    <div style="margin-top:16px;">
        <button type="button" id="bouton-scan-camera" class="button btn" hidden>{% icone "qr-scan" %} Scanner avec la camera</button>
        <p id="statut-scan-camera" class="subtitle" style="margin:8px 0 0;" role="status" aria-live="polite"></p>

        <div id="panneau-scan-camera" hidden style="position:relative;max-width:360px;margin-top:12px;border-radius:12px;overflow:hidden;background:#000;">
            <video id="video-scan-camera" autoplay muted playsinline aria-hidden="true" style="width:100%;display:block;"></video>
            <canvas id="canvas-scan-camera" style="display:none;"></canvas>
            <div aria-hidden="true" style="position:absolute;inset:15%;border:2px solid var(--primary-accent);border-radius:12px;pointer-events:none;"></div>
            <button type="button" id="bouton-fermer-scan-camera" class="button btn" style="position:absolute;top:8px;right:8px;">Fermer la camera</button>
        </div>
    </div>
</form>
```

- [ ] **Step 4: Ajouter la logique de scan au script existant**

Remplacer le bloc `<script>` de détection de capacité (ajouté en Task 1) :

```html
<script>
    (function () {
        var boutonScan = document.getElementById('bouton-scan-camera');
        var cameraDisponible = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        if (cameraDisponible && typeof jsQR === 'function' && boutonScan) {
            boutonScan.hidden = false;
        }
    })();
</script>
```

par :

```html
<script>
    (function () {
        var boutonScan = document.getElementById('bouton-scan-camera');
        var boutonFermer = document.getElementById('bouton-fermer-scan-camera');
        var panneau = document.getElementById('panneau-scan-camera');
        var statut = document.getElementById('statut-scan-camera');
        var video = document.getElementById('video-scan-camera');
        var canvas = document.getElementById('canvas-scan-camera');
        var contexte = canvas.getContext('2d');
        var champCode = document.getElementById('code_qr');
        var flux = null;
        var idAnimation = null;

        var cameraDisponible = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        if (cameraDisponible && typeof jsQR === 'function' && boutonScan) {
            boutonScan.hidden = false;
        }

        function arreterScan() {
            if (idAnimation) {
                window.cancelAnimationFrame(idAnimation);
                idAnimation = null;
            }
            if (flux) {
                flux.getTracks().forEach(function (piste) { piste.stop(); });
                flux = null;
            }
            panneau.hidden = true;
        }

        function analyserImage() {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                contexte.drawImage(video, 0, 0, canvas.width, canvas.height);
                var image = contexte.getImageData(0, 0, canvas.width, canvas.height);
                var resultat = jsQR(image.data, image.width, image.height);
                if (resultat && resultat.data) {
                    statut.textContent = 'Code detecte, verification...';
                    arreterScan();
                    champCode.value = resultat.data;
                    champCode.form.requestSubmit();
                    return;
                }
            }
            idAnimation = window.requestAnimationFrame(analyserImage);
        }

        function demarrerScan() {
            statut.textContent = "Demande d'acces a la camera...";
            navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } } })
                .then(function (fluxObtenu) {
                    flux = fluxObtenu;
                    video.srcObject = flux;
                    panneau.hidden = false;
                    statut.textContent = "Recherche d'un code...";
                    idAnimation = window.requestAnimationFrame(analyserImage);
                })
                .catch(function (erreur) {
                    if (erreur.name === 'NotAllowedError') {
                        statut.textContent = "Acces a la camera refuse. Autorisez la camera dans les parametres du navigateur, ou utilisez la saisie manuelle.";
                    } else if (erreur.name === 'NotFoundError') {
                        statut.textContent = 'Aucune camera detectee sur cet appareil.';
                    } else {
                        statut.textContent = 'Scan par camera indisponible sur cet appareil ou cette connexion (HTTPS requis). Utilisez la saisie manuelle ou une douchette ci-dessous.';
                    }
                });
        }

        if (boutonScan) { boutonScan.addEventListener('click', demarrerScan); }
        if (boutonFermer) { boutonFermer.addEventListener('click', arreterScan); }
    })();
</script>
```

- [ ] **Step 5: Lancer le test pour vérifier qu'il passe**

Run: `python manage.py test Plateform_medicale.tests.EspacePharmacienTests.test_scan_camera_panneau_et_gestion_erreurs -v 2`
Expected: PASS

- [ ] **Step 6: Lancer toute la classe `EspacePharmacienTests` pour vérifier l'absence de régression**

Run: `python manage.py test Plateform_medicale.tests.EspacePharmacienTests -v 2`
Expected: tous les tests PASS, y compris `test_scan_code_valide_affiche_ordonnance` et `test_scan_code_invalide_affiche_erreur` (flux manuel inchangé).

- [ ] **Step 7: Commit**

```bash
git add Plateform_medicale/templates/scanner_ordonnance.html Plateform_medicale/tests.py
git commit -m "feat(pharmacien): panneau scan camera jsQR + soumission automatique (plan direction artistique #8, 2/2)"
```

---

### Task 3: Non-régression complète, vérification manuelle, documentation et nettoyage

**Files:**
- Modify: `docs/superpowers/plan-direction-artistique.md`
- Modify: `FONCTIONNEMENT.txt`
- Delete: `docs/superpowers/specs/2026-07-24-scan-qr-pharmacien-design.md`
- Delete: `docs/superpowers/plans/2026-07-24-scan-qr-pharmacien.md` (ce fichier)

**Interfaces:**
- Consumes: fonctionnalité complète livrée par les Tasks 1-2.
- Produces: rien (tâche de clôture).

- [ ] **Step 1: Suite de tests complète**

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (172 tests : 170 existants + les 2 ajoutées en Task 1 et Task 2)

- [ ] **Step 2: `manage.py check`**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Vérification manuelle du chemin de repli (navigateur)**

Lancer `python manage.py runserver`, se connecter avec un compte Pharmacien, ouvrir `/pharmacien/scanner/` (ou l'URL réelle de `scanner_ordonnance`). Vérifier :
- Le bouton "Scanner avec la caméra" est visible si le navigateur/contexte le permet (Chrome/Edge en HTTP local = contexte non sécurisé possible selon la configuration : `localhost` est considéré sécurisé par les navigateurs, donc `getUserMedia` doit être exposé même sans HTTPS explicite).
- Un clic déclenche la demande de permission caméra du navigateur.
- Si aucune caméra n'est disponible dans cet environnement (probable ici), le message d'erreur "Aucune caméra détectée sur cet appareil." s'affiche dans la zone de statut, sans `alert()` natif, et le champ de saisie manuelle reste utilisable.
- La saisie manuelle d'un code existant continue de fonctionner (non-régression visuelle).

Consigner explicitement dans le résumé final si le scan caméra réel (avec une caméra physique) n'a pas pu être testé de bout en bout dans cet environnement — ne pas présenter cette partie comme vérifiée si elle ne l'a pas été.

- [ ] **Step 4: Marquer l'item 8 comme fait dans le plan de direction artistique**

Dans `docs/superpowers/plan-direction-artistique.md`, remplacer la ligne :

```
| 8 | Clarifier le scan pharmacien (caméra vs douchette) | "Scan" central dans le pitch, écran = saisie texte | Faible-moyenne | 0,5-3 j | scanner_ordonnance.html |
```

par (remplacer `<hash>` par le hash du commit de la Task 2, obtenu via `git log --oneline -1`) :

```
| 8 | ~~Clarifier le scan pharmacien (caméra vs douchette)~~ | **FAIT** (commit <hash>) | Faible-moyenne | 0,5-3 j | scanner_ordonnance.html |
```

- [ ] **Step 5: Reporter les décisions d'architecture utiles dans FONCTIONNEMENT.txt**

Dans `FONCTIONNEMENT.txt`, section `Ordonnance` (autour de la ligne 149), après la description existante du modèle, ajouter un paragraphe :

```
  Scan pharmacien (scanner_ordonnance.html) : saisie manuelle/douchette
  (comportement clavier standard) ou scan camera (lib jsQR via CDN,
  bouton explicite masque si le navigateur ne supporte pas getUserMedia).
  Dans les deux cas, meme champ code_qr, meme soumission POST -- aucune
  route ni vue dediee au scan camera, c'est une simple facon
  supplementaire de remplir le meme champ avant l'envoi du formulaire
  existant.
```

- [ ] **Step 6: Supprimer les documents de travail temporaires**

```bash
rm "docs/superpowers/specs/2026-07-24-scan-qr-pharmacien-design.md"
rm "docs/superpowers/plans/2026-07-24-scan-qr-pharmacien.md"
```

- [ ] **Step 7: Commit final**

```bash
git add docs/superpowers/plan-direction-artistique.md FONCTIONNEMENT.txt
git add -u docs/superpowers/specs docs/superpowers/plans
git commit -m "docs: cloture item 8 (scan camera pharmacien) - FONCTIONNEMENT.txt + nettoyage specs/plans"
```
