import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont

out_dir = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe\illustrations_isep"
os.makedirs(out_dir, exist_ok=True)

print("Génération de l'ensemble des figures et logos académiques pour le mémoire ISEP...")

def draw_header_footer(ax, title=""):
    ax.axis("off")
    ax.set_facecolor("#FFFFFF")

# =============================================================================
# 1. DIAGRAMMES DE CLASSES UML (Style Sobre ISEP : Boîtes noires, fond blanc/gris très pâle)
# =============================================================================

# FIGURE 1 : Diagramme de classes - Docteur
fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
draw_header_footer(ax)

# Classe Docteur
rect1 = patches.Rectangle((0.3, 0.62), 0.4, 0.35, linewidth=1.5, edgecolor="#000000", facecolor="#F8FAFC")
ax.add_patch(rect1)
ax.plot([0.3, 0.7], [0.91, 0.91], color="#000000", lw=1.2)
ax.plot([0.3, 0.7], [0.75, 0.75], color="#000000", lw=1.2)
ax.text(0.5, 0.935, "Docteur", weight="bold", fontsize=11, ha="center")
doc_attrs = "+ int id_docteur\n+ string matricule_ordre\n+ string nom\n+ string prenom\n+ string specialite\n+ string telephone"
ax.text(0.32, 0.83, doc_attrs, fontsize=8.5, va="center", family="monospace")
doc_methods = "+ consulterPlanning()\n+ voirDossierPatient()\n+ faireConsultation()\n+ redigerOrdonnance()\n+ apposerSceauHMAC()"
ax.text(0.32, 0.68, doc_methods, fontsize=8.5, va="center", family="monospace")

# Classe Consultation
rect2 = patches.Rectangle((0.55, 0.22), 0.38, 0.28, linewidth=1.5, edgecolor="#000000", facecolor="#FFFFFF")
ax.add_patch(rect2)
ax.plot([0.55, 0.93], [0.45, 0.45], color="#000000", lw=1.2)
ax.plot([0.55, 0.93], [0.34, 0.34], color="#000000", lw=1.2)
ax.text(0.74, 0.47, "Consultation", weight="bold", fontsize=10, ha="center")
cons_attrs = "+ int id_consultation\n+ date date_consultation\n+ string motif\n+ string diagnostic\n+ float montant_honoraires"
ax.text(0.57, 0.395, cons_attrs, fontsize=8, va="center", family="monospace")
cons_methods = "+ effectuerConsultation()\n+ emettreFeuilleSoins()\n+ cloturerConsultation()"
ax.text(0.57, 0.28, cons_methods, fontsize=8, va="center", family="monospace")

# Classe Ordonnance
rect3 = patches.Rectangle((0.08, 0.22), 0.38, 0.28, linewidth=1.5, edgecolor="#000000", facecolor="#FFFFFF")
ax.add_patch(rect3)
ax.plot([0.08, 0.46], [0.45, 0.45], color="#000000", lw=1.2)
ax.plot([0.08, 0.46], [0.34, 0.34], color="#000000", lw=1.2)
ax.text(0.27, 0.47, "Ordonnance", weight="bold", fontsize=10, ha="center")
ord_attrs = "+ int id_ordonnance\n+ string code_qr\n+ string sceau_hmac\n+ string statut (ACTIVE/DELIVREE)\n+ date date_prescription"
ax.text(0.10, 0.395, ord_attrs, fontsize=8, va="center", family="monospace")
ord_methods = "+ genererSceauHMAC()\n+ ajouterLigneMedicament()\n+ imprimerFormatA4()\n+ invaliderOrdonnance()"
ax.text(0.10, 0.28, ord_methods, fontsize=8, va="center", family="monospace")

