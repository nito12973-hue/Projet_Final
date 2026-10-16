# Guide de Style & Système de Design SantéSN

> **Projet :** SantéSN — Plateforme Médicale & Tiers Payant Dématérialisé (Sénégal)  
> **Branche de travail :** `refonte-visuelle`  
> **Norme de référence :** WCAG 2.1 Niveau AA · Standards NHS Digital Service Manual & Alan Health SaaS · Mobile-First (Afrique de l'Ouest / 3G/4G).

---

## 1. Direction Visuelle Retenue : « Slate Pro & Turquoise Médical (SaaS Health-Tech) »

### Justification du Choix
Inspirée des standards de référence du secteur (Stripe, Alan Santé, Vercel) :
* **Slate Moderne (`#0F172A`) :** Remplace les fonds sombres lourds par une neutralité institutionnelle haut de gamme.
* **Turquoise Médical Lumineux (`#0E7C86`, `#14B8A6`) :** Accentuation claire, symbolisant le soin et la santé connectée.
* **Typographie Internationale :** Duo **Plus Jakarta Sans** (titres nets et géométriques) et **Inter** (corps de texte hyper-lisible sur mobile et écrans haute résolution).
* **Architecture épurée :**
  - **Administrateur** : Supervision claire de l'infrastructure informatique (Postgres Neon, IAM, Journal de sécurité, Passerelles).
  - **Gestionnaire** : Pilotage opérationnel (assurés, mutuelle, prises en charge, prestataires).

---

## 2. Palette des Jetons CSS (`:root`)

| Jeton CSS | Code Couleur | Usage & Règle WCAG |
| :--- | :--- | :--- |
| `--bg` | `#F8FAFC` | Fond d'écran général ultra-propre (Slate 50) |
| `--surface` | `#FFFFFF` | Cartes, panneaux et tableaux de données |
| `--border` | `#E2E8F0` | Bordures fines et séparateurs discrets (1px) |
| `--text` | `#0F172A` | Texte courant de haute lisibilité (Slate 900) |
| `--muted` | `#64748B` | Libellés secondaires et sous-titres (Slate 500) |
| `--titre` | `#0F172A` | Titres h1, h2, h3 et totaux clés |
| `--primary` | `#0E7C86` | Turquoise médical interactif : boutons primaires, liens |
| `--primary-strong`| `#0A5F67` | Survols et accents foncés |
| `--primary-dark` | `#0F172A` | Deep Slate pour barres de commande et menus |
| `--primary-light`| `#14B8A6` | Liserés lumineux et indicateurs actifs |
| `--primary-accent`| `#0D9488` | Pastilles technologiques |
| `--primary-soft` | `#F0FDFA` | Arrière-plans doux et sélections de lignes |
| `--accent` | `#F97316` | Orange chaleureux pour points d'attention |
| `--ok-bg` / `--ok-fg` | `#ECFDF5` / `#065F46` | Statut **VALIDE** / Règlements acquittés (vert succès) |
| `--attente-bg` / `--attente-fg` | `#FFFBEB` / `#92400E` | Statut **EN_ATTENTE** / Décision requise (ambre) |
| `--refus-bg` / `--refus-fg` | `#FEF2F2` / `#991B1B` | Statut **REFUSE** / Erreur / Blocage (rouge) |

---

## 3. Typographie

* **Titres & Métriques :** `'Plus Jakarta Sans', sans-serif`  
  Poids : 600 / 700 / 800. Interlettrage optimisé (`-0.025em`) pour un rendu net et contemporain.
* **Corps de texte & Formulaires :** `'Inter', system-ui, sans-serif`  
  Poids : 400 (normal), 500 (moyen), 600 (semi-gras).  
  *Taille minimum sur mobile :* `16px` sur tous les champs de saisie pour empêcher le zoom forcé d'iOS Safari.
* **Chiffres, FCFA & Codes d'ordonnances :** `'IBM Plex Mono', monospace`  
  Chiffres tabulaires (`font-variant-numeric: tabular-nums`) pour aligner parfaitement les montants financiers et codes.

---

## 4. Composants Réutilisables & Règles d'Usage

### A. Boutons (`.button`)
* **Hauteur standard :** `44px` (surface tactile minimale WCAG / Apple HIG).
* **Variantes :**
  * `.button.primary` : Action principale (dégradé `--primary-dark` vers `--primary-strong`, texte blanc).
  * `.button` : Action secondaire neutre (fond blanc, bordure `--border`, texte `--titre`).
  * `.button.btn-danger` : Action de suppression ou refus (fond rouge rubis).
  * `.button.btn-sm` : Actions d'appoint ou boutons de lignes de tableau (hauteur alignée à `34px`).

### B. Badges de Statut (`.badge`)
Tout statut doit être intelligible sans dépendre uniquement de la couleur (symbole textuel ou icône associée) :
* `.badge.validee` ou `.badge.ok` : Pour les prises en charge validées et comptes actifs.
* `.badge.en_attente` : Pour les demandes sous instruction IPM ou contrôles anti-fraude.
* `.badge.refusee` : Pour les dossiers rejetés (avec infobulle ou texte explicatif).

### C. Cartes & Panneaux (`.panel`)
* Fond `--surface`, bordure fine `1px solid var(--border)`, rayon de courbure `14px` ou `16px`, ombre portée douce `--ombre-douce`.
* Toujours intégrer un `.panel-header` avec titre `h2` et sous-titre `.subtitle` explicatif.

### D. Tableaux de Données (`table` dans `.table-responsive` ou `.panel`)
* En-têtes `thead th` collants (`sticky`) avec fond opaque pour les défilements longs.
* Alignement numérique à droite pour les montants FCFA, colonnes d'actions harmonisées à droite avec boutons d'hauteur uniforme.
* Responsive : défilement horizontal fluide (`overflow-x: auto; -webkit-overflow-scrolling: touch;`).

### E. Formulaires & Champs de Saisie
* Chaque champ doit posséder un `<label>` explicite lié par `for="id"`.
* Textes d'aide `.aide` directement sous le champ.
* Bloc d'erreur `.erreurs` avec texte rouge visible et attribut `role="alert"`.
* Toujours préserver le token `{% csrf_token %}` dans chaque formulaire POST.

---

## 5. Règles Impératives pour toute Nouvelle Page

1. **Isolation stricte des rôles & Secret médical :**
   * L'Administrateur Général voit l'infrastructure, les organismes et les comptes IAM, mais **JAMAIS** les dossiers médicaux détaillés.
   * L'Assuré ne voit que sa propre couverture et celle de ses ayants droit.
   * Le Médecin ne voit que ses consultations et ses patients.
   * Le Pharmacien ne voit que les ordonnances scannées et sa console de délivrance.
2. **Accessibilité & Navigation Clavier :**
   * Tout élément cliquable doit être accessible au clavier (`Tab`) et présenter un anneau de focus contrasté (`:focus-visible`).
   * Cibles tactiles $\ge 44 \times 44\text{px}$.
3. **Légèreté & Vitesse Réseau :**
   * Aucun chargement de police ou script externe lourd non justifié.
   * Rendu rapide en cache froid : styles intégrés directement dans le gabarit maître pour un affichage immédiat sans saut de mise en page (FOUC).
4. **Zéro Régression :**
   * La suite de tests automatisés (853 tests) doit impérativement rester à 100% verte après chaque modification.

---

## 6. Architecture des Tableaux de Bord & Frontières Métier

### A. Règle d'Isolation Métier Absolue (Admin Général vs Gestionnaire IPM)
* **Administrateur Général (SaaS Multi-Tenant & Infrastructure) :**
  - **Périmètre exclusif :** Supervision des clusters de base de données (Neon PostgreSQL), passerelles télécoms (WhatsApp Cloud API, SMTP TLS), gouvernance des organismes partenaires (entreprises conventionnées et IPM), gestion des comptes d'accès IAM, journal d'audit CDP immuable.
  - **Ce qui lui est rigoureusement masqué :** L'administrateur n'a pas accès aux fiches patients personnelles, aux validations d'ayants droit, aux dossiers d'assurés sans plan, ni aux formulaires d'approbation médicale. Les tuiles opérationnelles de validation IPM (« Ayants droit en attente », « Assurés couverts », « Assuré sans plan ») sont réservées au rôle Gestionnaire et redirigent vers des vues d'audit/rapports lorsqu'elles sont consultées en mode macro-supervision.
* **Gestionnaire IPM (Assureur / Opérateur Tiers-Payant) :**
  - **Périmètre exclusif :** Roster des adhérents et ayants droit, plans de couverture, instruction et validation des prises en charge (PEC), contrôle anti-fraude, relations avec le réseau de soins et liquidation des bordereaux de paiement.

### B. Traitement Visuel des Files d'Attente & Surfaces de Données
* **Suppression de l'empilement sombre (« carré vert ») :**
  - Les files d'attente (`.file-attente`) sont désormais intégrées sur une surface claire (`#FFFFFF`) avec micro-bordure (`--border`), ombre douce et tuiles lumineuses (`#F8FAFC`).
  - L'ambiance visuelle ne cumule plus de blocs sombres successifs, préservant une lecture fluide, aérée et « lisse pour les yeux » conforme aux standards des applications web Django modernes (Stripe, Datadog, Linear).

---

## 7. Infrastructure, Observabilité & Télémétrie DevOps SantéSN

### A. Télémétrie d'Erreurs Sentry SDK
* **Intégration :** `sentry-sdk==2.22.0` initialisé dans `config/settings.py` via `SENTRY_DSN`.
* **Région :** Ingestion Cloud UE (`ingest.de.sentry.io`).
* **Protection stricte des Données Médicales & PII (Conformité CDP Sénégal) :**
  - `send_default_pii=False`.
  - Fonction de nettoyage `before_send` active : assainissement automatique des en-têtes d'autorisation, des cookies de session, et masquage systématique des champs médicaux sensibles (`diagnostic`, `ordonnance`, `medicament`, `posologie`, `numero_identification`, `cin`).
* **Vérification :** Événements réels et exceptions de test testés et reçus avec succès sur Sentry.

### B. Métriques Prometheus & OpenMetrics (`/metrics/`)
* **Endpoint unifié intelligent :** Accessible sur la route standard `/metrics/`.
* **Double mode d'exposition :**
  1. **Mode Navigateur Web (Humain / Administrateur SantéSN) :**
     - Détecte l'en-tête `Accept: text/html` ou le User-Agent navigateur.
     - Exige impérativement une session `User.Role.ADMIN` active. Si non connecté, redirige vers `/connexion/?next=/metrics/` pour préserver l'interface applicative et ne JAMAIS afficher de bandeau public orphelin ("Accueil / Connexion").
     - Rend une console graphique complète (`metrics_prometheus.html`) avec KPIs visuels temps réel (Disponibilité, Latence PostgreSQL, Latence cache mémoire, Échecs de connexion suspectes sur 24h, Répartition des comptes par rôle, Volumes opérationnels : patients, PECs en attente et validées, ordonnances, consultations).
     - Intègre un terminal sombre interactif (`#zone-flux-brut`) avec coloration et bouton « Copier le flux ».
     - Si `?format=raw` est appelé dans un navigateur, la page HTML est rendue avec défilement fluide automatique directement sur le terminal de code, éliminant tout affichage de « page blanche avec du texte brut ».
  2. **Mode Collecteur Machine (Robot Prometheus / Grafana / Scraper) :**
     - Détecte l'agent collecteur ou les appels non-navigateurs.
     - Renvoie le payload standard OpenMetrics `text/plain; version=0.0.4; charset=utf-8` pour ingestion sans aucune dépendance tierce.
* **Intégration Dashboard :**
  - Raccourci direct dans la barre latérale sous « Infrastructure & Support ».
  - Cartes télémétrie interactives sur le Tableau de bord Admin (`dashboard.html`) pour Prometheus et Sentry.

### C. Standard Visuel des Boutons SantéSN (Micro-interaction Signature .btn-expand & .btn-retour-expand)
* **Comportement « Expand au Survol / Focus » :**
  Les boutons d'action d'en-tête et de navigation utilisent la classe signature `.btn-expand` (ou `.btn-retour-expand`) associée à `<span class="expand-text">Texte</span>` :
  - **État repos :** Bouton pilule compact (`height: 36px`, `border-radius: 999px`) affichant l'icône vectorielle seule.
  - **Au survol (hover) / focus / clic :** Le libellé textuel se déplie de façon fluide avec transition CSS (`max-width: 260px; opacity: 1; margin-left: 6px;`).
  - **Lorsque le curseur s'éloigne :** Le bouton se rétracte doucement pour redevenir petit et discret.
* **Zéro « carré vert » ou fond lourd :** Proscrire les gros blocs verts, fonds dégradés lourds ou carrés colorés. Conserver une palette sobre et raffinée (fond blanc ou surface claire, bordure fine `1px solid var(--border)`, ou `.btn-expand.primary` pour l'action principale).

---

## 8. Journal de Bord & Point de Travail Actuel (État d'Avancement & Reprise)

> **Dernière mise à jour :** 13 Octobre 2026  
> **Branche active :** `refonte-visuelle`  
> **Environnement local :** Docker Compose (`santesn_web` sur :8000, `santesn_db` Postgres 17 sur :5432, `santesn_nginx` sur :80).  
> **Règle stricte :** Déploiement distant (`git push`) strictement interdit. Tout est construit et validé localement.

### A. Ce qui a été Réalisé & Validé
1. **Intégration Sentry Complète :**
   - SDK configuré avec DSN Europe officiel et assainisseur de confidentialité médical (RGPD / CDP Sénégal).
   - Bouton de test Sentry déclenché et vérifié dans la supervision système.
2. **Dashboard des Métriques Prometheus (`/metrics/`) :**
   - Vue unifiée éliminant l'erreur 500 et la régression de la page blanche brute.
   - Design graphique 100% cohérent avec SantéSN, navigation sécurisée et préservation du flux machine.
   - En-tête public orphelin supprimé grâce à l'authentification forcée pour tout navigateur.
3. **Mise à Niveau Visuelle Globale des Boutons :**
   - Intégration de pastilles circulaires pleines sur tous les boutons de navigation, d'actualisation et d'action.
   - Contraste WCAG AAA et bordures nettes de `2px`.
4. **Gouvernance Multi-Tenant & Sauvegardes :**
   - Modèles `Organisme` et `ConventionPrestataire` migrés avec succès (`0031` à `0034`).
   - Commande d'automatisation des sauvegardes (`python manage.py sauvegarder_base`) avec calcul de checksum SHA-256 et registre d'intégrité JSON dans `backups/manifest.json`.
5. **Nettoyage Système :**
   - Fichiers temporaires `__pycache__` et `*.pyc` purgés.
   - Images Docker orphelines et 1.23 Go de cache de construction Docker récupérés sans impacter les conteneurs actifs.

### B. Point de Reprise pour la Suite du Travail
Lors de la reprise de la session :
1. Continuer les enrichissements de la plateforme demandés par l'utilisateur sur la branche `refonte-visuelle`.
2. Maintenir la stricte interdiction de push distant (`git push`).
3. Vérifier systématiquement que toute nouvelle vue ou gabarit adopte la nouvelle charte graphique : pas de boîtes blanches plates, pastilles circulaires pour les icônes de boutons, et strict respect de l'isolation des rôles.
4. Les 3 conteneurs locaux (`santesn_web`, `santesn_db`, `santesn_nginx`) sont prêts et sains pour la suite.


