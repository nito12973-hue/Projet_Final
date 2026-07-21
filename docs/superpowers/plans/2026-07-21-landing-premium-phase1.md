# Landing page premium — Phase 1 (fondations, hero, stats) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer la landing page publique (`landing.html`) avec une identité visuelle premium (glassmorphism léger, ombres, formes organiques), un nouveau Hero (mockup téléphone + cartes flottantes) et une section Statistiques — sans toucher aux routes, vues, modèles ni au contenu métier des autres sections.

**Architecture:** Un seul fichier modifié (`Plateform_medicale/templates/landing.html`) : nouvelles variables/keyframes/classes CSS dans le `<style>` existant, nouveau balisage HTML pour le Hero et une nouvelle section, petit ajout JS (compteur animé) qui étend le script de révélation au défilement déjà en place. Aucune nouvelle route, vue, ou modèle Django — la vue `landing` (`views.py:210`) reste `return render(request, "landing.html")`.

**Tech Stack:** Django templates, CSS custom properties (déjà en place), JavaScript vanilla (`IntersectionObserver`, déjà en place), système d'icônes maison (`{% load icones %}` / `{% icone "nom" %}`, déjà chargé en tête de fichier) — aucune dépendance ajoutée.

## Global Constraints

- Aucune nouvelle route, vue ou modèle Django. Aucun fichier autre que `Plateform_medicale/templates/landing.html` n'est modifié dans ce plan.
- Aucune nouvelle dépendance externe (pas de Bootstrap, pas de Lucide, pas de CDN supplémentaire) — uniquement le CSS autonome existant et `templatetags/icones.py` (dict `_ICONES` : réutiliser `stethoscope`, `pill`, `calendar`, `shield-check`, `lock`, `zap`, `users`, `building`, `bar-chart` — tous déjà dans le dict, aucune icône nouvelle à créer pour cette phase).
- Les 2 boutons CTA du Hero gardent exactement leurs libellés et URLs actuels (`{% url 'login' %}`, `#acces`) — seul le style visuel évolue.
- Les statistiques chiffrées de la section Stats sont explicitement présentées comme des objectifs de déploiement, jamais comme des données d'usage réelles (ligne de texte dédiée, visible, pas une note en petit caractère cachée).
- Toutes les nouvelles animations respectent le bloc `@media (prefers-reduced-motion: reduce)` déjà présent en fin de `<style>` (aucune règle supplémentaire à y ajouter : il cible déjà `*, *::before, *::after` et neutralise toute `animation`/`transition`).
- Changement purement présentationnel : `python manage.py check` doit rester sans erreur et `python manage.py test Plateform_medicale` doit rester vert (145 tests actuels) après chaque tâche — aucun test n'exerce ce template aujourd'hui, donc aucune régression Python n'est possible tant que `views.py` n'est pas touché (il ne l'est pas dans ce plan).
- Commits séparés par tâche, jamais de commit combinant plusieurs tâches.
- Aucune vérification automatisée du rendu JS/CSS (pas de test Django possible pour de l'animation ou du CSS) — chaque tâche se vérifie par `python manage.py check` + vérification manuelle obligatoire (`runserver`, inspection visuelle desktop/mobile, bascule `prefers-reduced-motion`).

---

### Task 1 : Fondations visuelles (tokens CSS)

**Files:**
- Modify: `Plateform_medicale/templates/landing.html:22-40` (bloc `:root`)
- Modify: `Plateform_medicale/templates/landing.html:294-297` (juste après `@keyframes flotter`)

**Interfaces:**
- Consumes: rien (première tâche du plan).
- Produces (consommés par les Tasks 2 et 3) : tokens CSS `--ombre-douce`, `--ombre-flottante`, `--ombre-forte`, `--verre-fond`, `--verre-flou` ; keyframes `@keyframes flotter-lent` et `@keyframes flotter-inverse` ; classes `.forme-organique` (+ modificateurs `.forme-1`/`.forme-2`), `.badges-confiance` et `.badge-confiance`. Aucune de ces classes n'est encore utilisée dans le HTML à la fin de cette tâche (c'est la Task 2 qui les consomme) — la page rendue doit être visuellement identique à avant cette tâche.

- [ ] **Step 1 : Ajouter les nouveaux tokens dans `:root`**

Dans `Plateform_medicale/templates/landing.html`, remplacer :

```css
            --primary-soft: #e3f7f4;
            --border: #d9e2ea;
            --text: #1f2933;
            --muted: #5f6f7d;
            --surface: #ffffff;
            --masque-croix: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M12 3v18M3 12h18'/%3E%3C/svg%3E");
        }
```

par :

```css
            --primary-soft: #e3f7f4;
            --border: #d9e2ea;
            --text: #1f2933;
            --muted: #5f6f7d;
            --surface: #ffffff;
            --masque-croix: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M12 3v18M3 12h18'/%3E%3C/svg%3E");
            /* Ombres premium (Phase 1 landing) : plus douces/etagees que les
               box-shadow ponctuelles deja codees en dur ailleurs dans ce fichier. */
            --ombre-douce: 0 8px 24px rgba(15, 23, 42, 0.08);
            --ombre-flottante: 0 20px 48px rgba(15, 23, 42, 0.14);
            --ombre-forte: 0 30px 70px rgba(15, 23, 42, 0.20);
            /* Glassmorphism leger : meme principe que le <header> sticky
               (backdrop-filter deja utilise plus bas), applique aux cartes
               flottantes et badges. */
            --verre-fond: rgba(255, 255, 255, 0.65);
            --verre-flou: blur(16px);
        }
```

- [ ] **Step 2 : Ajouter les nouveaux keyframes**

Dans le même fichier, remplacer :

```css
        @keyframes flotter {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-12px); }
        }
```

par :

```css
        @keyframes flotter {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-12px); }
        }

        /* Variantes desynchronisees de "flotter", pour que plusieurs
           elements flottants ne bougent pas a l'unisson (cartes satellites
           du Hero, Task 2). */
        @keyframes flotter-lent {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50%      { transform: translateY(-16px) rotate(-1.5deg); }
        }

        @keyframes flotter-inverse {
            0%, 100% { transform: translateY(-8px) rotate(0deg); }
            50%      { transform: translateY(6px) rotate(1.5deg); }
        }
```

- [ ] **Step 3 : Ajouter les classes `.forme-organique` et `.badge-confiance`**

Dans le même fichier, juste après le bloc que vous venez de modifier à l'étape 2 (toujours avant `.hero-grille`), ajouter :

```css
        /* Formes organiques decoratives (Phase 1 landing) : blobs SVG en
           arriere-plan, basse opacite, purement decoratif. */
        .forme-organique {
            position: absolute;
            border-radius: 42% 58% 63% 37% / 41% 44% 56% 59%;
            background: linear-gradient(135deg, rgba(20, 184, 166, 0.16), rgba(45, 212, 191, 0.06));
            filter: blur(6px);
            pointer-events: none;
            user-select: none;
            z-index: 0;
        }

        /* Badges de confiance (Phase 1 landing) : pastille glassmorphism
           sous les CTA du Hero. */
        .badges-confiance {
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
        }

        .badge-confiance {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            background: var(--verre-fond);
            backdrop-filter: var(--verre-flou);
            -webkit-backdrop-filter: var(--verre-flou);
            border: 1px solid var(--border);
            font-size: 12.5px;
            font-weight: 700;
            color: var(--primary-strong);
            box-shadow: var(--ombre-douce);
        }

        .badge-confiance .icone-nav { width: 15px; height: 15px; }
```

- [ ] **Step 4 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py runserver`, ouvrir `/` (landing page, pas de connexion nécessaire). La page doit être **visuellement identique** à avant cette tâche (les nouveaux tokens/classes ne sont pas encore utilisés par le HTML). Vérifier dans les DevTools (onglet Elements/Styles) que `:root` expose bien les 5 nouvelles variables et qu'aucune erreur CSS n'apparaît dans la console.

- [ ] **Step 5 : Commit**

```bash
git add Plateform_medicale/templates/landing.html
git commit -m "style(landing): tokens premium (ombres, verre, formes organiques, badges de confiance)"
```

---

### Task 2 : Hero — nouveau titre, badges de confiance, mockup téléphone + cartes flottantes

**Files:**
- Modify: `Plateform_medicale/templates/landing.html:156` (`.btn-plein:hover`)
- Modify: `Plateform_medicale/templates/landing.html:260-275` (CSS `.hero .chiffres` / `.chiffres strong` / `.chiffres span` → supprimé)
- Modify: `Plateform_medicale/templates/landing.html:282-402` (zone CSS `.hero-visuel`/`.carte-demo`/`.mini-stat*` — nouvelles règles ajoutées après le bloc `.mini-stat span`)
- Modify: `Plateform_medicale/templates/landing.html` (bloc `@media (max-width: 920px)`, ajout de la règle mobile des cartes satellites)
- Modify: `Plateform_medicale/templates/landing.html:711-776` (HTML de la section `<section class="hero" id="accueil">`)

**Interfaces:**
- Consumes: tokens/keyframes/classes de la Task 1 (`--ombre-flottante`, `--ombre-douce`, `--verre-fond`, `--verre-flou`, `@keyframes flotter-lent`, `@keyframes flotter-inverse`, `.badges-confiance`, `.badge-confiance`). Icônes existantes du dict `_ICONES` : `stethoscope`, `calendar`, `pill`, `shield-check`, `lock`, `zap`, `qr-scan`.
- Produces (rien n'est consommé par la Task 3, qui est indépendante du Hero) : classes `.telephone-mockup`, `.telephone-encoche`, `.telephone-ecran`, `.telephone-entete`, `.carte-demo-telephone`, `.carte-satellite` (+ modificateurs `.satellite-qr`/`.satellite-medecin`/`.satellite-ordonnance`), `.pastille-sm`, `.avatar-initiales`, `.motif-qr`.

**Décision de contenu (à appliquer telle quelle, actée dans le spec) :** le mockup téléphone reprend le contenu réel de la carte "Rendez-vous du jour" actuelle, mais seulement les 2 premières lignes de rendez-vous (Mamadou Diallo 08h00, Aïssatou Diallo 09h00) + les mini-stats — la 3ᵉ ligne (Fatou Diallo, 10h30, "En attente") est retirée de cette vue compacte pour ne pas surcharger un cadre de téléphone étroit. Aucune donnée n'est inventée : c'est un sous-ensemble du contenu existant, pas un ajout.

- [ ] **Step 1 : Restyler l'ombre au survol du bouton plein (utilise le token de la Task 1)**

Remplacer :

```css
        .btn-plein:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(13, 148, 136, 0.40); }