# Liens
ax.annotate("", xy=(0.7, 0.50), xytext=(0.55, 0.62), arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
ax.text(0.53, 0.56, "1", fontsize=9, weight="bold")
ax.text(0.68, 0.52, "1..*", fontsize=9, weight="bold")

ax.annotate("", xy=(0.32, 0.50), xytext=(0.42, 0.62), arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
ax.text(0.40, 0.56, "1", fontsize=9, weight="bold")
ax.text(0.30, 0.52, "0..*", fontsize=9, weight="bold")

# Lien Consultation -> Ordonnance
ax.annotate("", xy=(0.46, 0.36), xytext=(0.55, 0.36), arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
ax.text(0.51, 0.38, "0..1", fontsize=9, weight="bold", ha="center")

ax.set_xlim(0, 1)
ax.set_ylim(0.1, 1.02)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_01_classe_docteur.png"), dpi=300)
plt.close()

# FIGURE 2 : Diagramme de classes - Patient / Assuré
fig, ax = plt.subplots(figsize=(8, 7.5), dpi=300)
draw_header_footer(ax)

# Classe Patient
rect1 = patches.Rectangle((0.3, 0.58), 0.42, 0.38, linewidth=1.5, edgecolor="#000000", facecolor="#F8FAFC")
ax.add_patch(rect1)
ax.plot([0.3, 0.72], [0.90, 0.90], color="#000000", lw=1.2)
ax.plot([0.3, 0.72], [0.74, 0.74], color="#000000", lw=1.2)
ax.text(0.51, 0.925, "Patient / Assuré", weight="bold", fontsize=11, ha="center")
pat_attrs = "+ int id_patient\n+ string matricule_ipm\n+ string numero_carte_iso\n+ string nom, prenom\n+ string groupe_sanguin\n+ float solde_plafond_annuel\n+ boolean est_ayant_droit"
ax.text(0.32, 0.82, pat_attrs, fontsize=8.5, va="center", family="monospace")
pat_methods = "+ afficherCarteISO7810()\n+ consulterSoldePlafond()\n+ declarerAyantDroit()\n+ soumettreRemboursement()\n+ voirHistoriqueSoins()"
ax.text(0.32, 0.66, pat_methods, fontsize=8.5, va="center", family="monospace")

# Classe RendezVous
rect2 = patches.Rectangle((0.05, 0.18), 0.40, 0.28, linewidth=1.5, edgecolor="#000000", facecolor="#FFFFFF")
ax.add_patch(rect2)
ax.plot([0.05, 0.45], [0.41, 0.41], color="#000000", lw=1.2)
ax.plot([0.05, 0.45], [0.30, 0.30], color="#000000", lw=1.2)
ax.text(0.25, 0.43, "RendezVous", weight="bold", fontsize=10, ha="center")
rdv_attrs = "+ int id_rdv\n+ datetime date_heure\n+ string motif\n+ string statut (CONFIRME, ANNULE)\n+ int id_medecin"
ax.text(0.07, 0.355, rdv_attrs, fontsize=8, va="center", family="monospace")
rdv_methods = "+ reserverCreneau()\n+ modifierRendezVous()\n+ annulerRendezVous()\n+ notifierRappel()"
ax.text(0.07, 0.24, rdv_methods, fontsize=8, va="center", family="monospace")

# Classe DemandeRemboursement
rect3 = patches.Rectangle((0.55, 0.18), 0.42, 0.28, linewidth=1.5, edgecolor="#000000", facecolor="#FFFFFF")
ax.add_patch(rect3)
ax.plot([0.55, 0.97], [0.41, 0.41], color="#000000", lw=1.2)
ax.plot([0.55, 0.97], [0.30, 0.30], color="#000000", lw=1.2)
ax.text(0.76, 0.43, "DemandeRemboursement", weight="bold", fontsize=10, ha="center")
remb_attrs = "+ int id_demande\n+ float montant_reclame\n+ float montant_accorde\n+ file justificatif_facture\n+ string statut_liquidation"
ax.text(0.57, 0.355, remb_attrs, fontsize=8, va="center", family="monospace")
remb_methods = "+ soumettreDemande()\n+ joindreQuittance()\n+ suivreStatutTraitement()\n+ percevoirIndemnite()"
ax.text(0.57, 0.24, remb_methods, fontsize=8, va="center", family="monospace")

# Liens
ax.annotate("", xy=(0.25, 0.46), xytext=(0.40, 0.58), arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
ax.text(0.38, 0.54, "1", fontsize=9, weight="bold")
ax.text(0.26, 0.48, "0..*", fontsize=9, weight="bold")

ax.annotate("", xy=(0.76, 0.46), xytext=(0.60, 0.58), arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
ax.text(0.61, 0.54, "1", fontsize=9, weight="bold")
ax.text(0.75, 0.48, "0..*", fontsize=9, weight="bold")

ax.set_xlim(0, 1)
ax.set_ylim(0.08, 1.02)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_02_classe_patient.png"), dpi=300)
plt.close()

# FIGURE 3 : Diagramme de classes - Pharmacie, Gestionnaire et Administrateur
fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=300)
draw_header_footer(ax)

# Classe Utilisateur (Parent)
rect_p = patches.Rectangle((0.32, 0.72), 0.36, 0.25, linewidth=1.5, edgecolor="#000000", facecolor="#F1F5F9")
ax.add_patch(rect_p)
ax.plot([0.32, 0.68], [0.92, 0.92], color="#000000", lw=1.2)
ax.plot([0.32, 0.68], [0.81, 0.81], color="#000000", lw=1.2)
ax.text(0.50, 0.94, "<<Abstract>>\nUtilisateur", weight="bold", fontsize=9.5, ha="center")
u_attrs = "+ int id_utilisateur\n+ string email, mot_de_passe\n+ string role (RBAC)\n+ boolean is_active"
ax.text(0.34, 0.865, u_attrs, fontsize=8, va="center", family="monospace")
u_methods = "+ seConnecter()\n+ seDeconnecter()\n+ reinitialiserMotDePasse()"
ax.text(0.34, 0.765, u_methods, fontsize=8, va="center", family="monospace")

# Classes Enfants (Héritage)
roles = [
    ("Pharmacien", 0.05, "+ string licence_officine\n+ int id_prestataire", "+ scannerQRCode()\n+ verifierOrdonnance()\n+ validerDelivranceACID()\n+ calculerTiersPayant()"),
    ("GestionnaireIPM", 0.37, "+ int id_organisme\n+ string matricule_agent", "+ gererConventions()\n+ instruireRemboursements()\n+ teletransmettreBordereaux()\n+ auditerDepenses()"),
    ("Administrateur", 0.69, "+ string niveau_privilege\n+ boolean acces_journal", "+ gererUtilisateurs()\n+ superviserLogsCDP()\n+ executerSauvegardeNeon()\n+ surveillerMetriques()")
]

for name, x, attrs, methods in roles:
    r = patches.Rectangle((x, 0.24), 0.27, 0.33, linewidth=1.5, edgecolor="#000000", facecolor="#FFFFFF")
    ax.add_patch(r)
    ax.plot([x, x+0.27], [0.52, 0.52], color="#000000", lw=1.2)
    ax.plot([x, x+0.27], [0.44, 0.44], color="#000000", lw=1.2)
    ax.text(x+0.135, 0.54, name, weight="bold", fontsize=9.5, ha="center")
    ax.text(x+0.015, 0.48, attrs, fontsize=7.5, va="center", family="monospace")
    ax.text(x+0.015, 0.34, methods, fontsize=7.5, va="center", family="monospace")
    
    # Flèche d'héritage (triangle blanc)
    ax.annotate("", xy=(0.50, 0.72), xytext=(x+0.135, 0.57),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, mutation_scale=15))

ax.set_xlim(0, 1)
ax.set_ylim(0.12, 1.02)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_03_classe_admin_gestionnaire.png"), dpi=300)
plt.close()

# FIGURE 4 : Diagramme de classes global consolidé (Toutes les entités clés)
fig, ax = plt.subplots(figsize=(9, 7.5), dpi=300)
draw_header_footer(ax)

boxes = [
    ("Organisme (IPM)", 0.05, 0.75, 0.25, 0.18, "+ string raison_sociale\n+ string ninea\n+ float budget_annuel", "+ liquiderDossier()"),
    ("PlanCouverture", 0.05, 0.45, 0.25, 0.18, "+ float taux_remboursement\n+ float plafond_annuel\n+ string exclusions", "+ appliquerTaux()"),
    ("Patient (Assuré)", 0.38, 0.45, 0.26, 0.20, "+ string matricule_ipm\n+ string numero_carte_iso\n+ float solde_plafond", "+ afficherCarteISO()"),
    ("Prestataire", 0.70, 0.75, 0.25, 0.18, "+ string nom_etablissement\n+ string type (CLINIQUE/PHARMACIE)\n+ float latitude, longitude", "+ localiserLeaflet()"),
    ("Convention", 0.38, 0.75, 0.26, 0.18, "+ string code_convention\n+ date date_signature\n+ float taux_tiers_payant", "+ verifierAccord()"),
    ("Consultation", 0.70, 0.45, 0.25, 0.20, "+ date date_acte\n+ string motif\n+ float montant_total", "+ genererOrdonnance()"),
    ("Ordonnance", 0.38, 0.12, 0.26, 0.22, "+ string code_qr\n+ string sceau_hmac\n+ string statut_delivrance", "+ controlerValidite()"),
    ("Delivrance", 0.70, 0.12, 0.25, 0.22, "+ date date_delivrance\n+ float part_organisme\n+ float part_patient", "+ executerVerrouACID()")
]

for title, x, y, w, h, attrs, meth in boxes:
    r = patches.Rectangle((x, y), w, h, linewidth=1.2, edgecolor="#000000", facecolor="#F8FAFC")
    ax.add_patch(r)
    ax.plot([x, x+w], [y+h-0.045, y+h-0.045], color="#000000", lw=1.0)
    ax.text(x+w/2, y+h-0.03, title, weight="bold", fontsize=8.5, ha="center")
    ax.text(x+0.01, y+h/2-0.01, attrs, fontsize=6.8, va="center", family="monospace")
    ax.plot([x, x+w], [y+0.04, y+0.04], color="#000000", lw=0.8)
    ax.text(x+0.01, y+0.02, meth, fontsize=6.8, va="center", family="monospace")

# Lignes de relations
ax.plot([0.175, 0.175], [0.75, 0.63], "k-", lw=1.0)
ax.text(0.19, 0.69, "1..*", fontsize=7.5)

ax.plot([0.30, 0.38], [0.55, 0.55], "k-", lw=1.0)
ax.text(0.34, 0.57, "1..*", fontsize=7.5)

ax.plot([0.30, 0.38], [0.84, 0.84], "k-", lw=1.0)
ax.plot([0.64, 0.70], [0.84, 0.84], "k-", lw=1.0)
ax.text(0.34, 0.86, "1..*", fontsize=7.5)
ax.text(0.67, 0.86, "1..*", fontsize=7.5)

ax.plot([0.51, 0.51], [0.45, 0.34], "k-", lw=1.0)
ax.text(0.53, 0.39, "0..*", fontsize=7.5)

ax.plot([0.64, 0.70], [0.22, 0.22], "k-", lw=1.0)
ax.text(0.67, 0.24, "1..1", fontsize=7.5)

ax.plot([0.825, 0.825], [0.45, 0.34], "k-", lw=1.0)
ax.text(0.84, 0.39, "0..1", fontsize=7.5)

ax.set_xlim(0, 1)
ax.set_ylim(0.05, 1.0)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "fig_04_classe_globale.png"), dpi=300)
plt.close()

print("Diagrammes de classes UML générés avec succès.")
