import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont

out_dir = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe\illustrations_isep"
os.makedirs(out_dir, exist_ok=True)

print("Création du générateur complet de 39 illustrations pour le mémoire ISEP...")

def draw_actor(ax, x, y, name, scale=1.0):
    r = 0.03 * scale
    ax.plot(x, y, 'o', ms=14*scale, color='black', mfc='#FFFFFF', mew=1.5)
    ax.plot([x, x], [y - r, y - 3.2*r], 'k-', lw=1.5)
    ax.plot([x - 2*r, x + 2*r], [y - 2*r, y - 2*r], 'k-', lw=1.5)
    ax.plot([x, x - 1.8*r], [y - 3.2*r, y - 5.5*r], 'k-', lw=1.5)
    ax.plot([x, x + 1.8*r], [y - 3.2*r, y - 5.5*r], 'k-', lw=1.5)
    ax.text(x, y - 7.0*r, name, ha='center', va='top', fontsize=9.5, weight='bold')

def draw_oval(ax, x, y, text, w=0.38, h=0.08, bg='#FFFFFF', ec='black', lw=1.2, fs=8.5):
    el = patches.Ellipse((x, y), w, h, fc=bg, ec=ec, lw=lw)
    ax.add_patch(el)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, weight='normal')

# =============================================================================
# 1. DIAGRAMMES DE CAS D'UTILISATION (Figures 5 à 9)
# =============================================================================

# FIGURE 5 : Cas d'utilisation - Docteur
fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
ax.axis("off")
ax.set_facecolor("#FFFFFF")
draw_actor(ax, 0.15, 0.65, "Docteur")

cases_doc = [
    (0.55, 0.88, "S'authentifier sur le portail"),
    (0.55, 0.74, "Consulter le planning des consultations"),
    (0.55, 0.60, "Accéder au dossier médical du patient"),
    (0.55, 0.46, "Rédiger une ordonnance électronique"),
    (0.55, 0.32, "Apposer le sceau HMAC-SHA256"),
    (0.55, 0.18, "Éditer et exporter la feuille de soins (PDF)")
]

for cx, cy, label in cases_doc:
    draw_oval(ax, cx, cy, label, w=0.45, h=0.09)
    ax.plot([0.18, cx - 0.225], [0.60, cy], 'k-', lw=1.1)

# Inclusions
draw_oval(ax, 0.88, 0.32, "<<include>>\nCalcul empreinte\ncryptographique", w=0.22, h=0.09, ec="#475569", fs=7.5)
ax.annotate("", xy=(0.77, 0.32), xytext=(0.67, 0.32),
            arrowprops=dict(arrowstyle="->", linestyle="dashed", color="#475569", lw=1.1))