```

par :

```css
        .btn-plein:hover { transform: translateY(-2px); box-shadow: var(--ombre-flottante); }
```

- [ ] **Step 2 : Supprimer le CSS `.chiffres` (remplacé par `.badges-confiance` de la Task 1)**

Remplacer :

```css
        .hero .chiffres {
            display: flex;
            flex-wrap: wrap;
            gap: 34px;
            margin-top: 44px;
            animation: entree 0.7s ease-out 0.36s both;
        }

        .chiffres strong {
            display: block;
            font-size: 28px;
            font-weight: 800;
            color: var(--primary-dark);
        }

        .chiffres span { color: var(--muted); font-size: 14px; font-weight: 600; }

        @keyframes entree {
```

par :

```css
        @keyframes entree {
```

L'ancienne règle `.hero .chiffres` portait `animation: entree 0.7s ease-out 0.36s both;` (apparition retardée, après le titre/sous-titre/CTA). `.badges-confiance` (défini à la Task 1) ne porte pas encore cette animation propre au Hero — c'est délibéré : la Task 1 ne définit que l'apparence réutilisable du badge, cette tâche (Hero) lui ajoute maintenant le timing d'apparition séquencée qui n'a de sens que dans ce contexte précis. Remplacer (dans le bloc ajouté par la Task 1) :

```css
        .badges-confiance {
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
        }
```

par :

```css
        .badges-confiance {
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
            animation: entree 0.7s ease-out 0.36s both;
        }
```

- [ ] **Step 3 : Ajouter le CSS du mockup téléphone et des cartes satellites**

Après le bloc existant :

```css
        .mini-stat span {
            font-size: 11px;
            color: var(--muted);
            font-weight: 600;
        }
```

ajouter :

```css

        /* ===== Illustration Hero : mockup telephone + cartes flottantes (Phase 1) ===== */
        .hero-visuel {
            position: relative;
            animation: entree 0.8s ease-out 0.2s both;
            display: flex;
            justify-content: center;
            padding: 30px 0;
        }

        .forme-organique.forme-1 { width: 260px; height: 260px; top: -30px; right: 8%; }
        .forme-organique.forme-2 { width: 200px; height: 200px; bottom: -10px; left: 4%; }

        .telephone-mockup {
            position: relative;
            z-index: 1;
            width: 260px;
            padding: 14px 10px 26px;
            background: linear-gradient(160deg, var(--primary-dark) 0%, #1e293b 100%);
            border-radius: 38px;
            box-shadow: var(--ombre-forte);
        }

        .telephone-encoche {
            position: absolute;
            top: 14px;
            left: 50%;
            transform: translateX(-50%);
            width: 70px;
            height: 16px;
            background: #0b1220;
            border-radius: 999px;
        }

        .telephone-ecran {
            background: #f4faf9;
            border-radius: 26px;
            padding: 30px 14px 16px;
        }

        .telephone-entete {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 800;
            font-size: 14px;
            color: var(--primary-dark);
            margin-bottom: 14px;
            padding: 0 4px;
        }

        .carte-demo-telephone {
            padding: 16px;
            box-shadow: none;
            border: 1px solid var(--border);
            animation: none;
        }

        .carte-satellite {
            position: absolute;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--verre-fond);
            backdrop-filter: var(--verre-flou);
            -webkit-backdrop-filter: var(--verre-flou);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 10px 14px;
            box-shadow: var(--ombre-flottante);
            font-size: 12px;
            max-width: 168px;
        }

        .carte-satellite strong { display: block; font-size: 13px; color: var(--primary-dark); }
        .satellite-sous-texte { color: var(--muted); font-size: 11.5px; }

        .pastille-sm { width: 34px; height: 34px; flex-shrink: 0; }
        .pastille-sm .icone-nav { width: 17px; height: 17px; }

        .satellite-qr {
            top: 6%;
            right: -10%;
            animation: flotter-lent 5.5s ease-in-out infinite;
        }

        .satellite-medecin {
            bottom: 32%;
            left: -14%;
            animation: flotter-inverse 6.2s ease-in-out infinite;
            animation-delay: 0.6s;
        }

        .satellite-ordonnance {
            bottom: 4%;
            right: -6%;
            animation: flotter-lent 5.8s ease-in-out infinite;
            animation-delay: 1.2s;
        }

        .avatar-initiales {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary-strong));
            color: #fff;
            font-weight: 800;
            font-size: 12px;
            flex-shrink: 0;
        }

        .motif-qr {
            display: inline-block;
            width: 30px;
            height: 30px;
            margin-top: 4px;
            background-image:
                linear-gradient(90deg, var(--primary-dark) 30%, transparent 30%),
                linear-gradient(var(--primary-dark) 30%, transparent 30%);
            background-size: 6px 6px;
            background-color: #ffffff;
            background-repeat: repeat;
            border: 1px solid var(--border);
            border-radius: 4px;
        }
