# Scan QR par caméra — écran pharmacien (plan direction artistique, item 8)

Spec temporaire (voir CLAUDE.md, "Documents de travail") : à supprimer une
fois l'item 8 livré et vérifié, le contenu utile étant reporté dans
FONCTIONNEMENT.txt si pertinent au moment où le plan de direction
artistique complet sera clôturé.

## Contexte

Le plan de direction artistique (`docs/superpowers/plan-direction-artistique.md`,
item 8) relève un écart de confiance : le landing page vend le "scan" d'une
ordonnance ("vérifiable en pharmacie en un scan", "La pharmacie scanne"),
mais `scanner_ordonnance.html` est aujourd'hui un simple champ texte —
aucune caméra, aucun mécanisme de scan réel. Décision actée avec
l'utilisateur (AskUserQuestion) : livrer un vrai scan caméra plutôt que de
simplement reformuler le texte de l'écran.

## Objectif

Ajouter un scan QR par caméra sur `scanner_ordonnance.html`, sans rien
casser du flux existant (saisie manuelle, douchette physique qui émule un
clavier). Le code décodé par la caméra doit suivre exactement le même
chemin que la saisie manuelle : même champ `code_qr`, même endpoint POST,
aucun changement de vue/modèle/URL.

## Décisions actées (AskUserQuestion, ne pas rouvrir)

- Activation caméra par **bouton explicite** ("Scanner avec la caméra"),
  jamais automatique à l'arrivée sur l'écran — cohérent avec le bouton
  "Rechercher sur la carte" déjà utilisé pour `ajouter_prestataire.html`,
  évite une demande de permission surprise.
- Après détection d'un code valide : **arrêt de la caméra, remplissage du
  champ, soumission automatique du formulaire** — reproduit le
  comportement d'une douchette physique (tape le code puis Entrée), même
  flux pour les deux méthodes de scan.
- Librairie de décodage : **jsQR** (pure JS, ~30 Ko) via CDN + `integrity`
  (SRI) + `crossorigin`, même convention que Leaflet (`ajouter_prestataire.html`)
  et Chart.js (`rapports.html`). Écarté : html5-qrcode (interface propre
  trop lourde à réaligner sur la charte SantéSN), API native
  `BarcodeDetector` seule (support navigateur incomplet, exclurait une
  partie des pharmaciens sur mobile — Safari/iOS, Firefox).

## Architecture

Changement strictement côté client. `scanner_ordonnance` (views.py) et
`scanner_ordonnance.html` (formulaire POST vers lui-même) restent
inchangés dans leur contrat : un champ `code_qr` soumis en POST, résolu
côté serveur en `Ordonnance` ou message d'erreur. Le scan caméra n'est
qu'une deuxième façon de remplir ce même champ avant soumission,
au même titre que la douchette.

```
Bouton "Scanner avec la caméra"
        │ clic
        ▼
getUserMedia({video:{facingMode:{ideal:"environment"}}})
        │ succès                              │ échec
        ▼                                     ▼
Flux vidéo affiché + boucle              Message inline dans la zone
requestAnimationFrame :                  de statut (jamais d'alert()) :
  canvas.drawImage(video)                 - permission refusée
  jsQR(imageData) → code détecté ?        - aucune caméra détectée
        │ oui                             - contexte non sécurisé (HTTPS)
        ▼                                  Le champ manuel reste utilisable.
Arrêt des tracks vidéo
Remplissage #code_qr
form.submit()  → flux existant inchangé
```

## Composants ajoutés à `scanner_ordonnance.html`

1. **Script CDN** : `<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js" integrity="sha384-b5Ya4Bq3qCyz39m2ISh+4DxjAIljdeFwK/BsXLuj9gugaNwAcj/ia15fxNZL9Nlx" crossorigin="anonymous"></script>`.
   `1.4.0` confirmée version `latest` du paquet npm `jsqr` (jsdelivr API,
   vérifié le 2026-07-24) ; hash `integrity` calculé en sha384 sur le
   fichier réellement téléchargé depuis ce CDN (pas une valeur devinée).

2. **Détection de capacité au chargement de la page** (avant tout clic) :
   si `!('mediaDevices' in navigator)` ou `!('getUserMedia' in navigator.mediaDevices)`
   ou `typeof jsQR !== 'function'` (échec de chargement du CDN), le bouton
   "Scanner avec la caméra" reste masqué (`hidden`) — pas de bouton mort
   qui échoue au clic.

3. **Bouton "Scanner avec la caméra"** : icône `qr-scan` existante
   (`templatetags/icones.py`), classe `.button .btn` comme le bouton
   "Rechercher sur la carte".

