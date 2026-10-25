import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont

output_dir = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe\figures"
os.makedirs(output_dir, exist_ok=True)

# Palette de couleurs SantéSN & ISEP
COLOR_PRIMARY = "#0E7C86"     # Teal médical
COLOR_SECONDARY = "#6A3E1E"   # Brun chaud ISEP
COLOR_ACCENT = "#E0824F"      # Corail
COLOR_DARK = "#0F172A"        # Ardoise foncée
COLOR_LIGHT = "#F8FAFC"       # Fond carte
COLOR_BORDER = "#CBD5E1"      # Bordure
COLOR_SUCCESS = "#10B981"     # Vert succès
COLOR_DANGER = "#EF4444"      # Rouge alerte

print("Génération des figures professionnelles pour le mémoire...")

# -------------------------------------------------------------
# FIGURE 1 : Schéma du circuit papier traditionnel
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
ax.set_facecolor("#FFFFFF")
ax.axis("off")

etapes = [
    ("1. Patient / Assuré", "Déplacement physique au siège\nDemande de bon papier", "#F1F5F9", "#475569"),
    ("2. Secrétariat IPM", "Vérification manuelle\nÉmission bon manuscrit", "#F1F5F9", "#475569"),
    ("3. Médecin Traitant", "Consultation clinique\nOrdonnance papier volante", "#F1F5F9", "#475569"),
    ("4. Pharmacie", "Calcul manuel quote-part\nDispensation & archivage", "#FEE2E2", "#DC2626"),
    ("5. Audit & Liquidation", "Tri des liasses papier\nContrôle a posteriori", "#FEE2E2", "#DC2626"),
    ("6. Règlement Financier", "Paiement différé (60-90j)\nTrésorerie pénalisée", "#FEF3C7", "#D97706"),
]

x_start = 0.5
box_w = 2.4
box_h = 1.3
gap = 0.6

for i, (titre, desc, bg, border_c) in enumerate(etapes):
    x = x_start + (i % 3) * (box_w + gap)
    y = 2.4 if i < 3 else 0.5
    
    rect = patches.FancyBboxPatch(
        (x, y), box_w, box_h,
        boxstyle="round,pad=0.1,rounding_size=0.15",
        facecolor=bg, edgecolor=border_c, linewidth=1.5
    )
    ax.add_patch(rect)
    
    ax.text(x + box_w/2, y + box_h - 0.3, titre, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#0F172A")
    ax.text(x + box_w/2, y + 0.45, desc, ha="center", va="center", fontsize=8, color="#334155")
    
    # Flèches
    if i < 2:
        ax.annotate("", xy=(x + box_w + gap, y + box_h/2), xytext=(x + box_w, y + box_h/2),
                    arrowprops=dict(arrowstyle="->", color="#0E7C86", lw=2))
    elif i == 2:
        ax.annotate("", xy=(x + box_w/2, 1.8), xytext=(x + box_w/2, y),
                    arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2))
    elif i > 3:
        pass

# Flèches ligne inférieure (de droite à gauche)
ax.annotate("", xy=(x_start + box_w + gap, 1.15), xytext=(x_start + 2*(box_w + gap), 1.15),
            arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2))
ax.annotate("", xy=(x_start + box_w, 1.15), xytext=(x_start + box_w + gap, 1.15),
            arrowprops=dict(arrowstyle="->", color="#D97706", lw=2))