```

- [ ] **Step 4 : Ajouter le repli mobile des cartes satellites**

Dans le bloc `@media (max-width: 920px) { ... }` existant, remplacer :

```css
            .hero { padding: 56px 0 64px; }
            .hero-grille { grid-template-columns: 1fr; gap: 40px; }
            .a-propos-grille { grid-template-columns: 1fr; gap: 32px; }
        }
```

par :

```css
            .hero { padding: 56px 0 64px; }
            .hero-grille { grid-template-columns: 1fr; gap: 40px; }
            .a-propos-grille { grid-template-columns: 1fr; gap: 32px; }

            .hero-visuel { flex-direction: column; align-items: center; }
            .cartes-satellites {
                position: static;
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 8px;
                margin-top: 16px;
                width: 100%;
            }
            .carte-satellite {
                position: static;
                animation: none !important;
                max-width: none;
            }
        }
```

- [ ] **Step 5 : Remplacer le titre, le sous-titre et les "chiffres" par les badges de confiance**

Dans la section `<section class="hero" id="accueil">`, remplacer :

```html
            <div>
                <h1>La santé <span class="accent">connectée</span><br>au service de tous.</h1>
                <p class="slogan">
                    SantéSN digitalise le parcours de prise en charge médicale au Sénégal :
                    rendez-vous, consultations, ordonnances sécurisées par QR Code et
                    remboursements d'assurance — le tout sur une seule plateforme.
                </p>
                <div class="cta">
                    <a class="btn btn-plein" href="{% url 'login' %}">Accéder à mon espace</a>
                    <a class="btn btn-contour" href="#acces">Comment obtenir un compte ?</a>
                </div>
                <div class="chiffres">
                    <div><strong>4</strong><span>Espaces dédiés par rôle</span></div>
                    <div><strong>100%</strong><span>Parcours digitalisé</span></div>
                    <div><strong>QR</strong><span>Ordonnances sécurisées</span></div>
                </div>
            </div>
