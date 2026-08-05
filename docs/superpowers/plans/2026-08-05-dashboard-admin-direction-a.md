# Dashboard Administrateur — "Poste de pilotage" (Direction A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `dashboard.html` (admin home screen) from a light, table-heavy layout into a dark "poste de pilotage" canvas — one strong visual gesture (pulse trace behind the payment figures) instead of many equal panels, compact digest lists instead of tables.

**Architecture:** All new content lives inside a single new wrapper, `<div class="dash-command">`, added around the existing sections of `dashboard.html`. Dark styling for components shared with other role dashboards (`.panel`, `.dash-grid`, `.dash-stat`, `.dash-pill`, `.admin-layout`, `.governance-card`, `.button`) is written as CSS rules nested under `.dash-command` in `base.html` — the base rules for those classes are never edited, so the 3 other dashboards and other admin pages are unaffected. Components exclusive to `dashboard.html` (`.dash-hero*`, `.dash-stat-discret`, `.dash-stat-urgent`, `.admin-card-large`, `.quick-actions`, `.gouvernance-comptes`) are edited or removed directly.

**Tech Stack:** Django templates, vanilla CSS (single `<style>` block in `base.html`, no build step), vanilla JS (Chart.js 4 via CDN for the sparkline, Leaflet 1.9 via CDN for the map — both already wired up and untouched by this plan).

## Global Constraints

Copied verbatim from `docs/superpowers/specs/2026-08-05-dashboard-admin-direction-a-design.md`:

- Scope: only `Plateform_medicale/templates/dashboard.html` and scoped CSS in `Plateform_medicale/templates/base.html`. No changes to `views.py`, `models.py`, or any other template.
- `.page-title` (h1 + subtitle) stays outside the dark canvas, unchanged.
- Preserve exactly (covered by `tests.py`, class `DashboardAdminTests`): the `'—'` and `'0\xa0FCFA'` strings when there is no data; the label **"Pharmaciens actifs"**; the heading **"Derniers comptes créés"**; `id="carte-reseau-admin"` on the map container; the empty-state text **"Aucun prestataire partenaire géolocalisé…"**; the gouvernance links `?statut=actif` / `?statut=inactif`.
- No new hues: dark surfaces reuse `--primary-dark` / `--primary-strong` / `--sb-text-muted` / `--sb-text-faint` / `--sb-border` / `--sb-hover`; one new literal is allowed for the primary light-on-dark text color (`#EFF4F3`, already documented in `CLAUDE.md` for the sidebar logo mark).
- No new mode toggle: `color-scheme: light` stays declared as-is in every `<head>`; this is a fixed composition for this one page, not a system dark mode.
- `python manage.py test Plateform_medicale` must pass after every task below.

---

## File Structure

- Modify `Plateform_medicale/templates/dashboard.html` — restructured across Tasks 1–7 (each task touches a distinct, non-overlapping section of the file).
- Modify `Plateform_medicale/templates/base.html` — new CSS added incrementally (one block per task, all inserted in the same neighborhood: right after the `@keyframes pulse-anneau` rule and before `.legende-type`, currently around line 1379). Dead CSS removed in the same task that stops using it (no task leaves temporarily-orphaned CSS behind).
- Modify `Plateform_medicale/tests.py` — two new guard tests added to the existing `DashboardAdminTests` class (Tasks 1 and 2), covering the two new structural classes that no existing test touches. All other tasks are verified by tests that already exist.

Classes confirmed **exclusive** to `dashboard.html` (verified by grepping every template in `Plateform_medicale/templates/`; safe to edit/delete directly): `.dash-hero`, `.dash-hero-carte`, `.dash-hero-icon`, `.dash-hero-watermark`, `.dash-hero-sparkline-zone`, `.dash-hero-sparkline-legende`, `.dash-stat-discret`, `.dash-stat-urgent`, `.admin-card-large`, `.quick-actions`, `.gouvernance-comptes`.

Classes confirmed **shared** with other templates (verified the same way; must only be touched via `.dash-command`-scoped overrides, base rule stays untouched): `.panel`, `.panel-header`, `.dash-grid`, `.dash-stat`, `.dash-stat-icon`, `.dash-pill`, `.admin-layout`, `.governance-card`, `.button`, `.subtitle`, `.etat-vide`, `.legende-type`.

---

### Task 1: Dark canvas foundation — wrapper + CSS tokens

**Files:**
- Modify: `Plateform_medicale/templates/dashboard.html:13-14` (open wrapper) and `:303-305` (close wrapper)
- Modify: `Plateform_medicale/templates/base.html:1379-1381` (insert new CSS block)
- Test: `Plateform_medicale/tests.py` (append to `DashboardAdminTests`, after line 449)

**Interfaces:**
- Produces: `.dash-command` wrapper class; CSS custom properties `--dc-text`, `--dc-text-muted`, `--dc-text-faint`, `--dc-border`, `--dc-hover`, all scoped to `.dash-command` and consumed by every later task's CSS.
- Consumes: existing tokens `--primary-dark`, `--primary-strong`, `--sb-text-muted`, `--sb-text-faint`, `--sb-border`, `--sb-hover`, `--accent`.

- [ ] **Step 1: Write the failing test**

In `Plateform_medicale/tests.py`, inside class `DashboardAdminTests` (starts at line 332), add after the last existing test method (`test_derniers_comptes_exclut_les_assures`, currently ending at line 449):

```python

    def test_dashboard_utilise_le_conteneur_sombre(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'class="dash-command"')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_dashboard_utilise_le_conteneur_sombre -v 2`
Expected: FAIL — `'class="dash-command"' not found in response`

- [ ] **Step 3: Add the CSS foundation**

In `Plateform_medicale/templates/base.html`, locate the end of the `@keyframes pulse-anneau` rule and the start of `.legende-type` (currently lines 1375–1381):

