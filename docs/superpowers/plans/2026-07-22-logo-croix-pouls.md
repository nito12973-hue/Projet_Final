# Logo Croix-Pouls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le mark Carte-bouclier par le nouveau mark Croix-Pouls (croix médicale arrondie traversée par le pouls terracotta) dans les 3 gabarits publics/auth (`base.html`, `landing.html`, `base_auth.html`), et terminer sur `base_auth.html` le passage à la palette Territoire A / typographie Manrope-Public Sans-Plex Mono qui n'y avait jamais été appliqué.

**Architecture:** Trois fichiers modifiés, un par tâche, comme pour le plan d'identité précédent (`docs/superpowers/plans/2026-07-22-identite-visuelle-design.md`, déjà exécuté pour `base.html`/`landing.html`). `base.html` et `landing.html` n'ont besoin que du remplacement du mark (favicon + occurrences du SVG) — palette et typographie y sont déjà correctes. `base_auth.html` reçoit le remplacement complet (jamais touché par le plan précédent) : palette (`--vert*` → `--primary*`), typographie, favicon et mark en un seul passage.

**Tech Stack:** Django templates, SVG inline, Google Fonts CDN (déjà en place, aucun changement de lien) — aucune dépendance ajoutée.

## Global Constraints

- Aucune nouvelle route, vue ou modèle Django. Seuls `Plateform_medicale/templates/base.html`, `landing.html` et `base_auth.html` sont modifiés.
- Le pouls (`stroke="#E0824F"`) est **toujours** terracotta, y compris dans les contextes où l'ancien mark utilisait un pouls blanc (bug à corriger au passage dans `landing.html`, mockup téléphone) — c'est la seule constante de couleur du système Croix-Pouls, voir `docs/superpowers/specs/2026-07-22-logo-croix-pouls-design.md`.
- Géométrie de référence du mark (`viewBox="0 0 48 48"`, réutilisée identique dans les 3 fichiers, seules les dimensions du `<svg>` conteneur et les couleurs de remplissage changent selon le contexte) :
  ```html
  <rect x="18" y="6" width="12" height="36" rx="4" fill="{couleur-croix}"/>
  <rect x="6" y="18" width="36" height="12" rx="4" fill="{couleur-croix}"/>
  <path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" stroke="#E0824F" stroke-width="{ep}" stroke-linecap="round" stroke-linejoin="round"/>
  ```
- `python manage.py check` doit rester sans erreur, `python manage.py test Plateform_medicale` doit rester vert (148 tests actuels, confirmés après le merge de `main` dans `feature/identite-visuelle`) après chaque tâche — changement purement présentationnel, aucun test n'exerce ces templates.
- Commits séparés par tâche.
- Aucune vérification automatisée du rendu visuel possible (SVG/CSS) — chaque tâche se vérifie par `python manage.py check` + inspection manuelle obligatoire (`runserver`).

---

### Task 1 : `base.html` (favicon + mark sidebar)

**Files:**
- Modify: `Plateform_medicale/templates/base.html:9` (favicon)
- Modify: `Plateform_medicale/templates/base.html:989-993` (mark sidebar)

**Interfaces:**
- Consumes : rien (fichier autonome, aucun `{% include %}` dans ce projet).
- Produces : rien consommé par les Tasks 2/3.

- [ ] **Step 1 : Favicon**

Remplacer :
```html
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath d='M11 15 H34 L41 22 V31 A5 5 0 0 1 36 36 H11 A5 5 0 0 1 6 31 V20 A5 5 0 0 1 11 15 Z' fill='%230e7c86'/%3E%3Cpath d='M12 26h4l2.5-5 3 10 2.5-7 1.5 2h11' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
```
par (croix pleine `--primary`, pouls terracotta — version pleine du mark, transparente, pas de fond) :
```html
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect x='18' y='6' width='12' height='36' rx='4' fill='%230e7c86'/%3E%3Crect x='6' y='18' width='36' height='12' rx='4' fill='%230e7c86'/%3E%3Cpath d='M6 24H14L17 16L21 32L25 19L27.5 24H42' fill='none' stroke='%23e0824f' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
```

- [ ] **Step 2 : Mark de la sidebar (fond sombre → croix quasi-blanche, pouls terracotta)**