ax.set_xlim(0, 9.5)
ax.set_ylim(0, 4.2)
plt.title("Figure 1.1 : Circuit papier traditionnel et points de rupture du tiers payant au Sénégal", fontsize=11, fontweight="bold", pad=12, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_01_circuit_papier.png"), dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# FIGURE 2 : Matrice SWOT
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
ax.set_facecolor("#FFFFFF")
ax.axis("off")

quadrants = [
    ("FORCES (STRENGTHS)", ["• Cadre réglementaire solide (Loi IPM 1975)", "• Réseau d'officines privées dense au Sénégal", "• Solidarité professionnelle des branches d'entreprises", "• Tiers payant reconnu par les conventions collectives"], 0.2, 3.2, "#EFF6FF", "#1D4ED8"),
    ("FAIBLESSES (WEAKNESSES)", ["• Dépendance intégrale aux liasses papier volantes", "• Vérification des plafonds a posteriori (fraudes)", "• Lenteur administrative et déplacements physiques", "• Délais de paiement de 60 à 120 jours pour les officines"], 4.8, 3.2, "#FEF2F2", "#B91C1C"),
    ("OPPORTUNITÉS (OPPORTUNITIES)", ["• Explosion du mobile money (Wave, Orange Money)", "• Volonté politique d'extension de la SEN-CSU", "• Démocratisation de l'Internet 4G/5G et des PWA", "• Technologies QR Code adoptées massivement"], 0.2, 0.4, "#F0FDF4", "#15803D"),
    ("MENACES (THREATS)", ["• Résistance au changement des habitudes papier", "• Zones à couverture réseau intermittente", "• Risque de cyberattaques sur les données de santé", "• Coûts des solutions propriétaires étrangères"], 4.8, 0.4, "#FFFBEB", "#B45309"),
]

for titre, points, x, y, bg, border_c in quadrants:
    rect = patches.FancyBboxPatch((x, y), 4.3, 2.5, boxstyle="round,pad=0.1,rounding_size=0.12", facecolor=bg, edgecolor=border_c, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + 0.3, y + 2.2, titre, fontsize=10, fontweight="bold", color=border_c)
    
    cur_y = y + 1.8
    for pt in points:
        ax.text(x + 0.3, cur_y, pt, fontsize=8.2, color="#1E293B")
        cur_y -= 0.4

ax.set_xlim(0, 9.4)
ax.set_ylim(0, 6.2)
plt.title("Figure 2.1 : Matrice SWOT de la gestion de la couverture maladie d'entreprise au Sénégal", fontsize=11, fontweight="bold", pad=12, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_02_swot_existant.png"), dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# FIGURE 3 : Diagramme de Cas d'Utilisation Global UML
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_facecolor("#FFFFFF")
ax.axis("off")

# Cadre Système
rect_sys = patches.Rectangle((2.8, 0.3), 6.5, 5.3, linewidth=2, edgecolor="#0E7C86", facecolor="#F8FAFC", linestyle="--")
ax.add_patch(rect_sys)
ax.text(6.0, 5.35, "Système SantéSN (Plateforme Web & PWA)", fontsize=11, fontweight="bold", ha="center", color="#0E7C86")

acteurs = [
    ("Assuré\n(Patient)", 1.2, 4.4),
    ("Médecin\nTraitant", 1.2, 3.1),
    ("Pharmacien\nd'Officine", 1.2, 1.8),
    ("Gestionnaire\nIPM", 1.2, 0.5),
    ("Administrateur\nIT", 9.8, 2.8)
]

for nom, x, y in acteurs:
    # Icône bonhomme simplifié
    ax.plot(x, y + 0.3, "o", markersize=14, color="#6A3E1E")
    ax.plot([x, x], [y + 0.2, y - 0.1], "-", color="#6A3E1E", lw=2)
    ax.plot([x - 0.25, x + 0.25], [y + 0.1, y + 0.1], "-", color="#6A3E1E", lw=2)
    ax.plot([x, x - 0.2], [y - 0.1, y - 0.35], "-", color="#6A3E1E", lw=2)
    ax.plot([x, x + 0.2], [y - 0.1, y - 0.35], "-", color="#6A3E1E", lw=2)
    ax.text(x, y - 0.55, nom, ha="center", va="center", fontsize=8, fontweight="bold", color="#0F172A")

cases = [
    ("Consulter carte ISO & QR Code", 4.3, 4.8),
    ("Suivre jauge plafond familial", 7.2, 4.8),
    ("Prescrire ordonnance certifiée HMAC", 4.3, 3.8),
    ("Consulter historique & dossier patient", 7.2, 3.8),
    ("Scanner ordonnance (Caméra jsQR)", 4.3, 2.7),
    ("Valider délivrance atomique (ACID)", 7.2, 2.7),
    ("Paramétrer conventions prestataires", 4.3, 1.6),
    ("Télétransmettre bordereaux mensuels", 7.2, 1.6),
    ("Superviser sécurité & audit CDP", 5.8, 0.7)
]

for label, cx, cy in cases:
    ellipse = patches.Ellipse((cx, cy), 2.5, 0.65, facecolor="#FFFFFF", edgecolor="#0E7C86", linewidth=1.2)
    ax.add_patch(ellipse)
    ax.text(cx, cy, label, ha="center", va="center", fontsize=7.5, color="#0F172A")

# Connexions acteurs -> cas
lignes = [
    ((1.2, 4.4), (3.1, 4.8)), ((1.2, 4.4), (6.0, 4.8)),
    ((1.2, 3.1), (3.1, 3.8)), ((1.2, 3.1), (6.0, 3.8)),
    ((1.2, 1.8), (3.1, 2.7)), ((1.2, 1.8), (6.0, 2.7)),
    ((1.2, 0.5), (3.1, 1.6)), ((1.2, 0.5), (6.0, 1.6)),
    ((9.8, 2.8), (7.0, 0.7))
]

for (x1, y1), (x2, y2) in lignes:
    ax.plot([x1, x2], [y1, y2], color="#94A3B8", lw=1.2, linestyle="-")

ax.set_xlim(0, 10.8)
ax.set_ylim(-0.2, 5.8)
plt.title("Figure 3.1 : Diagramme de cas d'utilisation global de la plateforme SantéSN (UML)", fontsize=11, fontweight="bold", pad=12, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_03_diagramme_use_cases.png"), dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# FIGURE 6 : Architecture Cloud MVT 4 couches
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
ax.set_facecolor("#FFFFFF")
ax.axis("off")

couches = [
    ("1. COUCHE CLIENT (PWA RESPONSIVE)", ["Navigateurs Chrome, Safari, Firefox sur Mobile & Desktop", "Service Worker (Cache Hors-ligne) · Décodeur jsQR · Leaflet SIG"], 4.0, "#F0FDF4", "#15803D"),
    ("2. COUCHE PASSERELLE & CDN (VERCEL EDGE)", ["Terminaison TLS 1.3 / HTTPS · WAF Anti-DDoS · Routage WSGI"], 2.8, "#EFF6FF", "#1D4ED8"),
    ("3. COUCHE MÉTIER & APPLICATION (DJANGO 5.2)", ["Contrôle RBAC (5 rôles) · Sceau HMAC-SHA256 · Tiers Payant & Plafonds · Passerelle WhatsApp"], 1.6, "#FEF2F2", "#B91C1C"),
    ("4. COUCHE DONNÉES (POSTGRESQL NEON CLOUD)", ["Cluster PostgreSQL Serverless · Transactions ACID (select_for_update) · Sauvegardes chiffrées"], 0.4, "#FFFBEB", "#B45309"),
]

for titre, sous_titres, y, bg, border_c in couches:
    rect = patches.FancyBboxPatch((1.0, y), 8.0, 0.95, boxstyle="round,pad=0.08,rounding_size=0.12", facecolor=bg, edgecolor=border_c, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(5.0, y + 0.65, titre, ha="center", va="center", fontsize=9.5, fontweight="bold", color=border_c)
    ax.text(5.0, y + 0.28, " · ".join(sous_titres), ha="center", va="center", fontsize=8, color="#334155")
    
    if y > 0.5:
        ax.annotate("", xy=(5.0, y - 0.2), xytext=(5.0, y),
                    arrowprops=dict(arrowstyle="<->", color="#0E7C86", lw=2))

ax.set_xlim(0, 10.0)
ax.set_ylim(0, 5.2)
plt.title("Figure 3.2 : Architecture multicouche Cloud et flux sécurisés de SantéSN", fontsize=11, fontweight="bold", pad=12, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_06_architecture_cloud_mvt.png"), dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# FIGURE 12 : Gantt Scrum
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
ax.set_facecolor("#FFFFFF")

sprints = [
    "Sprint 6 : QA, PWA Hors-ligne & Tests",
    "Sprint 5 : Conventions & SIG Leaflet",
    "Sprint 4 : Espace Pharmacie & Scanner",
    "Sprint 3 : Espace Médecin & HMAC",
    "Sprint 2 : Assurés & Cartes ISO 7810",
    "Sprint 1 : Socle & Multi-Tenancy",
    "Phase 0 : Cadrage & Benchmark"
]

debuts = [12, 10, 8, 6, 4, 2, 0]
durees = [2, 2, 2, 2, 2, 2, 2]
couleurs = ["#0E7C86", "#14B8A6", "#2DD4BF", "#0D9488", "#0F766E", "#115E59", "#6A3E1E"]

bars = ax.barh(sprints, durees, left=debuts, color=couleurs, height=0.55, edgecolor="#0F172A", linewidth=0.8)

ax.set_xlabel("Semaines de Réalisation (Semaine 1 à Semaine 14)", fontsize=9.5, fontweight="bold", labelpad=8)
ax.set_xlim(0, 14.5)
ax.set_xticks(range(0, 15, 2))
ax.set_xticklabels([f"S{w}" for w in range(0, 15, 2)], fontsize=9)
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar, d, deb in zip(bars, durees, debuts):
    ax.text(deb + d/2, bar.get_y() + bar.get_height()/2, f"{d} sem.", ha="center", va="center", color="#FFFFFF", fontsize=8, fontweight="bold")

plt.title("Figure 2.2 : Chronogramme prévisionnel des sprints Scrum (14 semaines)", fontsize=11, fontweight="bold", pad=12, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_12_planning_gantt_scrum.png"), dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# FIGURE 13 : Validation des 196 tests
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
ax.set_facecolor("#FFFFFF")

modules = [
    "Authentification & RBAC",
    "Espace Assuré & Cartes ISO",
    "Pharmacie & Scanner Optique",
    "Médecin & Ordonnances HMAC",
    "Gestionnaire & Multi-Tenant",
    "PWA, Hors-ligne & Légal CDP"
]
tests_counts = [32, 35, 46, 43, 22, 18]

y_pos = range(len(modules))
bars = ax.barh(y_pos, tests_counts, color="#0E7C86", height=0.55, edgecolor="#095059", linewidth=1)

ax.set_yticks(y_pos)
ax.set_yticklabels(modules, fontsize=9, fontweight="bold")
ax.invert_yaxis()
ax.set_xlabel("Nombre de tests automatisés validés (100% Succès)", fontsize=9.5, fontweight="bold", labelpad=8)
ax.set_xlim(0, 55)
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar, count in zip(bars, tests_counts):
    ax.text(count + 1, bar.get_y() + bar.get_height()/2, f"{count} tests (OK)", ha="left", va="center", color="#0E7C86", fontsize=8.5, fontweight="bold")

plt.title("Figure 4.1 : Répartition des 196 tests automatisés validés par domaine fonctionnel", fontsize=10.5, fontweight="bold", pad=12, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_13_resultats_tests_196.png"), dpi=300)
plt.close(fig)

# -------------------------------------------------------------
# FIGURE 8 : Carte Assuré ISO 7810
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.2), dpi=300)
ax.set_facecolor("#FFFFFF")
ax.axis("off")

# Corps de la carte (Ratio carte bancaire 85.6mm x 53.98mm)
card = patches.FancyBboxPatch((0.5, 0.4), 6.0, 3.4, boxstyle="round,pad=0.08,rounding_size=0.25", facecolor="#0E7C86", edgecolor="#095059", linewidth=2)
ax.add_patch(card)

# Bande décorative et en-tête
ax.text(1.0, 3.4, "SantéSN", fontsize=15, fontweight="bold", color="#FFFFFF")
ax.text(1.0, 3.15, "CARTE NATIONALE DE TIERS PAYANT", fontsize=7, color="#E0F2FE", fontweight="bold")
ax.text(6.0, 3.4, "IPM SANTÉSN", fontsize=10, fontweight="bold", color="#FEF08A", ha="right")

# Puce dorée réaliste
chip = patches.FancyBboxPatch((1.0, 2.0), 0.9, 0.7, boxstyle="round,pad=0.04,rounding_size=0.08", facecolor="#FACC15", edgecolor="#CA8A04", linewidth=1.2)
ax.add_patch(chip)
ax.plot([1.0, 1.9], [2.35, 2.35], color="#A16207", lw=1)
ax.plot([1.45, 1.45], [2.0, 2.7], color="#A16207", lw=1)

# QR Code fictif réaliste
qr_bg = patches.Rectangle((4.8, 1.2), 1.3, 1.3, facecolor="#FFFFFF", edgecolor="#CBD5E1")
ax.add_patch(qr_bg)
ax.text(5.45, 1.85, "QR CODE\nSÉCURISÉ", ha="center", va="center", fontsize=6.5, fontweight="bold", color="#0F172A")

# Données patient
ax.text(1.0, 1.5, "MOUSSA DIOP", fontsize=11, fontweight="bold", color="#FFFFFF")
ax.text(1.0, 1.25, "Matricule : SN-2026-77123", fontsize=8.5, color="#E0F2FE")
ax.text(1.0, 1.0, "Formule : Cadres Supérieurs (Taux : 80%)", fontsize=7.5, color="#FEF08A")

# Plafond jauge
ax.text(1.0, 0.7, "Plafond restant : 1 125 000 FCFA / 1 500 000 FCFA", fontsize=7, color="#FFFFFF")
gauge_bg = patches.Rectangle((1.0, 0.52), 3.5, 0.12, facecolor="#095059")
ax.add_patch(gauge_bg)
gauge_fill = patches.Rectangle((1.0, 0.52), 2.6, 0.12, facecolor="#10B981")
ax.add_patch(gauge_fill)

ax.set_xlim(0, 7.0)
ax.set_ylim(0, 4.2)
plt.title("Figure 4.2 : Rendu visuel de la carte d'assuré dématérialisée (Format ISO 7810 ID-1)", fontsize=10.5, fontweight="bold", pad=10, color=COLOR_DARK)
plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig_08_carte_assure_iso7810.png"), dpi=300)
plt.close(fig)

print("Toutes les figures professionnelles ont été générées avec succès dans :", output_dir)