```css
        @keyframes pulse-anneau {
            0% { opacity: 0.65; transform: scale(0.6); }
            75% { opacity: 0; transform: scale(1.6); }
            100% { opacity: 0; transform: scale(1.6); }
        }

        .legende-type {
```

Insert a new block between the closing `}` of the keyframes and `.legende-type`:

```css
        @keyframes pulse-anneau {
            0% { opacity: 0.65; transform: scale(0.6); }
            75% { opacity: 0; transform: scale(1.6); }
            100% { opacity: 0; transform: scale(1.6); }
        }

        /* Poste de pilotage (dashboard admin uniquement) : canevas sombre qui
           enveloppe tout le contenu sous le titre de page. Toutes les
           redefinitions sombres de composants partages (.panel, .dash-grid,
           .dash-stat, .dash-pill, .admin-layout, .governance-card, .button)
           vivent imbriquees sous .dash-command -- jamais dans la regle de
           base, qui reste utilisee telle quelle par les 3 autres dashboards
           et par d'autres pages admin (scanner_ordonnance.html, rapports.html). */
        .dash-command {
            margin-top: 24px;
            padding: 28px 30px 34px;
            border-radius: 24px;
            background: radial-gradient(140% 160% at 100% 0%, var(--primary-strong) 0%, var(--primary-dark) 55%);
            /* Texte clair sur fond sombre : reutilise les tokens deja concus
               pour ce contexte (sidebar), plus un seul token local pour le
               texte principal (meme valeur que la croix du logo sur fond
               sombre, deja documentee dans CLAUDE.md -- pas une couleur
               inventee). */
            --dc-text: #EFF4F3;
            --dc-text-muted: var(--sb-text-muted);
            --dc-text-faint: var(--sb-text-faint);
            --dc-border: var(--sb-border);
            --dc-hover: var(--sb-hover);
            color: var(--dc-text);
        }

        .dash-command .subtitle {
            color: var(--dc-text-muted);
        }

        .legende-type {
```

- [ ] **Step 4: Wrap the page content**

In `Plateform_medicale/templates/dashboard.html`, locate the end of `.page-title` and the start of `.dash-hero` (currently lines 12–14):

```html
</section>

<section class="dash-hero">
```

Change to:

```html
</section>

<div class="dash-command">
<section class="dash-hero">
```

Then locate the end of the map panel section and the start of the `json_script` tags (currently lines 300–305):

```html
    {% endif %}
</section>

{{ tendance_consultations|json_script:"donnees-tendance-consultations" }}
```

Change to:

```html
    {% endif %}
</section>
</div>

{{ tendance_consultations|json_script:"donnees-tendance-consultations" }}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_dashboard_utilise_le_conteneur_sombre -v 2`
Expected: PASS