```

par :

```html
            <div>
                <h1>La santé, <span class="accent">connectée</span><br>— du premier clic au remboursement.</h1>
                <p class="slogan">
                    SantéSN réunit rendez-vous, consultations, ordonnances sécurisées par
                    QR Code et remboursement d'assurance dans un seul espace — pensé pour
                    les assurés, les médecins et les pharmacies du Sénégal.
                </p>
                <div class="cta">
                    <a class="btn btn-plein" href="{% url 'login' %}">Accéder à mon espace</a>
                    <a class="btn btn-contour" href="#acces">Comment obtenir un compte ?</a>
                </div>
                <div class="badges-confiance">
                    <span class="badge-confiance">{% icone "shield-check" %} Ordonnances infalsifiables</span>
                    <span class="badge-confiance">{% icone "lock" %} Données sécurisées</span>
                    <span class="badge-confiance">{% icone "zap" %} Suivi en temps réel</span>
                </div>
            </div>
```

- [ ] **Step 6 : Remplacer l'illustration `.hero-visuel` (carte flottante → téléphone + satellites)**

Remplacer :

```html
            <div class="hero-visuel" aria-hidden="true">
                <div class="carte-demo">
                    <div class="entete-carte">
                        <span class="pastille">{% icone "stethoscope" %}</span>
                        <div>
                            <h3>Rendez-vous du jour</h3>
                            <span class="sous">Dr Ndiaye — Clinique Pasteur</span>
                        </div>
                    </div>
                    <div class="ligne-rdv">
                        <span class="heure">08h00</span>
                        <div>
                            <div class="nom">Mamadou Diallo</div>
                            <div class="detail">IPM Santé · EMP001</div>
                        </div>
                        <span class="etiquette">Confirmé</span>
                    </div>
                    <div class="ligne-rdv">
                        <span class="heure">09h00</span>
                        <div>
                            <div class="nom">Aïssatou Diallo</div>
                            <div class="detail">Ayant droit · Épouse</div>
                        </div>
                        <span class="etiquette">Confirmé</span>
                    </div>
                    <div class="ligne-rdv">
                        <span class="heure">10h30</span>
                        <div>
                            <div class="nom">Fatou Diallo</div>
                            <div class="detail">Ayant droit · Enfant</div>
                        </div>
                        <span class="etiquette">En attente</span>
                    </div>
                    <div class="mini-stats">
                        <div class="mini-stat">
                            <span class="mini-stat-icon">{% icone "calendar" %}</span>
                            <div><strong>37</strong><span>RDV aujourd'hui</span></div>
                        </div>
                        <div class="mini-stat">
                            <span class="mini-stat-icon">{% icone "pill" %}</span>
                            <div><strong>12</strong><span>Ordonnances</span></div>
                        </div>
                    </div>
                </div>
            </div>