Remplacer :
```html
                    <svg width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="flex-shrink:0;">
                        <path d="M11 15 H34 L41 22 V31 A5 5 0 0 1 36 36 H11 A5 5 0 0 1 6 31 V20 A5 5 0 0 1 11 15 Z" fill="none" stroke="#EFF4F3" stroke-width="2.4"/>
                        <path d="M12 26h4l2.5-5 3 10 2.5-7 1.5 2h11" fill="none" stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span class="brand-texte">Santé<span style="color: var(--primary-light);">SN</span></span>
```
par :
```html
                    <svg width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="flex-shrink:0;">
                        <rect x="18" y="6" width="12" height="36" rx="4" fill="#EFF4F3"/>
                        <rect x="6" y="18" width="36" height="12" rx="4" fill="#EFF4F3"/>
                        <path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span class="brand-texte">Santé<span style="color: var(--primary-light);">SN</span></span>
```

- [ ] **Step 3 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (148 tests, aucune régression — aucun test n'exerce ce template).

- [ ] **Step 4 : Vérification manuelle (obligatoire)**

Run: `python manage.py runserver`, se connecter avec n'importe quel rôle :
- La sidebar affiche la croix arrondie (pas de bouclier/carte) en blanc cassé sur fond navy foncé, pouls terracotta bien visible qui traverse la croix.
- Le mode réduit du menu (icônes seules) affiche toujours le mark correctement, sans déformation.
- L'onglet du navigateur affiche la nouvelle favicon (croix teal, pouls terracotta).
- Aucune erreur console, `manage.py check` toujours propre.

- [ ] **Step 5 : Commit**

```bash
git add Plateform_medicale/templates/base.html
git commit -m "style(identite): remplacer le mark Carte-bouclier par Croix-Pouls dans base.html"
```

---

### Task 2 : `landing.html` (favicon + mark en-tête, mockup téléphone, pied de page)

**Files:**
- Modify: `Plateform_medicale/templates/landing.html:17` (favicon)
- Modify: `Plateform_medicale/templates/landing.html:913-916` (mark en-tête)
- Modify: `Plateform_medicale/templates/landing.html:971-974` (mark mockup téléphone — corrige au passage le pouls blanc en pouls terracotta)
- Modify: `Plateform_medicale/templates/landing.html:1236-1239` (mark pied de page)

**Interfaces:**
- Consumes : rien (indépendant de la Task 1, même géométrie de mark appliquée).
- Produces : rien consommé par la Task 3.

- [ ] **Step 1 : Favicon**

Remplacer :
```html
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath d='M11 15 H34 L41 22 V31 A5 5 0 0 1 36 36 H11 A5 5 0 0 1 6 31 V20 A5 5 0 0 1 11 15 Z' fill='%230e7c86'/%3E%3Cpath d='M12 26h4l2.5-5 3 10 2.5-7 1.5 2h11' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
```
par :
```html
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect x='18' y='6' width='12' height='36' rx='4' fill='%230e7c86'/%3E%3Crect x='6' y='18' width='36' height='12' rx='4' fill='%230e7c86'/%3E%3Cpath d='M6 24H14L17 16L21 32L25 19L27.5 24H42' fill='none' stroke='%23e0824f' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
```

- [ ] **Step 2 : Mark de l'en-tête (fond clair → croix encre, pouls terracotta)**

Remplacer :
```html
                <svg width="38" height="38" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <path d="M11 15 H34 L41 22 V31 A5 5 0 0 1 36 36 H11 A5 5 0 0 1 6 31 V20 A5 5 0 0 1 11 15 Z" fill="none" stroke="#0B2027" stroke-width="2.4"/>
                    <path d="M12 26h4l2.5-5 3 10 2.5-7 1.5 2h11" fill="none" stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Santé<span style="color: var(--primary-strong);">SN</span>
```
par :
```html
                <svg width="38" height="38" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <rect x="18" y="6" width="12" height="36" rx="4" fill="#0B2027"/>
                    <rect x="6" y="18" width="36" height="12" rx="4" fill="#0B2027"/>
                    <path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Santé<span style="color: var(--primary-strong);">SN</span>
```

- [ ] **Step 3 : Mark du mockup téléphone (petite échelle, version pleine — corrige le pouls blanc en terracotta)**

Remplacer :
```html
                            <svg width="20" height="20" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M11 15 H34 L41 22 V31 A5 5 0 0 1 36 36 H11 A5 5 0 0 1 6 31 V20 A5 5 0 0 1 11 15 Z" fill="#0E7C86"/>
                                <path d="M12 26h4l2.5-5 3 10 2.5-7 1.5 2h11" fill="none" stroke="#ffffff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <span>SantéSN</span>
```
par :
```html
                            <svg width="20" height="20" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect x="18" y="6" width="12" height="36" rx="4" fill="#0E7C86"/>
                                <rect x="6" y="18" width="36" height="12" rx="4" fill="#0E7C86"/>
                                <path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" stroke="#E0824F" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <span>SantéSN</span>
```

- [ ] **Step 4 : Mark du pied de page (fond sombre → croix quasi-blanche, pouls terracotta)**

Remplacer :
```html
                    <svg width="30" height="30" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <path d="M11 15 H34 L41 22 V31 A5 5 0 0 1 36 36 H11 A5 5 0 0 1 6 31 V20 A5 5 0 0 1 11 15 Z" fill="none" stroke="#EFF4F3" stroke-width="2.4"/>
                        <path d="M12 26h4l2.5-5 3 10 2.5-7 1.5 2h11" fill="none" stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Santé<span style="color: var(--primary-light);">SN</span>
```
par :
```html
                    <svg width="30" height="30" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <rect x="18" y="6" width="12" height="36" rx="4" fill="#EFF4F3"/>
                        <rect x="6" y="18" width="36" height="12" rx="4" fill="#EFF4F3"/>
                        <path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Santé<span style="color: var(--primary-light);">SN</span>
```

- [ ] **Step 5 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (148 tests, aucune régression).

- [ ] **Step 6 : Vérification manuelle (obligatoire)**

Run: `python manage.py runserver`, ouvrir `/` sans être connecté :
- En-tête : croix encre + pouls terracotta, wordmark "Santé"+"SN" en teal, sur fond clair sticky.
- Mockup téléphone du Hero : mini-croix pleine (fond teal, pouls terracotta — plus de pouls blanc) bien visible à petite échelle.
- Pied de page : croix claire + pouls terracotta sur fond navy foncé, wordmark "SN" en teal clair lisible.
- Aucune erreur console.

- [ ] **Step 7 : Commit**

```bash
git add Plateform_medicale/templates/landing.html
git commit -m "style(identite): remplacer le mark Carte-bouclier par Croix-Pouls dans landing.html"
```

---

### Task 3 : `base_auth.html` (identité complète — jamais appliquée jusqu'ici)

**Files:**
- Modify: `Plateform_medicale/templates/base_auth.html:7-12` (theme-color, favicon, police)
- Modify: `Plateform_medicale/templates/base_auth.html:14-31` (bloc `:root`, unification `--vert*` → `--primary*`)
- Modify: `Plateform_medicale/templates/base_auth.html:41-43` (`body` font-family + usage `--vert-clair`)
- Modify: `Plateform_medicale/templates/base_auth.html:49-56` (`::selection`, `scrollbar-color`)
- Modify: `Plateform_medicale/templates/base_auth.html:67-74` (`::-webkit-scrollbar-thumb`)
- Modify: `Plateform_medicale/templates/base_auth.html:124` (dégradé `.panneau-marque`, usage `--vert-fonce`/`--vert-fort`)
- Modify: `Plateform_medicale/templates/base_auth.html:151-159` (règle `.logo`)
- Modify: `Plateform_medicale/templates/base_auth.html:232-237` (règle `h1`, usage `--vert-fonce`)
- Modify: `Plateform_medicale/templates/base_auth.html:266-271` (`.form-control:focus`, usage `--vert`)
- Modify: `Plateform_medicale/templates/base_auth.html:279` (usage `--vert-fonce`/`--vert-fort`)
- Modify: `Plateform_medicale/templates/base_auth.html:364-367` (`.btn-principal:focus-visible`)
- Modify: `Plateform_medicale/templates/base_auth.html:386-392` (mark + wordmark du panneau de marque)

**Interfaces:**
- Consumes : rien (indépendant des Tasks 1/2).
- Produces : rien.

- [ ] **Step 1 : Theme-color, favicon, police**

Remplacer :
```html
    <meta name="theme-color" content="#0f172a">
    <meta name="color-scheme" content="light">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath d='M24 4 L40 10 V22 C40 33 33 40.5 24 44 C15 40.5 8 33 8 22 V10 Z' fill='%230d9488'/%3E%3Cpath d='M10 20h4l2.4-5 3 10 2.4-7 1.6 2h6.6' fill='none' stroke='white' stroke-width='2.3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```
par :
```html
    <meta name="theme-color" content="#0b2027">
    <meta name="color-scheme" content="light">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect x='18' y='6' width='12' height='36' rx='4' fill='%230e7c86'/%3E%3Crect x='6' y='18' width='36' height='12' rx='4' fill='%230e7c86'/%3E%3Cpath d='M6 24H14L17 16L21 32L25 19L27.5 24H42' fill='none' stroke='%23e0824f' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

- [ ] **Step 2 : Tokens de palette — unifier `--vert*` en `--primary*`**

Remplacer :
```css
        :root {
            /* Navy : degrades fonces, titres — identique au reste de l'appli. */
            --vert-fonce: #0f172a;
            /* Turquoise vif : bordure/focus uniquement (pas assez de contraste
               pour du texte blanc en aplat). */
            --vert: #14b8a6;
            /* Teal fonce : seule variante sure pour texte blanc en degrade
               (panneau de marque, bouton principal). */
            --vert-fort: #0f766e;
            --vert-clair: #e3f7f4;
            --vert-accent: #2dd4bf;
            --texte: #1f2933;
            --muted: #5f6f7d;
            --surface: #ffffff;
            --border: #d9e2ea;
            --danger: #b42318;
            --masque-croix: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M12 3v18M3 12h18'/%3E%3C/svg%3E");
        }
```
par :
```css
        :root {
            /* Navy : degrades fonces, titres — identique au reste de l'appli. */
            --primary-dark: #0b2027;
            /* Turquoise vif : bordure/focus uniquement (pas assez de contraste
               pour du texte blanc en aplat). */
            --primary: #0e7c86;
            /* Teal fonce : seule variante sure pour texte blanc en degrade
               (panneau de marque, bouton principal). */
            --primary-strong: #095059;
            --primary-soft: #dcece9;
            --primary-light: #4fb8ae;
            --primary-accent: #4fb8ae;
            /* Terracotta : accent ponctuel uniquement (jamais en fond/aplat large). */
            --accent: #e0824f;
            --texte: #1f2933;
            --muted: #5f6f7d;
            --surface: #ffffff;
            --border: #d9e2ea;
            --danger: #b42318;
            --masque-croix: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M12 3v18M3 12h18'/%3E%3C/svg%3E");
        }
```

- [ ] **Step 3 : Police du corps + première référence `--vert-clair`**

Remplacer :
```css
            font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif;
            color: var(--texte);
            background: linear-gradient(150deg, var(--vert-clair) 0%, #f2f9f8 55%, #eaf6f4 100%);
```
par :
```css
            font-family: 'Public Sans', 'Segoe UI', Arial, sans-serif;
            color: var(--texte);
            background: linear-gradient(150deg, var(--primary-soft) 0%, #f2f9f8 55%, #eaf6f4 100%);
```

- [ ] **Step 4 : Teinte de sélection de texte et de barre de défilement**

Remplacer :
```css
        ::selection {
            background: rgba(20, 184, 166, 0.35);
        }

        * {
            scrollbar-width: thin;
            scrollbar-color: rgba(15, 118, 110, 0.35) transparent;
        }
```
par :
```css
        ::selection {
            background: rgba(14, 124, 134, 0.35);
        }

        * {
            scrollbar-width: thin;
            scrollbar-color: rgba(9, 80, 89, 0.35) transparent;
        }
```

- [ ] **Step 5 : Barre de défilement (thumb)**

Remplacer :
```css
        ::-webkit-scrollbar-thumb {
            background: rgba(15, 118, 110, 0.35);
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(15, 118, 110, 0.55);
        }
```
par :
```css
        ::-webkit-scrollbar-thumb {
            background: rgba(9, 80, 89, 0.35);
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(9, 80, 89, 0.55);
        }
```

- [ ] **Step 6 : Dégradé du panneau de marque**

Remplacer :
```css
            background: linear-gradient(160deg, var(--vert-fonce) 0%, var(--vert-fort) 70%, #115e56 100%);
```
par :
```css
            background: linear-gradient(160deg, var(--primary-dark) 0%, var(--primary-strong) 70%, #115e56 100%);
```

- [ ] **Step 7 : Police des titres (règle `.logo` et `h1`)**

Remplacer :
```css
        .logo {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-size: 27px;
            font-weight: 800;
            color: #ffffff;
            text-decoration: none;
        }
```
par :
```css
        .logo {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-family: 'Manrope', 'Public Sans', 'Segoe UI', Arial, sans-serif;
            font-size: 27px;
            font-weight: 800;
            color: #ffffff;
            text-decoration: none;
        }
```

Remplacer :
```css
        h1 {
            margin: 0 0 6px;
            font-size: 24px;
            font-weight: 800;
            color: var(--vert-fonce);
        }
```
par :
```css
        h1 {
            margin: 0 0 6px;
            font-family: 'Manrope', 'Public Sans', 'Segoe UI', Arial, sans-serif;
            font-size: 24px;
            font-weight: 800;
            color: var(--primary-dark);
        }
```

- [ ] **Step 8 : Bordure de champ au focus**

Remplacer :
```css
        .form-control:focus {
            outline: none;
            border-color: var(--vert);
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.16);
        }
```
par :
```css
        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.16);
        }
```

- [ ] **Step 9 : Dégradé du bouton principal**

Remplacer :
```css
            background: linear-gradient(135deg, var(--vert-fonce) 0%, var(--vert-fort) 100%);
```
par :
```css
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-strong) 100%);
```

- [ ] **Step 10 : Anneau de focus du bouton principal**

Remplacer :
```css
        .btn-principal:focus-visible {
            outline: none;
            box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.35);
        }