- [ ] **Step 6: Run the full suite (regression check)**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS (this task only adds a wrapper `div` and new, additive CSS — nothing existing changes visually except the whole page content now sits on a dark rounded panel with its old light styling still showing through underneath; that's expected and gets fixed task by task).

- [ ] **Step 7: Manual check**

Run `python manage.py runserver`, log in as an admin, open the dashboard. Confirm: a large dark rounded panel now wraps everything below the page title; the content inside still looks like the old light design (cards/tables still light-colored) — that mismatch is expected and temporary, resolved by Tasks 2–7.

- [ ] **Step 8: Commit**

```bash
git add Plateform_medicale/templates/dashboard.html Plateform_medicale/templates/base.html Plateform_medicale/tests.py
git commit -m "feat(dashboard-admin): ajoute le conteneur sombre .dash-command"
```

---

### Task 2: "Aujourd'hui" → bandeau compact

**Files:**
- Modify: `Plateform_medicale/templates/dashboard.html` (the `<section class="panel" style="margin-top:14px;padding:20px 24px;">…Aujourd'hui…</section>` block, currently lines 73–97, now shifted +2 lines by Task 1)
- Modify: `Plateform_medicale/templates/base.html` — remove the now-dead `.dash-stat-urgent` rule (currently lines 1165–1177), add new `.dc-status` CSS
- Test: `Plateform_medicale/tests.py` (append to `DashboardAdminTests`)

**Interfaces:**
- Consumes: `--dc-text`, `--dc-text-muted`, `--dc-border` from Task 1; `total_rendez_vous_aujourd_hui`, `total_consultations_aujourd_hui`, `total_prises_en_charge_attente` (existing view context, untouched).
- Produces: `.dc-status`, `.dc-status-sep`, `.dc-status-link`, `.dc-status-urgent` classes.

- [ ] **Step 1: Write the failing test**

Append to `DashboardAdminTests` in `Plateform_medicale/tests.py`:

```python

    def test_aujourd_hui_est_un_bandeau_compact(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'class="dc-status"')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_aujourd_hui_est_un_bandeau_compact -v 2`
Expected: FAIL

- [ ] **Step 3: Replace the "Aujourd'hui" panel with the compact bandeau**

In `dashboard.html`, find:

```html
<section class="panel" style="margin-top:14px;padding:20px 24px;">
    <div class="panel-header" style="padding:0 0 14px;">
        <div>
            <h2 style="display:flex;align-items:center;gap:9px;"><span class="pulse-dot" aria-hidden="true"></span>Aujourd'hui</h2>
            <p class="subtitle" style="margin:2px 0 0;">Activité de la plateforme, tous rôles confondus.</p>
        </div>
    </div>
    <div class="dash-grid">
        <div class="dash-stat" style="cursor:default;">
            <span class="dash-stat-icon">{% icone "calendar" %}</span>
            <strong class="code">{{ total_rendez_vous_aujourd_hui }}</strong>
            <span>Rendez-vous</span>
        </div>
        <div class="dash-stat" style="cursor:default;">
            <span class="dash-stat-icon">{% icone "clipboard-list" %}</span>
            <strong class="code">{{ total_consultations_aujourd_hui }}</strong>
            <span>Consultations</span>
        </div>
        <a class="dash-stat{% if total_prises_en_charge_attente %} dash-stat-urgent{% endif %}" href="{% url 'liste_prises_en_charge' %}?statut=en_attente">
            <span class="dash-stat-icon">{% icone "clock-history" %}</span>
            <strong class="code">{{ total_prises_en_charge_attente }}</strong>
            <span>Prises en charge en attente</span>
        </a>
    </div>
</section>
```

Replace with:

```html
<div class="dc-status">
    <span class="pulse-dot" aria-hidden="true"></span>
    <span>Aujourd'hui</span>
    <span class="dc-status-sep" aria-hidden="true"></span>
    <span><strong class="code">{{ total_rendez_vous_aujourd_hui }}</strong> rendez-vous</span>
    <span class="dc-status-sep" aria-hidden="true"></span>
    <span><strong class="code">{{ total_consultations_aujourd_hui }}</strong> consultations</span>
    <span class="dc-status-sep" aria-hidden="true"></span>
    <a class="dc-status-link{% if total_prises_en_charge_attente %} dc-status-urgent{% endif %}" href="{% url 'liste_prises_en_charge' %}?statut=en_attente">
        <strong class="code">{{ total_prises_en_charge_attente }}</strong> prise(s) en charge en attente
    </a>
</div>
```

- [ ] **Step 4: Remove the now-dead `.dash-stat-urgent` rule and add `.dc-status` CSS**

In `base.html`, find and delete this block (the tile it styled no longer exists after Step 3):

```css
        /* Tuile "Aujourd'hui" qui merite une action immediate (ex. prises en
           charge en attente > 0, condition posee cote template) : accent
           terracotta au sens ou CLAUDE.md le documente deja (ponctuel, jamais
           en aplat large) -- pas un style permanent, seulement quand il y a
           reellement quelque chose a traiter. */
        .dash-stat-urgent {
            border-left: 3px solid var(--accent);
        }

        .dash-stat-urgent .dash-stat-icon {
            background: rgba(224, 130, 79, 0.14);
            color: var(--accent);
        }
```

Then, right after the `.dash-command .subtitle` rule added in Task 1, add:

```css
        .dash-command .dc-status {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            font-size: 13px;
            color: var(--dc-text-muted);
            margin-bottom: 20px;
        }

        .dash-command .dc-status strong {
            color: var(--dc-text);
            font-family: 'IBM Plex Mono', 'Cascadia Code', Consolas, monospace;
            font-weight: 600;
        }

        .dash-command .dc-status-sep {
            width: 1px;
            height: 12px;
            background: var(--dc-border);
        }

        .dash-command .dc-status-link {
            color: inherit;
            text-decoration: none;
        }

        .dash-command .dc-status-link:hover strong {
            color: var(--primary-accent);
        }

        .dash-command .dc-status-urgent strong {
            color: var(--accent);
        }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_aujourd_hui_est_un_bandeau_compact -v 2`
Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS (`test_aujourd_hui_ne_compte_que_les_rendez_vous_et_consultations_du_jour` only checks `response.context`, not markup, so it is unaffected).

- [ ] **Step 7: Manual check**

`runserver`, confirm the "Aujourd'hui" panel is now a single compact line above the payment cards, with a pulse dot, and that the prises-en-charge figure turns terracotta only when non-zero.

- [ ] **Step 8: Commit**

```bash
git add Plateform_medicale/templates/dashboard.html Plateform_medicale/templates/base.html Plateform_medicale/tests.py
git commit -m "feat(dashboard-admin): compresse Aujourd'hui en bandeau"
```

---

### Task 3: Hero paiements — trace de pouls décorative

**Files:**
- Modify: `Plateform_medicale/templates/dashboard.html` (the `<section class="dash-hero">` block)
- Modify: `Plateform_medicale/templates/base.html` — remove `.dash-hero-watermark` (dead), add `.dc-hero-trace`

**Interfaces:**
- Consumes: nothing new from earlier tasks (this section is untouched by the `.dash-command` scoping — `.dash-hero-carte` is exclusive to this page and already dark/gradient).
- Produces: `.dc-hero-trace` class.
- **Does not touch:** the `<canvas id="graphe-tendance-consultations">`, the `{{ montant_regle|franc_cfa }}` / `{{ montant_non_regle|franc_cfa }}` / `{% if taux_reglement is not None %}` template code, or the Chart.js `<script>` block at the bottom of the file. These stay byte-for-byte identical.

**Design note:** `.dash-hero-carte` already renders as a dark navy→teal gradient card with verified WCAG-AA text contrast (see the existing code comment on `.dash-hero-sparkline-legende` about the 0.78 opacity threshold) — it already fits the "poste de pilotage" look without modification. This task only swaps its decorative watermark (a plain cross shape) for a pulse trace, keeping everything else about the card as-is rather than reinventing an already-accessible component.

- [ ] **Step 1: Replace the watermark SVG**

In `dashboard.html`, find (inside the first `.dash-hero-carte`):

```html
        <svg class="dash-hero-watermark" viewBox="0 0 48 48" fill="none" aria-hidden="true">
            <rect x="18" y="6" width="12" height="36" rx="4" fill="#ffffff"/>
            <rect x="6" y="18" width="36" height="12" rx="4" fill="#ffffff"/>
        </svg>
```

Replace with:

```html
        <svg class="dc-hero-trace" viewBox="0 0 220 70" preserveAspectRatio="none" aria-hidden="true">
            <path d="M0,42 L30,42 L36,42 L41,18 L46,60 L51,30 L57,42 L95,42 L101,42 L106,18 L111,60 L117,30 L123,42 L160,42 L166,42 L171,18 L176,60 L182,30 L188,42 L220,42"/>
        </svg>
```

- [ ] **Step 2: Verify no other markup in this section changed**

Confirm the rest of the first `.dash-hero-carte` — the `{% icone "receipt" %}`, `{{ montant_regle|franc_cfa }}`, the `.dash-hero-sparkline-zone` with the canvas, the legend — and the two other `.dash-hero-carte` blocks (en attente, taux de règlement) are unchanged from the current file.

- [ ] **Step 3: Swap the CSS**

In `base.html`, find and delete:

```css
        /* Filigrane discret (croix seule, sans le pouls) sur la carte hero
           principale uniquement -- pas les 3 cartes, pour ne pas diluer
           l'effet (une seule carte porte le bandeau financier "vedette",
           avec la trace ; les 2 autres restent sobres). */
        .dash-hero-watermark {
            position: absolute;
            top: -18px;
            right: -14px;
            width: 150px;
            height: 150px;
            opacity: 0.06;
            pointer-events: none;
        }
```

Add in its place:

```css
        /* Trace de pouls decorative en haut a droite de la carte hero
           principale, derriere l'icone/le montant -- pas au meme endroit
           que le sparkline Chart.js reel (en bas de la carte), pour ne
           jamais se superposer a une donnee reelle. */
        .dc-hero-trace {
            position: absolute;
            top: 10px;
            right: -6px;
            width: 220px;
            height: 70px;
            opacity: 0.16;
            pointer-events: none;
        }

        .dc-hero-trace path {
            fill: none;
            stroke: var(--accent);
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
            stroke-dasharray: 200;
            stroke-dashoffset: 200;
            animation: dc-trace 3.2s ease-in-out infinite;
        }

        @keyframes dc-trace {
            to { stroke-dashoffset: 0; }
        }
```

No dedicated `prefers-reduced-motion` rule is needed here: `base.html` already has a global `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; ... } }` rule (see around line 1756) that automatically covers this new `@keyframes dc-trace` animation.

- [ ] **Step 4: Run the affected tests**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_sans_donnees_le_bandeau_financier_affiche_un_tiret Plateform_medicale.tests.DashboardAdminTests.test_bandeau_financier_calcule_les_montants_regles_et_en_attente -v 2`
Expected: both PASS unchanged (this task never touches the Django template variables they assert on).

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS.

- [ ] **Step 6: Manual check**

`runserver`, confirm: the Chart.js sparkline at the bottom of the first card still renders the real 30-day trend; the new pulse trace is visible as a subtle animated line behind the icon/amount near the top of the card, without overlapping the sparkline; with OS "reduce motion" enabled (or DevTools → Rendering → emulate `prefers-reduced-motion: reduce`), the trace stops animating.

- [ ] **Step 7: Commit**

```bash
git add Plateform_medicale/templates/dashboard.html Plateform_medicale/templates/base.html
git commit -m "feat(dashboard-admin): trace de pouls decorative sur le hero paiements"
```

---

### Task 4: Grille KPI — 6 tuiles, libellés complets conservés

**Files:**
- Modify: `Plateform_medicale/templates/dashboard.html` (the `<section class="dash-grid" style="margin-top:14px;">` block)
- Modify: `Plateform_medicale/templates/base.html` — remove `.dash-stat-discret` and its two sub-rules (dead), add `.dash-command .dash-stat*` overrides

**Interfaces:**
- Consumes: `--dc-text`, `--dc-text-muted`, `--dc-hover`, `--dc-border` from Task 1; `total_patients`, `total_medecins`, `total_pharmaciens`, `total_prestataires`, `total_consultations`, `total_ordonnances` (existing context, untouched).
- Produces: `.dash-command .dash-stat` dark override (also styles the lock icon in the governance card, Task 5, since both use the shared `.dash-stat-icon` class).

- [ ] **Step 1: Drop the `dash-stat-discret` modifier**

In `dashboard.html`, find the 6 KPI tiles:

```html
<section class="dash-grid" style="margin-top:14px;">
    <a class="dash-stat dash-stat-discret" href="{% url 'liste_patients' %}">
        <span class="dash-stat-icon">{% icone "id-card" %}</span>
        <strong class="code">{{ total_patients }}</strong>
        <span>Assurés gérés</span>
    </a>
    <a class="dash-stat dash-stat-discret" href="{% url 'liste_medecins' %}">
        <span class="dash-stat-icon">{% icone "stethoscope" %}</span>
        <strong class="code">{{ total_medecins }}</strong>
        <span>Médecins actifs</span>
    </a>
    <a class="dash-stat dash-stat-discret" href="{% url 'liste_pharmaciens' %}">
        <span class="dash-stat-icon">{% icone "pill" %}</span>
        <strong class="code">{{ total_pharmaciens }}</strong>
        <span>Pharmaciens actifs</span>
    </a>
    <a class="dash-stat dash-stat-discret" href="{% url 'liste_prestataires' %}">
        <span class="dash-stat-icon">{% icone "building" %}</span>
        <strong class="code">{{ total_prestataires }}</strong>
        <span>Prestataires partenaires</span>
    </a>
    <a class="dash-stat dash-stat-discret" href="{% url 'rapports' %}">
        <span class="dash-stat-icon">{% icone "clipboard-list" %}</span>
        <strong class="code">{{ total_consultations }}</strong>
        <span>Consultations</span>
    </a>
    <a class="dash-stat dash-stat-discret" href="{% url 'rapports' %}">
        <span class="dash-stat-icon">{% icone "qr-scan" %}</span>
        <strong class="code">{{ total_ordonnances }}</strong>
        <span>Ordonnances émises</span>
    </a>
</section>
```

Replace only the two attributes shown (`style="margin-top:14px;"` → `style="margin-top:20px;"`, and every `class="dash-stat dash-stat-discret"` → `class="dash-stat"`) — every label, URL, icon name and template variable stays exactly as-is:

```html
<section class="dash-grid" style="margin-top:20px;">
    <a class="dash-stat" href="{% url 'liste_patients' %}">
        <span class="dash-stat-icon">{% icone "id-card" %}</span>
        <strong class="code">{{ total_patients }}</strong>
        <span>Assurés gérés</span>
    </a>
    <a class="dash-stat" href="{% url 'liste_medecins' %}">
        <span class="dash-stat-icon">{% icone "stethoscope" %}</span>
        <strong class="code">{{ total_medecins }}</strong>
        <span>Médecins actifs</span>
    </a>
    <a class="dash-stat" href="{% url 'liste_pharmaciens' %}">
        <span class="dash-stat-icon">{% icone "pill" %}</span>
        <strong class="code">{{ total_pharmaciens }}</strong>
        <span>Pharmaciens actifs</span>
    </a>
    <a class="dash-stat" href="{% url 'liste_prestataires' %}">
        <span class="dash-stat-icon">{% icone "building" %}</span>
        <strong class="code">{{ total_prestataires }}</strong>
        <span>Prestataires partenaires</span>
    </a>
    <a class="dash-stat" href="{% url 'rapports' %}">
        <span class="dash-stat-icon">{% icone "clipboard-list" %}</span>
        <strong class="code">{{ total_consultations }}</strong>
        <span>Consultations</span>
    </a>
    <a class="dash-stat" href="{% url 'rapports' %}">
        <span class="dash-stat-icon">{% icone "qr-scan" %}</span>
        <strong class="code">{{ total_ordonnances }}</strong>
        <span>Ordonnances émises</span>
    </a>
</section>
```

- [ ] **Step 2: Remove the now-dead `.dash-stat-discret` rules**

In `base.html`, find and delete this whole block (three rules + their comments — `.dash-stat-discret` was only ever applied to the tiles just edited in Step 1):

```css
        /* Totaux de reference (grille KPI globale du dashboard admin, ex.
           "Medecins actifs") : traitement plus discret que .dash-stat
           standard, pour laisser "Aujourd'hui" (activite qui change
           reellement au quotidien, meme composant .dash-stat juste en
           dessous) rester la donnee la plus visible sous le bandeau
           financier. Modificateur, ne redefinit pas .dash-stat -- aucun
           impact sur les 3 autres dashboards (Assure/Medecin/Pharmacien)
           qui utilisent .dash-stat sans ce modificateur. */
        .dash-stat-discret {
            /* Meme teinte que --primary-soft (220,236,233), en transparence
               sur --bg plutot qu'en aplat : meme principe deja utilise par
               --accent-turquoise-wash (rgba de --primary), pas une nouvelle
               couleur. Distingue ces tuiles de reference du blanc plein des
               tuiles "Aujourd'hui" juste en dessous. */
            background: rgba(220, 236, 233, 0.5);
            border-color: rgba(14, 124, 134, 0.16);
            padding: 14px 16px;
            box-shadow: none;
        }

        .dash-stat-discret .dash-stat-icon {
            width: 28px;
            height: 28px;
            margin-bottom: 10px;
        }

        /* Specificite .dash-stat.dash-stat-discret (pas .dash-stat-discret
           seul) : meme specificite que .dash-stat strong sinon, et cette
           regle-ci arrive avant elle dans le fichier -- perdrait la
           cascade sans la classe composee. */
        .dash-stat.dash-stat-discret strong {
            font-size: 20px;
        }
```

- [ ] **Step 3: Add the dark `.dash-stat` override**

Right after the `.dash-command .dc-status-urgent strong` rule added in Task 2, add:

```css
        .dash-command .dash-stat {
            background: var(--dc-hover);
            border-color: var(--dc-border);
            box-shadow: none;
            color: var(--dc-text);
        }

        .dash-command a.dash-stat:hover {
            border-color: rgba(255, 255, 255, 0.22);
            box-shadow: none;
        }

        .dash-command .dash-stat strong {
            color: var(--dc-text);
        }

        .dash-command .dash-stat span {
            color: var(--dc-text-muted);
        }

        .dash-command .dash-stat-icon {
            background: rgba(255, 255, 255, 0.08);
            color: var(--primary-accent);
        }
```

- [ ] **Step 4: Run the affected tests**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_compte_les_pharmaciens Plateform_medicale.tests.DashboardAdminTests.test_ne_compte_que_les_prestataires_partenaires -v 2`
Expected: both PASS (`'Pharmaciens actifs'` is still rendered verbatim — only the CSS class changed, not the label text).

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS.

- [ ] **Step 6: Manual check**

`runserver`, confirm the 6 reference KPI tiles now render as dark glass tiles matching the rest of `.dash-command`, with full labels ("Pharmaciens actifs", "Prestataires partenaires", "Ordonnances émises" — not abbreviated).

- [ ] **Step 7: Commit**

```bash
git add Plateform_medicale/templates/dashboard.html Plateform_medicale/templates/base.html
git commit -m "feat(dashboard-admin): grille KPI en tuiles sombres"
```

---

### Task 5: Actions rapides + Gouvernance

**Files:**
- Modify: `Plateform_medicale/templates/base.html` only — no template markup changes required in this task (see note below).

**Interfaces:**
- Consumes: `--dc-text`, `--dc-text-muted`, `--dc-hover`, `--dc-border` from Task 1; `.dash-stat-icon` dark override from Task 4 (reused as-is for the governance card's lock icon, since it's the same class with no extra scoping).

**Note:** `dashboard.html:99-134` (the `<section class="admin-layout">` with "Actions rapides" and "Comptes et gouvernance") needs **no markup changes** — it already uses only classes that get dark-styled via `.dash-command`-scoped CSS (`.panel`, `.admin-layout`, `.governance-card`, `.quick-actions`, `.gouvernance-comptes`, `.button`). The leftover `panel-discret` class on both cards is harmless (redundant with the new `.dash-command .panel` override, which also sets `box-shadow: none`) and is left as-is to keep the diff minimal.

- [ ] **Step 1: Add the dark overrides**

Right after the `.dash-command .dash-stat-icon` rule added in Task 4, add:

```css
        .dash-command .panel {
            background: var(--dc-hover);
            border-color: var(--dc-border);
            box-shadow: none;
            color: var(--dc-text);
        }

        .dash-command .panel-header h2,
        .dash-command .governance-card h2 {
            color: var(--dc-text);
        }

        .dash-command .gouvernance-comptes strong {
            color: var(--dc-text);
        }

        .dash-command .gouvernance-comptes span {
            color: var(--dc-text-muted);
        }

        .dash-command .button:not(.primary) {
            background: var(--dc-hover);
            border-color: var(--dc-border);
            color: var(--dc-text);
        }

        .dash-command .button:not(.primary):hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.22);
        }
```

- [ ] **Step 2: Run the affected tests**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_gouvernance_compte_les_comptes_actifs_et_inactifs Plateform_medicale.tests.DashboardAdminTests.test_gouvernance_stats_actifs_inactifs_sont_cliquables -v 2`
Expected: both PASS (no template change in this task — these tests were already passing and stay untouched).

- [ ] **Step 3: Run the full suite**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS.

- [ ] **Step 4: Manual check**

`runserver`, confirm: "Actions rapides" primary buttons still show the teal gradient clearly against the dark card; the "Suivre les prises en charge" ghost button and "Gérer les utilisateurs" button are legible (light text/border) on the dark card; the governance numbers (comptes actifs/désactivés) are readable.

- [ ] **Step 5: Commit**

```bash
git add Plateform_medicale/templates/base.html
git commit -m "feat(dashboard-admin): actions rapides et gouvernance en cartes sombres"
```

---

### Task 6: 4 listes condensées en grille 2×2 (remplace les 4 tableaux)

**Files:**
- Modify: `Plateform_medicale/templates/dashboard.html` (the two `<section class="admin-layout">` blocks containing the 4 tables — "Derniers assurés"/"Suivi des prises en charge" and "Derniers comptes créés"/"Derniers prestataires ajoutés")
- Modify: `Plateform_medicale/templates/base.html` — add `.dc-digests`, `.dc-row`, `.dc-avatar`, `.dc-meta`, `.dc-name`, `.dc-sub`, `.dash-command .etat-vide p`, and dark `.dash-pill` variants

**Interfaces:**
- Consumes: `--dc-text`, `--dc-text-muted`, `--dc-text-faint`, `--dc-border` from Task 1; `derniers_patients`, `dernieres_prises_en_charge`, `derniers_comptes`, `derniers_prestataires` (existing context, untouched); the `illustration_vide` template tag (untouched, from `templatetags/icones.py`).
- Produces: `.dc-digests`, `.dc-row`, `.dc-avatar`, `.dc-meta`, `.dc-name`, `.dc-sub` classes.

This is the largest markup change in the plan. It replaces two `<section class="admin-layout">` blocks (4 `<table>` elements total) with one `<section class="dc-digests">` (four `.panel` cards in a 2×2 grid, each holding a list of compact rows instead of a table). Every `{% if %}` branch, every empty-state block, every status-pill condition, and the exact heading **"Derniers comptes créés"** are preserved unchanged from the current file — only the "found results" branch changes from `<table>` markup to `.dc-row` markup.

- [ ] **Step 1: Write the failing test**

Append to `DashboardAdminTests` in `Plateform_medicale/tests.py`:

```python

    def test_listes_du_dashboard_sont_en_grille_de_digests(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'class="dc-digests"')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_listes_du_dashboard_sont_en_grille_de_digests -v 2`
Expected: FAIL

- [ ] **Step 3: Replace the two `admin-layout` table sections**

In `dashboard.html`, find the two consecutive sections (currently starting with `<section class="admin-layout">` for "Derniers assurés" / "Suivi des prises en charge", and ending after the `<section class="admin-layout">` for "Derniers comptes créés" / "Derniers prestataires ajoutés" — the exact current content is the two blocks together spanning from `<section class="admin-layout">` right after the "Actions rapides"/"Gouvernance" section, through to the closing `</section>` right before the map panel's `<section class="panel panel-discret" style="margin-top:18px;...">`).

Replace both `admin-layout` blocks with:

```html
<section class="dc-digests">
    <article class="panel">
        <div class="panel-header">
            <h2>Derniers assurés</h2>
            <a class="button" href="{% url 'liste_patients' %}">Voir tout</a>
        </div>
        {% if derniers_patients %}
        <div class="dc-list">
            {% for patient in derniers_patients %}
            <div class="dc-row">
                <span class="dc-avatar">{{ patient.prenom|slice:":1"|upper }}{{ patient.nom|slice:":1"|upper }}</span>
                <span class="dc-meta">
                    <span class="dc-name">{{ patient.prenom }} {{ patient.nom }}</span>
                    <span class="dc-sub">{{ patient.get_type_beneficiaire_display }} · {{ patient.telephone|default:"-" }}</span>
                </span>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="etat-vide">
            {% illustration_vide "id-card" %}
            <p>Aucun assuré enregistré.</p>
            <div class="actions">
                <a class="button primary" href="{% url 'ajouter_patient' %}">Ajouter un assuré</a>
            </div>
        </div>
        {% endif %}
    </article>

    <article class="panel">
        <div class="panel-header">
            <h2>Suivi des prises en charge</h2>
            <a class="button" href="{% url 'liste_prises_en_charge' %}">Voir tout</a>
        </div>
        {% if dernieres_prises_en_charge %}
        <div class="dc-list">
            {% for prise in dernieres_prises_en_charge %}
            <div class="dc-row">
                <span class="dc-meta">
                    <span class="dc-name">{{ prise.patient }}</span>
                    <span class="dc-sub">{{ prise.date_demande|date:"d/m/Y" }}</span>
                </span>
                <span class="dash-pill {% if prise.statut == 'validee' or prise.statut == 'terminee' %}ok{% elif prise.statut == 'refusee' %}danger{% else %}attente{% endif %}">{{ prise.get_statut_display }}</span>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="etat-vide">
            {% illustration_vide "shield-check" %}
            <p>Aucune prise en charge enregistrée.</p>
            <div class="actions">
                <a class="button primary" href="{% url 'ajouter_prise_en_charge' %}">Ajouter une prise en charge</a>
            </div>
        </div>
        {% endif %}
    </article>

    <article class="panel">
        <div class="panel-header">
            <h2>Derniers comptes créés</h2>
            <a class="button" href="{% url 'liste_utilisateurs' %}">Voir tout</a>
        </div>
        {% if derniers_comptes %}
        <div class="dc-list">
            {% for compte in derniers_comptes %}
            <div class="dc-row">
                <span class="dc-avatar">{{ compte.get_full_name|default:compte.email|slice:":2"|upper }}</span>
                <span class="dc-meta">
                    <span class="dc-name">{{ compte.get_full_name|default:compte.email }}</span>
                    <span class="dc-sub">{{ compte.get_role_display }} · {{ compte.date_joined|date:"d/m/Y" }}</span>
                </span>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="etat-vide">
            {% illustration_vide "users" %}
            <p>Aucun compte enregistré.</p>
            <div class="actions">
                <a class="button primary" href="{% url 'ajouter_utilisateur' %}">Ajouter un utilisateur</a>
            </div>
        </div>
        {% endif %}
    </article>

    <article class="panel">
        <div class="panel-header">
            <h2>Derniers prestataires ajoutés</h2>
            <a class="button" href="{% url 'liste_prestataires' %}">Voir tout</a>
        </div>
        {% if derniers_prestataires %}
        <div class="dc-list">
            {% for prestataire in derniers_prestataires %}
            <div class="dc-row">
                <span class="dc-avatar">{{ prestataire.nom|slice:":2"|upper }}</span>
                <span class="dc-meta">
                    <span class="dc-name">{{ prestataire.nom }}</span>
                    <span class="dc-sub">{{ prestataire.get_type_prestataire_display }} · {{ prestataire.ville|default:"-" }}</span>
                </span>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="etat-vide">
            {% illustration_vide "building" %}
            <p>Aucun prestataire enregistré.</p>
            <div class="actions">
                <a class="button primary" href="{% url 'ajouter_prestataire' %}">Ajouter un prestataire</a>
            </div>
        </div>
        {% endif %}
    </article>
</section>
```

- [ ] **Step 4: Add the digest-list CSS**

Right after the `.dash-command .button:not(.primary):hover` rule added in Task 5, add:

```css
        .dash-command .dc-digests {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 20px;
        }

        @media (max-width: 720px) {
            .dash-command .dc-digests {
                grid-template-columns: 1fr;
            }
        }

        .dash-command .dc-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 0;
            border-top: 1px solid var(--dc-border);
            font-size: 13px;
        }

        .dash-command .dc-row:first-child {
            border-top: none;
        }

        .dash-command .dc-avatar {
            flex-shrink: 0;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10.5px;
            font-weight: 700;
            font-family: 'IBM Plex Mono', 'Cascadia Code', Consolas, monospace;
            background: rgba(79, 184, 174, 0.18);
            color: var(--primary-accent);
        }

        .dash-command .dc-meta {
            flex: 1;
            min-width: 0;
        }

        .dash-command .dc-name {
            display: block;
            color: var(--dc-text);
        }

        .dash-command .dc-sub {
            display: block;
            font-size: 11.5px;
            color: var(--dc-text-faint);
        }

        .dash-command .etat-vide p {
            color: var(--dc-text-muted);
        }

        .dash-command .dash-pill.ok { background: rgba(30, 122, 76, 0.22); color: #6fd39a; }
        .dash-command .dash-pill.attente { background: rgba(138, 90, 0, 0.28); color: #f0c375; }
        .dash-command .dash-pill.danger { background: rgba(179, 38, 30, 0.24); color: #ec8a83; }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_listes_du_dashboard_sont_en_grille_de_digests -v 2`
Expected: PASS

- [ ] **Step 6: Run the affected tests**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_derniers_comptes_et_derniers_prestataires Plateform_medicale.tests.DashboardAdminTests.test_derniers_comptes_exclut_les_assures -v 2`
Expected: both PASS.

- [ ] **Step 7: Run the full suite**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS.

- [ ] **Step 8: Manual check**

`runserver`, confirm: the 4 lists render as a 2×2 grid of dark cards with compact rows (avatar-initial circle + name + meta line); status pills on "Suivi des prises en charge" are legible (translucent tinted background, not the old pale pastel); temporarily emptying a queryset (or checking with a fresh DB) shows the illustrated empty state with readable muted text and a working CTA button.

- [ ] **Step 9: Commit**

```bash
git add Plateform_medicale/templates/dashboard.html Plateform_medicale/templates/base.html Plateform_medicale/tests.py
git commit -m "feat(dashboard-admin): remplace les 4 tableaux par une grille de listes condensees"
```

---

### Task 7: Carte réseau — habillage sombre

**Files:**
- Modify: `Plateform_medicale/templates/dashboard.html` (the map `<section class="panel panel-discret" style="margin-top:18px;padding:22px 24px;">` block)
- Modify: `Plateform_medicale/templates/base.html` — add `.dash-command .legende-type`

**Interfaces:**
- Consumes: `--dc-border` from Task 1; `.dash-command .panel` / `.panel-header h2` / `.subtitle` / `.button` / `.etat-vide p` overrides already added in Tasks 5–6 (apply automatically here, no new rules needed for those).
- **Does not touch:** `id="carte-reseau-admin"`, the `{% if prestataires_carte %}` branch, the empty-state text, the `{{ prestataires_carte|json_script:... }}` tag, or the Leaflet `<script>` block. These stay byte-for-byte identical.

- [ ] **Step 1: Update the map section**

In `dashboard.html`, find:

```html
<section class="panel panel-discret" style="margin-top:18px;padding:22px 24px;">
    <div class="panel-header" style="padding:0 0 16px;">
        <div>
            <h2>Réseau de prestataires partenaires</h2>
            <p class="subtitle" style="margin:2px 0 0;">Couverture géographique du réseau conventionné.</p>
        </div>
        <a class="button btn" href="{% url 'liste_prestataires' %}">Voir tout</a>
    </div>
    {% if prestataires_carte %}
    <div id="carte-reseau-admin" style="height:320px;border-radius:12px;border:1px solid var(--border);"></div>
```

Replace with:

```html
<section class="panel" style="margin-top:20px;padding:22px 24px;">
    <div class="panel-header" style="padding:0 0 16px;">
        <div>
            <h2>Réseau de prestataires partenaires</h2>
            <p class="subtitle" style="margin:2px 0 0;">Couverture géographique du réseau conventionné.</p>
        </div>
        <a class="button btn" href="{% url 'liste_prestataires' %}">Voir tout</a>
    </div>
    {% if prestataires_carte %}
    <div id="carte-reseau-admin" style="height:320px;border-radius:12px;border:1px solid var(--dc-border);"></div>
```

Everything below this point in the section (the `carte-legende` block, the `{% else %}` empty state, `{% endif %}`, closing `</section>`) stays exactly as it is in the current file.

- [ ] **Step 2: Add the legend color override**

Right after the `.dash-command .dash-pill.danger` rule added in Task 6, add:

```css
        .dash-command .legende-type {
            color: var(--dc-text-muted);
        }
```

- [ ] **Step 3: Run the affected tests**

Run: `python manage.py test Plateform_medicale.tests.DashboardAdminTests.test_carte_reseau_ignore_les_prestataires_sans_coordonnees Plateform_medicale.tests.DashboardAdminTests.test_carte_reseau_etat_vide_sans_prestataire_geolocalise -v 2`
Expected: both PASS (`id="carte-reseau-admin"` and the empty-state text are untouched).

- [ ] **Step 4: Run the full suite**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS.

- [ ] **Step 5: Manual check**

`runserver`, confirm: the map panel is dark like the rest of `.dash-command`; the Leaflet map still loads, zooms, and shows popups on marker click; the legend (Hôpital/Clinique/Pharmacie/Cabinet) is readable against the dark card.

- [ ] **Step 6: Commit**

```bash
git add Plateform_medicale/templates/dashboard.html Plateform_medicale/templates/base.html
git commit -m "feat(dashboard-admin): habillage sombre du panneau carte reseau"
```

---

### Task 8: Vérification finale et nettoyage

**Files:**
- Verify only: `Plateform_medicale/templates/dashboard.html`, `Plateform_medicale/templates/base.html`

**Interfaces:** none (verification task, no new code).

- [ ] **Step 1: Confirm no dead CSS remains**

Run (from the repo root):

```bash
grep -n "dash-stat-discret\|dash-stat-urgent\|dash-hero-watermark" Plateform_medicale/templates/*.html
```

Expected: no output (all three were removed from both `dashboard.html` and `base.html` in Tasks 2–4).

- [ ] **Step 2: Run the full suite one more time**

Run: `python manage.py test Plateform_medicale`
Expected: all tests PASS, including the 3 new guard tests added in Tasks 1, 2 and 6.

- [ ] **Step 3: Manual accessibility pass**

`runserver`, log in as admin, on the dashboard:
- Use the browser's contrast checker (or DevTools → Accessibility) on: the payment amounts (`--dc-text` `#EFF4F3` on the `.dash-hero-carte` gradient — already previously verified, unchanged by this plan), the KPI tile numbers/labels (`--dc-text` / `--dc-text-muted` on `--dc-hover`), the digest row names/meta text, the status pills. Fix any pairing that reads below 4.5:1 for normal-size text before closing this task.
- Tab through the page with keyboard only: confirm every link/button in `.dash-command` (KPI tiles, "Voir tout" links, quick actions, gouvernance links, map "Voir tout") shows a visible focus ring (inherited from the app's global `:focus-visible` rule — no new focus styling was added in this plan, so this step only confirms nothing in Tasks 1–7 accidentally suppressed it).
- Emulate `prefers-reduced-motion: reduce` in DevTools → Rendering: confirm the hero pulse trace and the `.pulse-dot` ring both stop animating.

- [ ] **Step 4: Fold the spec into `FONCTIONNEMENT.txt`, delete the working docs**

Per `CLAUDE.md`'s policy on `docs/superpowers/`: once verified, move the non-obvious decisions (the `.dash-command` scoping strategy, the exclusive-vs-shared class list, the "no JS changes needed" reasoning) into `FONCTIONNEMENT.txt`, then delete `docs/superpowers/specs/2026-08-05-dashboard-admin-direction-a-design.md` and `docs/superpowers/plans/2026-08-05-dashboard-admin-direction-a.md`.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "docs(dashboard-admin): reporte la refonte poste de pilotage dans FONCTIONNEMENT.txt"
```

---

## Self-Review

**Spec coverage:** every section of the design spec maps to a task — périmètre/wrapper (Task 1), simplification "Aujourd'hui" (Task 2), hero + pulse trace (Task 3), grille KPI libellés complets (Task 4), actions/gouvernance (Task 5), 4 listes en 2×2 (Task 6), carte réseau (Task 7), accessibilité + tests (Task 8). No gaps found.

**Placeholder scan:** no "TBD"/"TODO"/"add appropriate styling" left in any step — every step has real Django template code or real CSS.

**Type/name consistency:** `--dc-text`, `--dc-text-muted`, `--dc-text-faint`, `--dc-border`, `--dc-hover` are defined once in Task 1 and referenced with those exact names in Tasks 2, 4, 5, 6, 7 — checked, no drift. `.dc-status*` (Task 2), `.dc-hero-trace` (Task 3), `.dc-digests`/`.dc-row`/`.dc-avatar`/`.dc-meta`/`.dc-name`/`.dc-sub` (Task 6) are each introduced once and reused with the same name everywhere they appear.