```

par :

```html
            <div class="hero-visuel" aria-hidden="true">
                <span class="forme-organique forme-1"></span>
                <span class="forme-organique forme-2"></span>

                <div class="telephone-mockup">
                    <span class="telephone-encoche"></span>
                    <div class="telephone-ecran">
                        <div class="telephone-entete">
                            <svg width="20" height="20" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M24 4 L40 10 V22 C40 33 33 40.5 24 44 C15 40.5 8 33 8 22 V10 Z" fill="url(#degrade-logo-telephone)"/>
                                <path d="M10 20h4l2.4-5 3 10 2.4-7 1.6 2h6.6" fill="none" stroke="#ffffff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
                                <defs>
                                    <linearGradient id="degrade-logo-telephone" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                                        <stop stop-color="#14b8a6"/>
                                        <stop offset="1" stop-color="#0d9488"/>
                                    </linearGradient>
                                </defs>
                            </svg>
                            <span>SantéSN</span>
                        </div>
                        <div class="carte-demo carte-demo-telephone">
                            <div class="entete-carte">
                                <span class="pastille">{% icone "stethoscope" %}</span>
                                <div>
                                    <h3>Rendez-vous du jour</h3>
                                    <span class="sous">Dr Ndiaye — Clinique Pasteur</span>
                                </div>
                            </div>
                            <div class="ligne-rdv">
                                <span class="heure">08h00</span>
                                <div>
                                    <div class="nom">Mamadou Diallo</div>
                                    <div class="detail">IPM Santé · EMP001</div>
                                </div>
                                <span class="etiquette">Confirmé</span>
                            </div>
                            <div class="ligne-rdv">
                                <span class="heure">09h00</span>
                                <div>
                                    <div class="nom">Aïssatou Diallo</div>
                                    <div class="detail">Ayant droit · Épouse</div>
                                </div>
                                <span class="etiquette">Confirmé</span>
                            </div>
                            <div class="mini-stats">
                                <div class="mini-stat">
                                    <span class="mini-stat-icon">{% icone "calendar" %}</span>
                                    <div><strong>37</strong><span>RDV aujourd'hui</span></div>
                                </div>
                                <div class="mini-stat">
                                    <span class="mini-stat-icon">{% icone "pill" %}</span>
                                    <div><strong>12</strong><span>Ordonnances</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="cartes-satellites">
                    <div class="carte-satellite satellite-qr">
                        <span class="pastille pastille-sm">{% icone "qr-scan" %}</span>
                        <div>
                            <strong>Ordonnance vérifiée</strong>
                            <span class="motif-qr" aria-hidden="true"></span>
                        </div>
                    </div>

                    <div class="carte-satellite satellite-medecin">
                        <span class="avatar-initiales">DN</span>
                        <div>
                            <strong>Dr Ndiaye</strong>
                            <span class="satellite-sous-texte">En consultation</span>
                        </div>
                    </div>

                    <div class="carte-satellite satellite-ordonnance">
                        <span class="pastille pastille-sm">{% icone "pill" %}</span>
                        <div>
                            <strong>3 médicaments</strong>
                            <span class="satellite-sous-texte">Prête</span>
                        </div>
                    </div>
                </div>
            </div>
```

- [ ] **Step 7 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (145 tests, aucune régression — aucun test n'exerce ce template).

- [ ] **Step 8 : Vérification manuelle (obligatoire, rendu visuel non testé automatiquement)**

Run: `python manage.py runserver`, ouvrir `/` sans être connecté :
- Le Hero affiche le nouveau titre, le nouveau sous-titre, les 2 boutons CTA identiques (mêmes libellés, mêmes destinations `{% url 'login' %}` et `#acces`), et 3 badges de confiance (icônes + textes) sous les boutons.
- À droite, un mockup de téléphone (bordure sombre, encoche en haut) affiche la mini-carte "Rendez-vous du jour" (Dr Ndiaye, 2 lignes de RDV, mini-stats 37/12) — pas la 3ᵉ ligne "Fatou Diallo".
- 3 cartes flottantes (QR, Dr Ndiaye, "3 médicaments") sont visibles en débord autour du téléphone, chacune flotte avec un léger décalage temporel (pas toutes synchronisées).
- Réduire la fenêtre sous ~920px : les 3 cartes flottantes cessent d'être en position absolue et se rangent en ligne sous le téléphone, sans chevaucher le texte.
- Dans les DevTools, activer l'émulation `prefers-reduced-motion: reduce` : toutes les animations (flottement, apparition) doivent s'arrêter (aucune règle nouvelle à ajouter ici : le bloc `@media (prefers-reduced-motion: reduce)` existant couvre déjà `animation`/`transition` globalement).
- Aucune erreur dans la console navigateur.

- [ ] **Step 9 : Commit**

```bash
git add Plateform_medicale/templates/landing.html
git commit -m "feat(landing): hero premium (mockup telephone + cartes flottantes + badges de confiance)"
```

---

### Task 3 : Section Statistiques

**Files:**
- Modify: `Plateform_medicale/templates/landing.html` (CSS : nouvelle règle `.grille-stats`/`.carte-stat`/`.chiffre-anime`/`.libelle-stat`, ajoutée avant `/* ===== Sections ===== */`)
- Modify: `Plateform_medicale/templates/landing.html:776-778` (HTML : nouvelle `<section>` insérée entre la fermeture de `.hero` et le commentaire `<!-- ===== SERVICES ===== -->`)
- Modify: `Plateform_medicale/templates/landing.html` (fin de fichier : extension du `<script>` existant avec le compteur animé)

**Interfaces:**
- Consumes: token `--ombre-flottante` (Task 1) pour le hover des cartes stats ; classe `.revele` et l'`IntersectionObserver` de révélation déjà en place (réutilisés tels quels, pas dupliqués) ; icônes existantes `_ICONES` : `users`, `stethoscope`, `building`, `bar-chart`.
- Produces: rien de consommé par une tâche ultérieure de ce plan (section autonome). Les Phases 2-4 (hors de ce plan) pourront s'insérer avant/après cette section sans dépendance.

- [ ] **Step 1 : Ajouter le CSS de la grille de statistiques**

Avant la ligne :

```css
        /* ===== Sections ===== */
        section.bloc { padding: 78px 0; }
```

ajouter :

```css
        /* ===== Statistiques (Phase 1 landing) ===== */
        .grille-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 22px;
        }

        .carte-stat {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 30px 22px;
            text-align: center;
            transition: transform 0.22s ease, box-shadow 0.22s ease;
        }

        .carte-stat:hover {
            transform: translateY(-6px);
            box-shadow: var(--ombre-flottante);
        }

        .carte-stat .pastille { margin: 0 auto 16px; }

        .chiffre-anime {
            display: block;
            font-size: 32px;
            font-weight: 800;
            color: var(--primary-dark);
            font-variant-numeric: tabular-nums;
        }

        .libelle-stat {
            display: block;
            margin-top: 6px;
            font-size: 14px;
            font-weight: 600;
            color: var(--muted);
        }

        /* ===== Sections ===== */
        section.bloc { padding: 78px 0; }
```

- [ ] **Step 2 : Insérer la section HTML**

Entre la fermeture du Hero et le commentaire des services, remplacer :

```html
        </div>
    </section>

    <!-- ===== SERVICES ===== -->
```

par :

```html
        </div>
    </section>

    <!-- ===== STATISTIQUES ===== -->
    <section class="bloc alterne" id="stats">
        <div class="conteneur">
            <div class="titre-section revele">
                <span class="sur-titre">Notre ambition</span>
                <h2>Une plateforme conçue pour passer à l'échelle</h2>
                <p>Chiffres cibles de déploiement du réseau partenaire — pas des statistiques d'usage actuelles.</p>
            </div>
            <div class="grille-stats">
                <div class="carte-stat revele">
                    <span class="pastille">{% icone "users" %}</span>
                    <strong class="chiffre-anime" data-cible="15000">0</strong>
                    <span class="libelle-stat">Assurés couverts</span>
                </div>
                <div class="carte-stat revele">
                    <span class="pastille">{% icone "stethoscope" %}</span>
                    <strong class="chiffre-anime" data-cible="500">0</strong>
                    <span class="libelle-stat">Médecins partenaires</span>
                </div>
                <div class="carte-stat revele">
                    <span class="pastille">{% icone "building" %}</span>
                    <strong class="chiffre-anime" data-cible="250">0</strong>
                    <span class="libelle-stat">Prestataires du réseau</span>
                </div>
                <div class="carte-stat revele">
                    <span class="pastille">{% icone "bar-chart" %}</span>
                    <strong class="chiffre-anime" data-cible="100000">0</strong>
                    <span class="libelle-stat">Consultations gérées</span>
                </div>
            </div>
        </div>
    </section>

    <!-- ===== SERVICES ===== -->
```

- [ ] **Step 3 : Étendre le script de fin de fichier avec le compteur animé**

Remplacer le `<script>` existant en fin de fichier :

```html
    <script>
        // Apparition des sections au défilement
        const observateur = new IntersectionObserver((entrees) => {
            entrees.forEach((entree) => {
                if (entree.isIntersecting) {
                    entree.target.classList.add('visible');
                    observateur.unobserve(entree.target);
                }
            });
        }, { threshold: 0.12 });

        document.querySelectorAll('.revele').forEach((el) => observateur.observe(el));
    </script>
```

par :

```html
    <script>
        // Apparition des sections au défilement
        const observateur = new IntersectionObserver((entrees) => {
            entrees.forEach((entree) => {
                if (entree.isIntersecting) {
                    entree.target.classList.add('visible');
                    observateur.unobserve(entree.target);
                }
            });
        }, { threshold: 0.12 });

        document.querySelectorAll('.revele').forEach((el) => observateur.observe(el));

        // Compteur anime des statistiques (Phase 1) : desactive si
        // prefers-reduced-motion, sinon anime de 0 a la valeur cible.
        const reductionMouvement = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        function animerCompteur(element) {
            const cible = parseInt(element.dataset.cible, 10);
            if (reductionMouvement || !cible) {
                element.textContent = cible.toLocaleString('fr-FR') + '+';
                return;
            }
            const duree = 1200;
            const debut = performance.now();
            function etape(instant) {
                const progression = Math.min((instant - debut) / duree, 1);
                const progressionAttenuee = 1 - Math.pow(1 - progression, 2);
                const valeur = Math.round(cible * progressionAttenuee);
                element.textContent = valeur.toLocaleString('fr-FR') + (progression >= 1 ? '+' : '');
                if (progression < 1) requestAnimationFrame(etape);
            }
            requestAnimationFrame(etape);
        }

        const observateurStats = new IntersectionObserver((entrees) => {
            entrees.forEach((entree) => {
                if (entree.isIntersecting) {
                    animerCompteur(entree.target);
                    observateurStats.unobserve(entree.target);
                }
            });
        }, { threshold: 0.4 });

        document.querySelectorAll('.chiffre-anime').forEach((el) => observateurStats.observe(el));
    </script>
```

- [ ] **Step 4 : Vérification**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py test Plateform_medicale`
Expected: `OK` (145 tests, aucune régression).

- [ ] **Step 5 : Vérification manuelle (obligatoire)**

Run: `python manage.py runserver`, ouvrir `/` :
- Une nouvelle section "Notre ambition" apparaît entre le Hero et "Nos services", fond turquoise clair (même teinte que "Comment ça marche" plus bas).
- La ligne de texte sur les chiffres cibles (pas des stats d'usage réelles) est bien visible, pas cachée.
- En faisant défiler jusqu'à cette section, les 4 chiffres s'animent de 0 jusqu'à leur valeur finale (15 000+, 500+, 250+, 100 000+, séparateur de milliers français) en un peu plus d'une seconde.
- Survoler une carte stat : léger soulèvement + ombre.
- Activer `prefers-reduced-motion: reduce` dans les DevTools, recharger la page, faire défiler jusqu'à la section : les chiffres s'affichent directement à leur valeur finale, sans animation de comptage.
- Aucune erreur dans la console navigateur.

- [ ] **Step 6 : Commit**

```bash
git add Plateform_medicale/templates/landing.html
git commit -m "feat(landing): section statistiques avec compteur anime"
```

---

## Après cette phase

Ce plan couvre uniquement la Phase 1 (sur 4) de la feuille de route du spec
`docs/superpowers/specs/2026-07-21-landing-premium-phase1-design.md`. Ne pas
mettre à jour `FONCTIONNEMENT.txt`/`GUIDE_UTILISATEUR.md` ni supprimer le
dossier `docs/superpowers/` à l'issue de cette phase seule : ces mises à
jour n'ont lieu qu'une fois les 4 phases livrées (la landing page premium
dans son ensemble), pour éviter de documenter une fonctionnalité à moitié
terminée. Passer ensuite au brainstorming de la Phase 2 (section
partenaires, refonte des cartes Services, timeline "Comment ça marche").