4. **Panneau caméra** (masqué par défaut, `hidden` retiré au clic) :
   - `<video>` (`autoplay`, `muted`, `playsinline` — requis iOS Safari
     pour éviter le plein écran natif).
   - `<canvas>` caché (`display:none`), utilisé uniquement pour extraire
     les pixels de chaque frame via `drawImage` + `getImageData`.
   - Cadre de visée CSS (bordure superposée en `position:absolute`,
     couleur `--primary-accent`), purement décoratif.
   - Zone de statut `role="status" aria-live="polite"` (même pattern que
     l'item 7, `Plateform_medicale/templates/ajouter_prestataire.html`) :
     "Recherche d'un code…" pendant le scan, "Code détecté, vérification…"
     juste avant la soumission automatique, ou message d'erreur si échec.
   - Bouton "Fermer la caméra" : arrête les tracks vidéo, masque le
     panneau, revient à la saisie manuelle seule.

5. **JS inline** (le projet n'a pas de dossier `static/` — tout le
   CSS/JS/SVG est inline dans les templates, cf. CLAUDE.md "Design
   system") :
   - `demarrerScan()` : `getUserMedia` → si succès, affiche le panneau,
     lance la boucle `requestAnimationFrame`. Si échec, catch typé :
     - `NotAllowedError` → "Accès à la caméra refusé. Autorisez la caméra
       dans les paramètres du navigateur, ou utilisez la saisie manuelle."
     - `NotFoundError` → "Aucune caméra détectée sur cet appareil."
     - autre → "Scan par caméra indisponible sur cet appareil ou cette
       connexion (HTTPS requis). Utilisez la saisie manuelle ou une
       douchette ci-dessous."
   - Boucle de décodage : throttling raisonnable non nécessaire (jsQR sur
     une image ~640×480 est largement assez rapide pour tourner à chaque
     frame sur du matériel de pharmacie standard).
   - `arreterScan()` : appelle `.stop()` sur chaque `MediaStreamTrack`,
     masque le panneau. Appelée à la fois par "Fermer la caméra" et
     automatiquement après une détection réussie.
   - Sur détection : `arreterScan()` → `input#code_qr.value = code` →
     `form.requestSubmit()` (pas de nouvel appel réseau custom : réutilise
     le POST existant du formulaire).

## Ce qui ne change PAS

- `views.py` (`scanner_ordonnance`, `valider_delivrance`) : aucune
  modification. Le champ `code_qr` est déjà normalisé côté serveur
  (`.strip().upper()`), donc peu importe la casse restituée côté client.
- Le flux manuel (saisie clavier ou douchette qui tape le code + Entrée)
  reste le chemin par défaut, inchangé, et fonctionne même sans caméra.
- `landing.html` : aucun changement de texte nécessaire — la promesse
  "scan" devient littéralement exacte.

## Gestion d'erreur (résumé)

| Cas | Comportement |
|---|---|
| Navigateur sans `getUserMedia` / CDN jsQR indisponible | Bouton caméra jamais affiché (détection au chargement) |
| Permission refusée | Message inline dans la zone de statut, saisie manuelle toujours utilisable |
| Aucune caméra détectée | Idem |
| Contexte non sécurisé (HTTP simple, hors localhost) | Idem (message générique HTTPS) |
| Code décodé ne correspond à aucune ordonnance | Comportement serveur existant, inchangé (message toast "Aucune ordonnance ne correspond à ce code.") |

## Tests

La partie caméra réelle (accès matériel, décodage d'une vraie image) n'est
pas testable par le client de test Django — pas de matériel caméra en CI.
Périmètre des tests automatisés (`Plateform_medicale/tests.py`,
`EspacePharmacienTests` ou classe dédiée) :

- Le script `jsQR` (balise `<script>` avec l'URL CDN attendue) et le
  bouton "Scanner avec la caméra" sont présents dans la réponse de
  `GET scanner_ordonnance`.
- La zone de statut porte bien `role="status"` et `aria-live="polite"`.
- Les deux tests existants (`test_scan_code_valide_affiche_ordonnance`,
  `test_scan_code_invalide_affiche_erreur`) continuent de passer sans
  modification — ils prouvent que le flux manuel/douchette est intact.

Vérification manuelle (`runserver`) : le chemin de dégradation (bouton
masqué / message d'erreur si caméra indisponible) sera vérifié dans le
navigateur. Cet environnement de développement n'a probablement pas de
caméra accessible — le flux de décodage réel ne pourra pas être testé de
bout en bout ici ; ce sera signalé explicitement plutôt que présenté comme
vérifié.

## Hors périmètre (YAGNI)

- Pas de sélecteur multi-caméra (avant/arrière) : `facingMode:"environment"`
  suffit, un pharmacien scanne un document, pas un selfie.
- Pas de lecture de codes-barres 1D ni d'autres formats : uniquement QR
  (seul format généré par `Ordonnance.qr_svg`).
- Pas de torche/flash : fonctionnalité additionnelle non demandée, à
  ajouter seulement si un besoin concret émerge.