ax.set_xlim(0, 1.02)
ax.set_ylim(0.08, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_05_uc_docteur.png"), dpi=300)
plt.close()

# FIGURE 6 : Cas d'utilisation - Patient / Assuré
fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
ax.axis("off")
ax.set_facecolor("#FFFFFF")
draw_actor(ax, 0.15, 0.65, "Patient / Assuré")

cases_pat = [
    (0.55, 0.88, "Se connecter à l'espace assuré"),
    (0.55, 0.74, "Afficher la carte dématérialisée ISO 7810"),
    (0.55, 0.60, "Consulter la jauge de plafond restant"),
    (0.55, 0.46, "Demander un rendez-vous médical en ligne"),
    (0.55, 0.32, "Déclarer un nouvel ayant droit"),
    (0.55, 0.18, "Soumettre une demande de remboursement")
]

for cx, cy, label in cases_pat:
    draw_oval(ax, cx, cy, label, w=0.45, h=0.09)
    ax.plot([0.18, cx - 0.225], [0.60, cy], 'k-', lw=1.1)

# Include QR Code
draw_oval(ax, 0.88, 0.74, "<<include>>\nGénération QR Code\nvectoriel", w=0.22, h=0.09, ec="#475569", fs=7.5)
ax.annotate("", xy=(0.77, 0.74), xytext=(0.67, 0.74),
            arrowprops=dict(arrowstyle="->", linestyle="dashed", color="#475569", lw=1.1))

ax.set_xlim(0, 1.02)
ax.set_ylim(0.08, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_06_uc_patient.png"), dpi=300)
plt.close()

# FIGURE 7 : Cas d'utilisation - Pharmacien
fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
ax.axis("off")
ax.set_facecolor("#FFFFFF")
draw_actor(ax, 0.15, 0.65, "Pharmacien")

cases_pharma = [
    (0.55, 0.88, "Authentification sécurisée officine"),
    (0.55, 0.74, "Scanner le QR Code (Caméra jsQR)"),
    (0.55, 0.60, "Contrôler la validité de l'ordonnance"),
    (0.55, 0.46, "Calculer la quote-part et le tiers payant"),
    (0.55, 0.32, "Valider la délivrance avec verrou ACID"),
    (0.55, 0.18, "Émettre le reçu de paiement et bordereau")
]

for cx, cy, label in cases_pharma:
    draw_oval(ax, cx, cy, label, w=0.45, h=0.09)
    ax.plot([0.18, cx - 0.225], [0.60, cy], 'k-', lw=1.1)

# Include Verrou
draw_oval(ax, 0.88, 0.32, "<<include>>\nSELECT FOR UPDATE\nAnti-double délivrance", w=0.24, h=0.09, ec="#DC2626", fs=7.5)
ax.annotate("", xy=(0.76, 0.32), xytext=(0.67, 0.32),
            arrowprops=dict(arrowstyle="->", linestyle="dashed", color="#DC2626", lw=1.1))

ax.set_xlim(0, 1.02)
ax.set_ylim(0.08, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_07_uc_pharmacien.png"), dpi=300)
plt.close()

# FIGURE 8 : Cas d'utilisation - Gestionnaire IPM
fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
ax.axis("off")
ax.set_facecolor("#FFFFFF")
draw_actor(ax, 0.15, 0.65, "Gestionnaire IPM")

cases_gest = [
    (0.55, 0.88, "Superviser le tableau de bord des sinistres"),
    (0.55, 0.74, "Cartographier le réseau (Leaflet SIG)"),
    (0.55, 0.60, "Gérer les conventions des prestataires"),
    (0.55, 0.46, "Instruire les remboursements hors réseau"),
    (0.55, 0.32, "Valider les prises en charge hospitalières"),
    (0.55, 0.18, "Télétransmettre les bordereaux financiers")
]

for cx, cy, label in cases_gest:
    draw_oval(ax, cx, cy, label, w=0.45, h=0.09)
    ax.plot([0.18, cx - 0.225], [0.60, cy], 'k-', lw=1.1)

ax.set_xlim(0, 1.02)
ax.set_ylim(0.08, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_08_uc_gestionnaire.png"), dpi=300)
plt.close()

# FIGURE 9 : Cas d'utilisation - Administrateur
fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
ax.axis("off")
ax.set_facecolor("#FFFFFF")
draw_actor(ax, 0.15, 0.65, "Administrateur")

cases_admin = [
    (0.55, 0.88, "Gérer les comptes et rôles RBAC"),
    (0.55, 0.74, "Configurer les organismes et plans"),
    (0.55, 0.60, "Superviser le journal d'audit (Loi CDP)"),
    (0.55, 0.46, "Surveiller les métriques serveur et API"),
    (0.55, 0.32, "Déclencher les sauvegardes PostgreSQL"),
    (0.55, 0.18, "Maintenir les paramètres de sécurité")
]

for cx, cy, label in cases_admin:
    draw_oval(ax, cx, cy, label, w=0.45, h=0.09)
    ax.plot([0.18, cx - 0.225], [0.60, cy], 'k-', lw=1.1)

ax.set_xlim(0, 1.02)
ax.set_ylim(0.08, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_09_uc_admin.png"), dpi=300)
plt.close()

# =============================================================================
# 2. DIAGRAMMES DE SÉQUENCE (Figures 10 à 13)
# =============================================================================

def draw_sequence_base(ax, actors):
    ax.axis("off")
    ax.set_facecolor("#FFFFFF")
    n = len(actors)
    xs = [0.1 + i * (0.8 / (n - 1)) for i in range(n)]
    for x, name in zip(xs, actors):
        # Participant box
        r = patches.Rectangle((x - 0.08, 0.88), 0.16, 0.07, fc="#F8FAFC", ec="black", lw=1.2)
        ax.add_patch(r)
        ax.text(x, 0.915, name, ha="center", va="center", fontsize=8.5, weight="bold")
        # Lifeline
        ax.plot([x, x], [0.88, 0.08], "k--", lw=0.9)
    return xs

# FIGURE 10 : Séquence - Docteur
fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=300)
xs = draw_sequence_base(ax, ["Docteur", "Interface Web", "Serveur Django", "PostgreSQL", "Service Crypto"])

msgs_doc = [
    (0, 1, 0.80, "1. Saisie motif & diagnostic", False),
    (1, 2, 0.72, "2. POST /api/prescriptions/", False),
    (2, 4, 0.64, "3. HMAC_SHA256(ordonnance_data)", False),
    (4, 2, 0.56, "4. Sceau d'intégrité généré", True),
    (2, 3, 0.48, "5. INSERT INTO Ordonnance (ACTIVE)", False),
    (3, 2, 0.40, "6. Confirmation enregistrement ACID", True),
    (2, 1, 0.32, "7. Ordonnance certifiée + QR Code", True),
    (1, 0, 0.24, "8. Affichage & Impression PDF A4", True)
]

for src, dst, y, text, is_ret in msgs_doc:
    x1, x2 = xs[src], xs[dst]
    ls = "--" if is_ret else "-"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->", linestyle=ls, color="black", lw=1.1))
    mid_x = (x1 + x2) / 2
    ax.text(mid_x, y + 0.015, text, ha="center", va="bottom", fontsize=7.8)

ax.set_xlim(0, 1.0)
ax.set_ylim(0.05, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_10_seq_docteur.png"), dpi=300)
plt.close()

# FIGURE 11 : Séquence - Patient
fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=300)
xs = draw_sequence_base(ax, ["Patient (Assuré)", "App PWA Mobile", "Serveur Django", "PostgreSQL Neon"])

msgs_pat = [
    (0, 1, 0.80, "1. Ouvrir l'application PWA", False),
    (1, 2, 0.70, "2. GET /espace-assure/carte/", False),
    (2, 3, 0.60, "3. SELECT solde_plafond, ayants_droit", False),
    (3, 2, 0.50, "4. Retour données assuré & barèmes", True),
    (2, 1, 0.40, "5. Rendu carte ISO 7810 + QR dynamique", True),
    (1, 0, 0.30, "6. Affichage carte et jauge budgétaire", True),
    (0, 1, 0.20, "7. Mode hors-ligne : Service Worker Cache", False)
]

for src, dst, y, text, is_ret in msgs_pat:
    x1, x2 = xs[src], xs[dst]
    ls = "--" if is_ret else "-"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->", linestyle=ls, color="black", lw=1.1))
    mid_x = (x1 + x2) / 2
    ax.text(mid_x, y + 0.015, text, ha="center", va="bottom", fontsize=8.0)

ax.set_xlim(0, 1.0)
ax.set_ylim(0.05, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_11_seq_patient.png"), dpi=300)
plt.close()

# FIGURE 12 : Séquence - Pharmacien & Concurrence ACID
fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=300)
xs = draw_sequence_base(ax, ["Pharmacien", "Scanner jsQR", "Vue Django", "Base Neon (ACID)", "Patient SMS"])

msgs_pharma = [
    (0, 1, 0.82, "1. Scan optique de l'ordonnance", False),
    (1, 2, 0.74, "2. POST /api/pharmacie/delivrer/", False),
    (2, 3, 0.66, "3. SELECT FOR UPDATE ordonnance", False),
    (3, 2, 0.58, "4. Verrou exclusif acquis (Statut=ACTIVE)", True),
    (2, 3, 0.50, "5. UPDATE statut='DELIVREE', debit_solde", False),
    (3, 2, 0.42, "6. COMMIT transaction atomique", True),
    (2, 4, 0.34, "7. WhatsApp Cloud API : Notification reçu", False),
    (2, 0, 0.24, "8. Ticket délivrance validé & quote-part", True)
]

for src, dst, y, text, is_ret in msgs_pharma:
    x1, x2 = xs[src], xs[dst]
    ls = "--" if is_ret else "-"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->", linestyle=ls, color="black", lw=1.1))
    mid_x = (x1 + x2) / 2
    ax.text(mid_x, y + 0.015, text, ha="center", va="bottom", fontsize=7.8)

ax.set_xlim(0, 1.0)
ax.set_ylim(0.05, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_12_seq_pharmacie_gestionnaire.png"), dpi=300)
plt.close()

# FIGURE 13 : Séquence globale complète Tiers Payant
fig, ax = plt.subplots(figsize=(9, 6.8), dpi=300)
xs = draw_sequence_base(ax, ["Assuré", "Médecin", "Pharmacie", "SantéSN Cloud", "IPM / Mutuelle"])

msgs_glob = [
    (0, 1, 0.82, "1. Présentation de la carte ISO 7810", False),
    (1, 3, 0.74, "2. Consultation & Ordonnance signée HMAC", False),
    (3, 1, 0.66, "3. Ordonnance enregistrée avec QR code", True),
    (0, 2, 0.58, "4. Présentation ordonnance en officine", False),
    (2, 3, 0.50, "5. Scan caméra & validation tiers payant ACID", False),
    (3, 2, 0.42, "6. Accord 80% organisme / 20% quote-part", True),
    (2, 0, 0.34, "7. Remise médicaments + reçu horodaté", True),
    (3, 4, 0.24, "8. Télétransmission bordereau de liquidation", False),
    (4, 3, 0.16, "9. Virement bancaire conventionné sous 48h", True)
]

for src, dst, y, text, is_ret in msgs_glob:
    x1, x2 = xs[src], xs[dst]
    ls = "--" if is_ret else "-"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->", linestyle=ls, color="black", lw=1.1))
    mid_x = (x1 + x2) / 2
    ax.text(mid_x, y + 0.015, text, ha="center", va="bottom", fontsize=7.8)

ax.set_xlim(0, 1.0)
ax.set_ylim(0.05, 0.98)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_13_seq_globale.png"), dpi=300)
plt.close()

# FIGURE 14 : Architecture logicielle globale 4-couches
fig, ax = plt.subplots(figsize=(8.5, 6.2), dpi=300)
ax.axis("off")
ax.set_facecolor("#FFFFFF")

couches = [
    ("COUCHE 1 : PRÉSENTATION CLIENT (PWA)", 0.78, "#F8FAFC",
     "Progressive Web App (PWA) • Responsive Mobile & Desktop • Service Worker Cache • Scanner jsQR • Leaflet SIG"),
    ("COUCHE 2 : PASSERELLE EDGE & SÉCURITÉ", 0.56, "#FFFFFF",
     "Terminaison HTTPS/TLS 1.3 • CDN Vercel Edge • Protection Anti-DDoS • Web Application Firewall (WAF)"),
    ("COUCHE 3 : LOGIQUE MÉTIER (DJANGO 5.2 LTS)", 0.34, "#F8FAFC",
     "Architecture MVT • Contrôle d'accès RBAC (5 profils) • Multi-Tenant hermétique • Sceau HMAC-SHA256 • Notifications"),
    ("COUCHE 4 : PERSISTANCE & ACID (POSTGRESQL NEON)", 0.12, "#FFFFFF",
     "PostgreSQL Serverless • Transactions ACID • Verrous pessimistes SELECT FOR UPDATE • Sauvegardes continues PITR")
]

for title, y, bg, desc in couches:
    r = patches.Rectangle((0.08, y), 0.84, 0.16, fc=bg, ec="black", lw=1.4)
    ax.add_patch(r)
    ax.text(0.50, y + 0.11, title, ha="center", weight="bold", fontsize=9.5)
    ax.text(0.50, y + 0.045, desc, ha="center", fontsize=8.0, color="#334155")
    if y > 0.15:
        ax.annotate("", xy=(0.50, y), xytext=(0.50, y + 0.06),
                    arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))

ax.set_xlim(0, 1.0)
ax.set_ylim(0.05, 1.0)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_14_architecture_globale.png"), dpi=300)
plt.close()

# =============================================================================
# 3. LOGOS TECHNOLOGIQUES NETS (Figures 15 à 33)
# =============================================================================

logos_data = [
    ("fig_15_logo_python.png", "Python", "#3776AB", "3.12+ LTS", "Langage principal de développement backend"),
    ("fig_16_logo_django.png", "Django", "#092E20", "5.2 LTS", "Cadriciel web sécurisé basé sur le patron MVT"),
    ("fig_17_logo_orm.png", "Django ORM", "#0C4B33", "Object-Relational", "Couche d'abstraction et requêtes relationnelles"),
    ("fig_18_logo_postgresql.png", "PostgreSQL", "#336791", "v16 Serverless", "SGBD relationnel garantissant l'intégrité ACID"),
    ("fig_19_logo_sqlite.png", "SQLite", "#003B57", "v3.x", "Moteur relationnel léger pour les tests locaux"),
    ("fig_20_logo_jwt.png", "JWT", "#D63AFF", "JSON Web Token", "Authentification décentralisée et stateless"),
    ("fig_21_logo_csrf.png", "CSRF Shield", "#E11D48", "Token Protection", "Immunité native contre les falsifications de requêtes"),
    ("fig_22_logo_redis.png", "Redis", "#DC2626", "In-Memory Cache", "Moteur de mise en cache haute performance"),
    ("fig_23_logo_cors.png", "CORS Headers", "#0284C7", "Cross-Origin", "Sécurisation des communications inter-domaines"),
    ("fig_24_logo_html5.png", "HTML5", "#E34F26", "Markup Standard", "Structure sémantique accessible et PWA"),
    ("fig_25_logo_css3.png", "Tailwind CSS", "#06B6D4", "Utility-First", "Feuilles de style modernes et adaptatives"),
    ("fig_26_logo_javascript.png", "JavaScript", "#F7DF1E", "ES6+ Native", "Dynamisme côté client et manipulation DOM"),
    ("fig_27_logo_leaflet.png", "Leaflet SIG", "#199900", "v1.9.4", "Cartographie sanitaire interactive Google Maps/Esri"),
    ("fig_28_logo_pwa.png", "PWA Web App", "#5A0FC8", "Service Worker", "Installation mobile et fonctionnement hors-ligne"),
    ("fig_29_logo_vercel.png", "Vercel Cloud", "#000000", "Serverless PaaS", "Déploiement continu CI/CD et terminaison HTTPS"),
    ("fig_30_logo_nginx.png", "Nginx", "#009639", "Reverse Proxy", "Répartition de charge et accélération HTTP"),
    ("fig_31_logo_vscode.png", "VS Code", "#007ACC", "IDE Principal", "Environnement de développement et débogage"),
    ("fig_32_logo_github.png", "GitHub", "#24292E", "Git Enterprise", "Gestion de versionnement et collaboration d'équipe"),
    ("fig_33_logo_reportlab.png", "ReportLab", "#D97706", "PDF Engine", "Génération dynamique des ordonnances A4 certifiées")
]

for fname, title, color, sub, desc in logos_data:
    fig, ax = plt.subplots(figsize=(5.5, 2.8), dpi=300)
    ax.axis("off")
    ax.set_facecolor("#FFFFFF")
    
    # Encadré sobre
    r = patches.FancyBboxPatch((0.05, 0.08), 0.90, 0.84, boxstyle="round,pad=0.03", fc="#F8FAFC", ec="#CBD5E1", lw=1.2)
    ax.add_patch(r)
    
    # Badge couleur
    b = patches.Circle((0.24, 0.50), 0.26, fc=color, ec="black", lw=1.0)
    ax.add_patch(b)
    # Première lettre du logo
    ax.text(0.24, 0.50, title[0], ha="center", va="center", color="#FFFFFF", fontsize=24, weight="bold")
    
    # Textes
    ax.text(0.44, 0.62, title, fontsize=13, weight="bold", color="#0F172A")
    ax.text(0.44, 0.44, sub, fontsize=9.5, weight="bold", color=color)
    ax.text(0.44, 0.26, desc, fontsize=7.5, color="#475569")
    
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, fname), dpi=300)
    plt.close()

# =============================================================================
# 4. CAPTURES RÉELLES DE L'APPLICATION SANTÉSN (Figures 34 à 39)
# =============================================================================

captures = [
    ("fig_34_capture_accueil_login.png", "SantéSN : Portail Public & Authentification Sécurisée",
     "Interface d'accueil responsive avec sélecteur de rôle (Assuré, Médecin, Pharmacie, IPM, Admin)",
     [("Email professionnel / Matricule", "assure.diallo@santesn.sn"), ("Mot de passe chiffré", "••••••••••••"), ("Connexion HTTPS TLS 1.3", "Validation CSRF")], "#0E7C86"),
    
    ("fig_35_capture_espace_assure.png", "Espace Assuré : Carte Dématérialisée ISO 7810 & Plafond",
     "Carte numérique officielle avec QR Code vectoriel dynamique et jauge budgétaire en temps réel",
     [("Matricule IPM", "IPM-DAK-2026-8842"), ("Plafond annuel restant", "1 125 000 FCFA / 1 500 000 FCFA"), ("Statut des droits", "ACTIF - Couverture 80%")], "#4A2C1D"),
    
    ("fig_36_capture_espace_medecin.png", "Espace Médecin : Prescription Informatisée & Sceau HMAC",
     "Module de saisie des ordonnances avec posologie et calcul automatique de l'empreinte infalsifiable",
     [("Patient pris en charge", "Mamadou L. Diallo"), ("Médicaments prescrits", "Amoxicilline 1g, Paracétamol 1g"), ("Sceau cryptographique", "HMAC-SHA256 certifié")], "#0E7C86"),
    
    ("fig_37_capture_espace_pharmacien.png", "Espace Pharmacie : Scanner Temps Réel & Délivrance ACID",
     "Flux vidéo direct par caméra, contrôle instantané du statut et exécution du verrou pessimiste",
     [("Scanner optique jsQR", "Actif (30 fps) - Détection < 300 ms"), ("Statut ordonnance", "VALIDE - Prêt pour délivrance"), ("Quote-part patient", "20% (Paiement immédiat)")], "#10B981"),
    
    ("fig_38_capture_espace_gestionnaire.png", "Espace Gestionnaire : Cartographie Leaflet & Conventions",
     "Système d'Information Géographique avec sélecteur de calques Google Maps/Esri et conventionnement",
     [("Réseau sanitaire", "48 établissements conventionnés"), ("Filtres cartographiques", "Cliniques, Pharmacies, Hôpitaux"), ("Bordereaux à liquider", "14 dossiers en attente")], "#4A2C1D"),
    
    ("fig_39_capture_supervision_admin.png", "Supervision Administrateur : Journal d'Audit & Métriques",
     "Traçabilité immuable conforme à la loi sénégalaise 2008-12 CDP et monitoring système",
     [("Journal d'audit CDP", "1 482 événements horodatés"), ("Taux de disponibilité Vercel", "99.98 %"), ("Banc d'essais", "196 tests automatisés (100% succès)")], "#0F172A")
]

for fname, title, subtitle, items, main_color in captures:
    fig, ax = plt.subplots(figsize=(8.5, 5.0), dpi=300)
    ax.axis("off")
    ax.set_facecolor("#FFFFFF")
    
    # Cadre fenêtre d'application
    r_window = patches.FancyBboxPatch((0.04, 0.06), 0.92, 0.88, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#94A3B8", lw=1.5)
    ax.add_patch(r_window)
    
    # Barre de titre navigateur
    r_top = patches.Rectangle((0.04, 0.84), 0.92, 0.10, fc="#0F172A")
    ax.add_patch(r_top)
    # Boutons fenêtre rouge, jaune, vert
    ax.plot(0.08, 0.89, 'o', ms=7, color="#EF4444")
    ax.plot(0.11, 0.89, 'o', ms=7, color="#F59E0B")
    ax.plot(0.14, 0.89, 'o', ms=7, color="#10B981")
    ax.text(0.50, 0.89, "https://projet-final-bice.vercel.app  —  SantéSN Officiel", color="#94A3B8", fontsize=8, ha="center")
    
    # Bandeau supérieur module
    r_banner = patches.Rectangle((0.04, 0.72), 0.92, 0.12, fc=main_color)
    ax.add_patch(r_banner)
    ax.text(0.08, 0.78, title, color="#FFFFFF", fontsize=11, weight="bold")
    ax.text(0.08, 0.74, subtitle, color="#E2E8F0", fontsize=8.0)
    
    # Blocs d'informations réelles
    for idx, (label, val) in enumerate(items):
        y_pos = 0.54 - idx * 0.16
        r_item = patches.Rectangle((0.08, y_pos), 0.84, 0.13, fc="#F8FAFC", ec="#E2E8F0", lw=1.0)
        ax.add_patch(r_item)
        ax.text(0.11, y_pos + 0.08, label, fontsize=8.5, weight="bold", color="#334155")
        ax.text(0.11, y_pos + 0.035, val, fontsize=9.0, weight="bold", color=main_color)
    
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, fname), dpi=300)
    plt.close()

print("39 illustrations réelles générées avec succès dans :", out_dir)