```
par :
```css
        .btn-principal:focus-visible {
            outline: none;
            box-shadow: 0 0 0 4px rgba(14, 124, 134, 0.35);
        }
```

- [ ] **Step 11 : Mark + wordmark du panneau de marque (croix translucide, pouls terracotta)**

Remplacer :
```html
                <span class="logo">
                    <svg width="46" height="46" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <path d="M24 4 L40 10 V22 C40 33 33 40.5 24 44 C15 40.5 8 33 8 22 V10 Z" fill="rgba(255,255,255,0.14)" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
                        <path d="M10 20h4l2.4-5 3 10 2.4-7 1.6 2h6.6" fill="none" stroke="#ffffff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    SantéSN
                </span>
```
par :
```html
                <span class="logo">
                    <svg width="46" height="46" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <rect x="18" y="6" width="12" height="36" rx="4" fill="rgba(255,255,255,0.9)"/>
                        <rect x="6" y="18" width="36" height="12" rx="4" fill="rgba(255,255,255,0.9)"/>
                        <path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" stroke="#E0824F" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Santé<span style="color: var(--primary-light);">SN</span>
                </span>
```

- [ ] **Step 12 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (148 tests, aucune régression).

- [ ] **Step 13 : Vérification manuelle (obligatoire)**

Run: `python manage.py runserver`, ouvrir `/connexion/` (déconnecté) :
- Panneau de marque gauche : croix blanche translucide + pouls terracotta, wordmark "Santé"+"SN" coloré, dégradé navy/teal (plus l'ancien vert/Plus Jakarta Sans).
- Bouton principal, bordures de champ au focus : toujours en teal, teinte cohérente avec `base.html`/`landing.html`.
- Si aucun admin n'existe, vérifier aussi `/installation/` (setup wizard) qui partage ce même gabarit.
- Aucune erreur console.

- [ ] **Step 14 : Commit**

```bash
git add Plateform_medicale/templates/base_auth.html
git commit -m "style(identite): palette Territoire A, typographie et mark Croix-Pouls dans base_auth.html"
```

---

## Après ce plan

Ce plan couvre uniquement le mark et la finalisation de `base_auth.html`. Ne
pas mettre à jour `FONCTIONNEMENT.txt` à l'issue de ce seul plan : la
convention du projet est de documenter une fois le chantier identité
visuelle complet livré (mark + palette + typographie dans les 3 gabarits).
Une fois ce plan exécuté, les chantiers suivants restent à brainstormer
séparément, dans l'ordre déjà proposé : Design System de composants
(boutons/cartes/tableaux/badges/formulaires/sidebar/navbar/footer/modales/
pagination/filtres), bibliothèque d'icônes, illustrations, langage
d'animation. L'audit UX écran par écran et le Top 50 final restent
volontairement pour après ces chantiers de design.
