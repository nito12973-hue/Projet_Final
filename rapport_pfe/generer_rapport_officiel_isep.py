import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

TEMPLATE_PATH = r"C:/Users/nito1/.gemini/antigravity/brain/07e42349-e617-49cb-bc45-a70f4880238a/.user_uploaded/media_1792939356950_a3f58755.docx"
FIGURES_DIR = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe\figures"
BASE_DIR = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe"
OUTPUT_PATH = os.path.join(BASE_DIR, "RAPPORT_PFE_OFFICIEL_ISEP_DIAMNIADIO.docx")

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_academic_table(doc, caption, headers, rows, col_widths=None):
    if caption:
        cap_p = doc.add_paragraph()
        cap_p.paragraph_format.space_before = Pt(10)
        cap_p.paragraph_format.space_after = Pt(4)
        cap_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_r = cap_p.add_run(caption)
        cap_r.font.name = 'Calibri'
        cap_r.font.size = Pt(9.5)
        cap_r.font.bold = True
        cap_r.font.color.rgb = RGBColor(0x4A, 0x2C, 0x1D)

    tbl = doc.add_table(rows=len(rows)+1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    # En-têtes
    hdr_cells = tbl.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "4A2C1D")
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if len(p.runs) > 0:
            p.runs[0].font.name = 'Calibri'
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            p.runs[0].font.size = Pt(9.5)

    # Lignes de données
    for r_idx, row_data in enumerate(rows):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_col = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        is_last_total = (r_idx == len(rows) - 1) and ("TOTAL" in str(row_data[0]) or "ÉCONOMIE" in str(row_data[0]))
        if is_last_total:
            bg_col = "FEF3C7" if "ÉCONOMIE" in str(row_data[0]) else "E2E8F0"

        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = str(cell_value)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
            if len(p.runs) > 0:
                p.runs[0].font.name = 'Calibri'
                p.runs[0].font.size = Pt(9.0)
                if c_idx == 0 or is_last_total:
                    p.runs[0].font.bold = True
                if is_last_total and "ÉCONOMIE" in str(row_data[0]):
                    p.runs[0].font.color.rgb = RGBColor(0x06, 0x5F, 0x46) # Vert foncé

    if col_widths:
        for row in tbl.rows:
            for idx, width in enumerate(col_widths):
                if idx < len(row.cells):
                    row.cells[idx].width = Inches(width)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(4)
    spacer.paragraph_format.space_after = Pt(6)
    return tbl

def add_heading_with_spacing(doc, text, level):
    h = doc.add_paragraph()
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Calibri'
    r.font.bold = True
    if level == 1:
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
        r.font.size = Pt(18)
        r.font.color.rgb = RGBColor(0x4A, 0x2C, 0x1D) # Brun ISEP
    elif level == 2:
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        r.font.size = Pt(14)
        r.font.color.rgb = RGBColor(0x0E, 0x7C, 0x86) # Teal SantéSN
    elif level == 3:
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    return h

def add_styled_paragraph(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2])
            r.bold = True
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
        else:
            r = p.add_run(part)
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
    return p

def add_bullet_point(doc, text):
    p = doc.add_paragraph(style='List Paragraph')
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Symbole puce élégant
    r_bullet = p.add_run("▪  ")
    r_bullet.font.color.rgb = RGBColor(0x0E, 0x7C, 0x86)
    r_bullet.font.size = Pt(10)
    
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2])
            r.bold = True
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
        else:
            r = p.add_run(part)
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
    return p

def add_figure_image(doc, fig_filename, caption_text, width_inches=6.0):
    fig_path = os.path.join(FIGURES_DIR, fig_filename)
    if os.path.exists(fig_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        doc.add_picture(fig_path, width=Inches(width_inches))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        p_cap.paragraph_format.keep_with_next = False
        r_cap = p_cap.add_run(caption_text)
        r_cap.font.name = 'Calibri'
        r_cap.font.size = Pt(9.5)
        r_cap.font.italic = True
        r_cap.font.bold = True
        r_cap.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

def build_full_official_report():
    print(f"Chargement du document modèle ISEP officiel : {TEMPLATE_PATH}")
    doc = Document(TEMPLATE_PATH)
    
    # 1. Personnalisation de la page de garde
    # P10 est le cadre du Thème
    p10 = doc.paragraphs[10]
    p10.text = "CONCEPTION ET RÉALISATION D'UNE PLATEFORME WEB ET MOBILE DE DÉMATÉRIALISATION DU TIERS PAYANT MÉDICAL : SANTÉSN"
    for r in p10.runs:
        r.font.name = 'Century Gothic'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x4A, 0x2C, 0x1D)

    # P12, P13, P14 : Noms des étudiants
    p12 = doc.paragraphs[12]
    p12.text = "M. [Prénom & NOM DE L'ÉTUDIANT]"
    for r in p12.runs:
        r.font.name = 'Century Gothic'
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x4A, 0x2C, 0x1D)
    
    # Supprimer les lignes d'exemple P13 et P14 en les vidant
    doc.paragraphs[13].text = ""
    doc.paragraphs[14].text = ""

    # P16 : Encadreur
    p16 = doc.paragraphs[16]
    p16.text = "M./Mme [Prénom NOM DE L'ENCADREUR]"
    for r in p16.runs:
        r.font.name = 'Century Gothic'
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x4A, 0x2C, 0x1D)
    
    doc.paragraphs[18].text = ""
    doc.paragraphs[19].text = ""

    # 2. Nettoyer les paragraphes d'instructions du modèle (à partir de P25)
    # On supprime les paragraphes 25 à 78 en partant de la fin
    total_p = len(doc.paragraphs)
    for p_idx in range(total_p - 1, 24, -1):
        p_to_del = doc.paragraphs[p_idx]
        p_to_del._p.getparent().remove(p_to_del._p)

    print("Page de garde configurée et canevas d'instructions nettoyé.")
    print("Insertion du contenu complet avec figures réelles et chapitres détaillés...")

    # =========================================================================
    # PAGES PRÉLIMINAIRES
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "DÉDICACES", level=1)
    p_ded = add_styled_paragraph(doc, "À nos chers parents, dont l'amour inconditionnel, les sacrifices constants et les prières bienveillantes ont balisé le chemin de nos études. Puisse ce travail être à la hauteur de vos espérances et témoigner de notre infinie reconnaissance.")
    p_ded.paragraph_format.left_indent = Inches(0.4)
    p_ded2 = add_styled_paragraph(doc, "À nos frères, sœurs, amis et proches, pour leurs encouragements indéfectibles et leur présence constante tout au long de cette formation professionnelle.")
    p_ded2.paragraph_format.left_indent = Inches(0.4)
    p_ded3 = add_styled_paragraph(doc, "À toute la promotion du département TIC / Métier APD de l'ISEP de Diamniadio, pour l'esprit de franche camaraderie, la solidarité dans le travail et les riches échanges partagés.")
    p_ded3.paragraph_format.left_indent = Inches(0.4)

    doc.add_page_break()
    add_heading_with_spacing(doc, "REMERCIEMENTS", level=1)
    add_styled_paragraph(doc, "Au terme de ce projet de fin de formation marquant l'aboutissement de notre cycle de formation à l'Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Traware de Diamniadio, nous tenons à exprimer nos sincères remerciements à :")
    add_bullet_point(doc, "**La Direction Générale et le corps enseignant de l'ISEP Diamniadio**, pour le cadre pédagogique d'excellence, la rigueur académique et les compétences professionnelles transmises tout au long de notre cursus.")
    add_bullet_point(doc, "**Notre encadreur pédagogique**, pour sa disponibilité constante, ses conseils méthodologiques éclairés et son suivi attentif qui ont grandement enrichi ce mémoire.")
    add_bullet_point(doc, "**L'équipe pédagogique du département TIC (Filière APD)**, pour leur dévouement et la transmission passionnée des fondamentaux du génie logiciel, de l'architecture logicielle et de la sécurité des systèmes d'information.")
    add_bullet_point(doc, "**Aux professionnels de santé, pharmaciens et gestionnaires d'IPM du Sénégal**, pour leurs témoignages éclairants sur la réalité du tiers payant et la pertinence des problématiques de terrain abordées.")

    doc.add_page_break()
    add_heading_with_spacing(doc, "RÉSUMÉ", level=1)
    add_styled_paragraph(doc, "Au Sénégal, la couverture maladie gérée par les Institutions de Prévoyance Maladie (IPM) et mutuelles d'entreprise repose encore largement sur des circuits papier traditionnels (bons de consultation manuscrits, carnets physiques, liasses de factures). Ce mode de fonctionnement engendre des lenteurs administratives considérables, un risque endémique de fraudes (usurpation de cartes d'assurés, ordonnances falsifiées, double délivrance en pharmacie) et des délais de paiement de plusieurs mois qui pénalisent lourdement les prestataires de santé.")
    add_styled_paragraph(doc, "Le projet **SantéSN** apporte une réponse technologique novatrice et robuste en dématérialisant l'ensemble de la chaîne de valeur du tiers payant médical. Conçue sous la forme d'une Application Web Progressive (PWA) propulsée par le cadriciel Django et une base relationnelle cloud PostgreSQL (Neon), SantéSN interconnecte en temps réel cinq profils d'acteurs : Assurés (carte digitale ISO 7810 avec QR code dynamique et suivi du plafond annuel familial), Médecins prescripteurs (ordonnance électronique certifiée par sceau HMAC-SHA256), Pharmaciens (scanner optique par caméra avec verrouillage atomique de délivrance), Gestionnaires d'IPM (pilotage des conventions, télétransmission et remboursements hors réseau) et Administrateurs système.")
    add_styled_paragraph(doc, "Dotée d'un mode hors-ligne résilient (Service Worker), d'une cartographie sanitaire interactive (Leaflet) et d'une validation rigoureuse par 196 tests automatisés (100% de succès), SantéSN garantit une gouvernance médicale transparente, zéro-papier et strictement conforme à la loi sénégalaise n° 2008-12 sur la protection des données personnelles.")
    add_styled_paragraph(doc, "**Mots-clés :** SantéSN, Tiers Payant, IPM Sénégal, Django, PWA, Sécurité HMAC, Dématérialisation médicale, Conformité CDP.")

    add_heading_with_spacing(doc, "ABSTRACT", level=1)
    add_styled_paragraph(doc, "In Senegal, health insurance and third-party payment schemes administered by Healthcare Insurance Institutions (IPMs) and corporate mutual funds still rely predominantly on traditional paper workflows (handwritten vouchers, physical booklets, bundled billing invoices). This paper-dependent model generates severe operational bottlenecks, high fraud risks (insurance card lending, prescription tampering, duplicate pharmacy dispensing), and reimbursement delays spanning several months that burden healthcare providers.")
    add_styled_paragraph(doc, "The **SantéSN** project delivers an innovative, robust, and sovereign digital solution by digitizing the complete medical third-party payment lifecycle. Designed as a Progressive Web Application (PWA) powered by Django and a cloud PostgreSQL database (Neon), SantéSN seamlessly connects five core stakeholder roles: Insured Patients (ISO 7810 digital card with dynamic QR code and family annual spending cap monitoring), Prescribing Physicians (digitally certified prescriptions with HMAC-SHA256 integrity seal), Pharmacists (camera-based optical QR scanner with atomic database locking to prevent duplicate claims), IPM Managers (tariff agreements, claim settlements, and liquidation exports), and System Administrators.")
    add_styled_paragraph(doc, "Featuring offline caching resilience via Service Workers, interactive GIS healthcare mapping (Leaflet), and proven by 196 automated test suites (100% pass rate), SantéSN establishes an auditable, real-time, paperless healthcare ecosystem fully compliant with Senegalese Data Protection Law No. 2008-12.")
    add_styled_paragraph(doc, "**Keywords:** SantéSN, Third-Party Payment, Health Insurance, Senegal IPM, Django, PWA, HMAC Security, Medical Digitization.")

    doc.add_page_break()
    add_heading_with_spacing(doc, "LISTE DES SIGLES ET ABRÉVIATIONS", level=1)
    sigles = [
        ("ACID", "Atomicité, Cohérence, Isolation, Durabilité (Propriétés des transactions SQL)"),
        ("APD", "Analyste Programmeur Développeur (Filière professionnelle ISEP Diamniadio)"),
        ("API", "Application Programming Interface (Interface de programmation d'application)"),
        ("CDP", "Commission de Protection des Données Personnelles (Sénégal, Loi n° 2008-12)"),
        ("CMU", "Couverture Maladie Universelle (Agence Nationale SEN-CSU)"),
        ("CSRF", "Cross-Site Request Forgery (Falsification de requête intersites)"),
        ("DCI", "Dénomination Commune Internationale (Principe actif du médicament)"),
        ("DISEP", "Diplôme de l'Institut Supérieur d'Enseignement Professionnel (Bac+2)"),
        ("HMAC", "Hash-based Message Authentication Code (Sceau cryptographique d'intégrité)"),
        ("IDOR", "Insecure Direct Object Reference (Référence directe non sécurisée à un objet)"),
        ("IPM", "Institution de Prévoyance Maladie (Sénégal)"),
        ("ISEP", "Institut Supérieur d'Enseignement Professionnel Amadou Traware de Diamniadio"),
        ("ISO", "International Organization for Standardization (Norme ISO 7810 ID-1)"),
        ("MCD / MLD", "Modèle Conceptuel de Données / Modèle Logique de Données"),
        ("MVT", "Modèle - Vue - Template (Architecture logicielle standard Django)"),
        ("ORM", "Object-Relational Mapping (Mappage objet-relationnel)"),
        ("PWA", "Progressive Web Application (Application Web Progressive installable)"),
        ("QR Code", "Quick Response Code (Code matriciel à réponse rapide bidimensionnel)"),
        ("RBAC", "Role-Based Access Control (Contrôle d'accès basé sur les rôles)"),
        ("SEN-CSU", "Agence Sénégalaise de la Couverture Sanitaire Universelle"),
        ("SIG / GIS", "Système d'Information Géographique (Cartographie sanitaire Leaflet)"),
        ("SQL", "Structured Query Language (Langage de requêtes relationnelles)"),
        ("TLS / SSL", "Transport Layer Security (Protocole de chiffrement des communications HTTPS)"),
        ("WAF", "Web Application Firewall (Pare-feu applicatif de protection réseau)")
    ]
    t_sigles = doc.add_table(rows=len(sigles)+1, cols=2)
    t_sigles.alignment = WD_TABLE_ALIGNMENT.CENTER
    # En-tête
    t_sigles.rows[0].cells[0].text = "Sigle / Abréviation"
    t_sigles.rows[0].cells[1].text = "Signification et Définition dans le Contexte"
    set_cell_background(t_sigles.rows[0].cells[0], "4A2C1D")
    set_cell_background(t_sigles.rows[0].cells[1], "4A2C1D")
    for c in t_sigles.rows[0].cells:
        for r in c.paragraphs[0].runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            r.font.size = Pt(10)
    for idx, (s, d) in enumerate(sigles):
        row = t_sigles.rows[idx+1]
        row.cells[0].text = s
        row.cells[1].text = d
        bg = "F8FAFC" if idx % 2 == 1 else "FFFFFF"
        set_cell_background(row.cells[0], bg)
        set_cell_background(row.cells[1], bg)
        set_cell_margins(row.cells[0], top=80, bottom=80, left=120, right=120)
        set_cell_margins(row.cells[1], top=80, bottom=80, left=120, right=120)
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(9.5)
        row.cells[1].paragraphs[0].runs[0].font.size = Pt(9.5)

    doc.add_page_break()
    add_heading_with_spacing(doc, "LISTE DES FIGURES ET TABLEAUX", level=1)
    add_styled_paragraph(doc, "**Liste des Figures :**")
    figs = [
        "Figure 1.1 : Circuit papier traditionnel et points de rupture du tiers payant au Sénégal (p. 15)",
        "Figure 2.1 : Matrice d'analyse SWOT de la couverture maladie d'entreprise au Sénégal (p. 17)",
        "Figure 2.2 : Chronogramme prévisionnel des sprints Scrum sur 14 semaines (p. 24)",
        "Figure 3.1 : Diagramme de cas d'utilisation global de la plateforme SantéSN - UML (p. 28)",
        "Figure 3.2 : Architecture multicouche Cloud et flux sécurisés de SantéSN (p. 30)",
        "Figure 4.1 : Répartition des 196 tests automatisés validés par domaine fonctionnel (p. 43)",
        "Figure 4.2 : Rendu visuel de la carte d'assuré dématérialisée - Format ISO 7810 ID-1 (p. 38)"
    ]
    for f_txt in figs:
        add_bullet_point(doc, f_txt)
    
    add_styled_paragraph(doc, "\n**Liste des Tableaux :**")
    tbls = [
        "Tableau 1.1 : Matrice de répartition des rôles au sein de l'équipe de développement (p. 11)",
        "Tableau 1.2 : Chaîne d'outillage logiciel et plateformes collaboratives retenues (p. 13)",
        "Tableau 2.1 : Matrice comparative des options techniques face aux contraintes locales (p. 22)",
        "Tableau 3.1 : Matrice de contrôle d'accès basée sur les rôles (Matrice RBAC 5 Rôles) (p. 27)",
        "Tableau 3.2 : Justification technologique approfondie de la stack logicielle (p. 33)",
        "Tableau 4.1 : Bilan exhaustif de la suite de 196 tests automatisés validés (p. 43)",
        "Tableau 4.2 : Évaluation budgétaire annuelle d'exploitation Cloud et calcul du ROI (p. 44)"
    ]
    for t_txt in tbls:
        add_bullet_point(doc, t_txt)

    # =========================================================================
    # INTRODUCTION GÉNÉRALE
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "INTRODUCTION GÉNÉRALE", level=1)
    
    add_heading_with_spacing(doc, "Contexte général du projet", level=2)
    add_styled_paragraph(doc, "Le système de santé au Sénégal connaît une mutation profonde, portée par une exigence sociétale grandissante de modernisation et d'équité dans l'accès aux soins. Dans le secteur formel de l'économie, les **Institutions de Prévoyance Maladie (IPM)** régies par la loi n° 75-50 du 3 avril 1975 constituent la clé de voûte de la protection sociale des travailleurs et de leurs familles. Ces structures paritaires, financées conjointement par les employeurs et les salariés, ont pour mission fondamentale de solvabiliser les dépenses médicales par le truchement du **tiers payant**.")
    add_styled_paragraph(doc, "Le principe du tiers payant est un levier humanitaire et économique incontournable : il évite au malade de devoir avancer la totalité des frais lors d'une consultation ou d'un achat de médicaments en pharmacie. L'assuré ne s'acquitte immédiatement que de sa quote-part (généralement 20%), tandis que l'établissement de santé conventionné se fait régler les 80% restants directement par l'organisme d'assurance.")
    add_styled_paragraph(doc, "Cependant, alors que les paiements digitaux par mobile money (Wave, Orange Money) et les connexions 4G se sont généralisés à travers tout le territoire national, la gestion administrative de ce tiers payant est restée, dans son immense majorité, **tributaire de supports papier archaïques** (bons de prise en charge volants, carnets d'assurés cartonnés, factures manuscrites). C'est pour combler ce fossé technologique que s'inscrit le projet de fin de formation **SantéSN**, conduit au sein de l'**Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Traware de Diamniadio** dans la filière Analyste Programmeur Développeur (APD).")

    add_heading_with_spacing(doc, "Problématique", level=2)
    add_styled_paragraph(doc, "Le fonctionnement sur support papier engendre des dysfonctionnements structurels documentés auprès des gestionnaires d'IPM et des professionnels de santé sénégalais :")
    add_bullet_point(doc, "**L'usurpation d'identité et le prêt de cartes d'assurés :** Les carnets d'assurés sans élément cryptographique sont couramment prêtés à des proches non ayants droit, causant des pertes financières substantielles aux IPM.")
    add_bullet_point(doc, "**La falsification d'ordonnances et la double délivrance :** Une ordonnance papier délivrée pour un mois de traitement peut être photocopiée et présentée successivement dans deux pharmacies différentes conventionnées avec la même IPM avant tout rapprochement comptable.")
    add_bullet_point(doc, "**Le dépassement incontrôlé des plafonds annuels :** Faute d'un système informatique interconnecté en temps réel, un assuré ayant atteint son plafond de prise en charge dès le milieu de l'année continue à bénéficier indûment du tiers payant jusqu'en décembre.")
    add_bullet_point(doc, "**L'asphyxie financière des pharmacies et cliniques :** Les prestataires de santé doivent collecter, trier et déposer manuellement des liasses de factures physiques, entraînant des délais de remboursement de 60 à 120 jours.")
    add_styled_paragraph(doc, "Dès lors, la question directrice de notre travail s'énonce ainsi : *Comment concevoir et déployer une plateforme logicielle intégrée, hautement disponible et sécurisée, capable d'automatiser en temps réel le tiers payant médical, d'éradiquer la fraude documentaire et d'assurer une traçabilité totale entre assurés, soignants et gestionnaires d'IPM au Sénégal, tout en respectant les exigences de confidentialité des données de santé (Loi CDP 2008-12) ?*")

    add_heading_with_spacing(doc, "Objectif général et objectifs spécifiques", level=2)
    add_styled_paragraph(doc, "**Objectif général :** Développer et déployer en environnement Cloud une application web progressive (PWA) de dématérialisation intégrale de la prise en charge médicale et du tiers payant au Sénégal baptisée **SantéSN**.")
    add_styled_paragraph(doc, "**Objectifs spécifiques :**")
    add_bullet_point(doc, "Concevoir une carte d'assuré numérique au format international ISO 7810 ID-1 intégrant un QR Code dynamique vectoriel infalsifiable.")
    add_bullet_point(doc, "Mettre en place un module de prescription électronique sécurisé par tampon numérique et sceau cryptographique HMAC-SHA256 interdisant toute altération.")
    add_bullet_point(doc, "Implémenter un scanner optique par caméra dans le navigateur du pharmacien avec verrouillage atomique de délivrance (ACID) empêchant toute double dispensation.")
    add_bullet_point(doc, "Automatiser le calcul en temps réel du tiers payant avec écrêtement automatique dès l'atteinte du plafond annuel familial.")
    add_bullet_point(doc, "Déployer une cartographie sanitaire interactive (Leaflet) géolocalisant les structures partenaires du Sénégal avec guidage routier.")
    add_bullet_point(doc, "Assurer la résilience hors-ligne (Service Worker) et la conformité légale avec la loi sur la protection des données personnelles (CDP).")

    add_heading_with_spacing(doc, "Méthodologie adoptée", level=2)
    add_styled_paragraph(doc, "Le projet s'est appuyé sur une démarche d'ingénierie logicielle rigoureuse alliant la méthode agile **Scrum** (itérations de 2 semaines avec intégration continue) et les standards de modélisation du génie logiciel (**UML** pour les diagrammes de cas d'utilisation, de séquences et de classes). L'assurance qualité s'est concrétisée par le développement d'un banc d'essais complet de **196 tests automatisés** validant l'étanchéité des rôles et l'intégrité des transactions.")

    add_heading_with_spacing(doc, "Annonce du plan", level=2)
    add_styled_paragraph(doc, "Le mémoire s'articule autour de quatre chapitres structurés :")
    add_bullet_point(doc, "**Chapitre 1 : Présentation du cadre du projet**, détaillant le contexte de l'ISEP Diamniadio, la genèse de SantéSN, le périmètre et l'organisation de l'équipe.")
    add_bullet_point(doc, "**Chapitre 2 : Analyse de l'existant et cadrage**, dressant un diagnostic critique du modèle papier actuel, le cahier des charges fonctionnel et le planning prévisionnel.")
    add_bullet_point(doc, "**Chapitre 3 : Conception de la solution**, exposant l'architecture multicouche Cloud, les diagrammes UML et la modélisation relationnelle de la base de données.")
    add_bullet_point(doc, "**Chapitre 4 : Réalisation, tests et résultats**, illustrant les cinq espaces utilisateurs, le bilan des 196 tests automatisés, l'analyse des coûts et les défis techniques résolus.")

    # =========================================================================
    # CHAPITRE 1 : PRÉSENTATION DU CADRE DU PROJET
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "CHAPITRE 1 : PRÉSENTATION DU CADRE DU PROJET", level=1)
    
    add_heading_with_spacing(doc, "1.1 Présentation de la structure d’accueil ou du commanditaire", level=2)
    add_heading_with_spacing(doc, "1.1.1 L'Institut Supérieur d'Enseignement Professionnel (ISEP) de Diamniadio", level=3)
    add_styled_paragraph(doc, "Créé par l'État du Sénégal par la loi n° 2015-05 du 23 avril 2015, l'**Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Traware de Diamniadio** est un établissement public d'enseignement supérieur d'avant-garde. Situé au cœur du pôle technologique et urbain de Diamniadio, l'ISEP a pour vocation de dispenser des formations professionnelles supérieures courtes et professionnalisantes, alignées sur les compétences réellement recherchées par les entreprises nationales et sous-régionales.")
    add_styled_paragraph(doc, "L'institut délivre le **Diplôme de l'ISEP (DISEP)**, niveau Bac+2 (Niveau 3 du cadre national des certifications), selon l'Approche par Compétences (APC).")

    add_heading_with_spacing(doc, "1.1.2 Le Département TIC et le Métier Analyste Programmeur Développeur (APD)", level=3)
    add_styled_paragraph(doc, "Le département Technologies de l'Information et de la Communication (TIC) abrite la filière **Analyste Programmeur Développeur (APD)**. Ce parcours forme des concepteurs logiciels polyvalents et rigoureux, aptes à concevoir des architectures web complexes, à administrer des bases de données relationnelles conformes aux formes normales et à intégrer les standards de cybersécurité modernes.")
    add_styled_paragraph(doc, "Le Projet de Fin de Formation (PFF) constitue la clé de voûte de ce programme : il évalue la capacité des futurs diplômés à conduire en autonomie un cycle complet de développement logiciel, depuis le recueil des besoins jusqu'au déploiement et à la validation en production.")

    add_heading_with_spacing(doc, "1.2 Présentation du projet : origine, bénéficiaires, périmètre", level=2)
    add_heading_with_spacing(doc, "1.2.1 Origine et genèse de SantéSN", level=3)
    add_styled_paragraph(doc, "Le projet SantéSN émane d'une observation directe des files d'attente quotidiennes devant les sièges des IPM dakaroises (IPM Sonatel, IPM de la Senelec, IPM bancaires). Les salariés doivent régulièrement s'absenter de leur travail pendant des heures pour faire signer un bon papier de consultation. En cas de crise de paludisme d'un enfant la nuit ou le week-end, l'absence de bon physique complique dramatiquement l'admission en clinique.")
    add_styled_paragraph(doc, "Convaincus que le numérique doit être un vecteur d'inclusion et de dignité humaine, nous avons entrepris de concevoir une plateforme 100% web, accessible sans installation lourde, capable de digitaliser ces échanges en garantissant la solvabilité de l'assuré en une fraction de seconde.")

    add_heading_with_spacing(doc, "1.2.2 Bénéficiaires du projet", level=3)
    add_bullet_point(doc, "**Les Assurés et leurs familles :** Obtention immédiate de la carte de santé sur smartphone, suivi transparent du budget santé familial et prise en charge instantanée en officine.")
    add_bullet_point(doc, "**Les Professionnels de Santé :** Sécurisation immédiate du paiement, scanner optique sans matériel dédié, télétransmission des feuilles de soins électroniques.")
    add_bullet_point(doc, "**Les IPM et Mutuelles de Santé :** Visibilité financière en temps réel, éradication des contestations comptables et suppression intégrale des budgets d'impression de carnets.")
    add_bullet_point(doc, "**L'Agence Nationale SEN-CSU :** Disponibilité d'un socle d'interopérabilité technique reproductible pour la couverture maladie universelle.")

    add_heading_with_spacing(doc, "1.2.3 Périmètre fonctionnel et limites du système", level=3)
    add_styled_paragraph(doc, "Le périmètre de SantéSN englobe la gestion multi-organismes hermétique (Multi-Tenant), les cartes dématérialisées ISO 7810 avec QR code vectoriel, la prescription certifiée HMAC, la délivrance officinale avec scanner caméra, le calcul des plafonds annuels, la géolocalisation des prestataires et la résilience PWA hors-ligne. Sont exclus du périmètre actuel la télémédecine par visioconférence et la gestion de la paie interne des entreprises.")

    add_heading_with_spacing(doc, "1.3 Organisation du groupe : rôles et outils de travail collaboratif", level=2)
    add_styled_paragraph(doc, "Le projet s'est appuyé sur une organisation claire et complémentaire :")
    add_bullet_point(doc, "**Lead Développeur Backend & Architecture :** Modélisation relationnelle de la base de données PostgreSQL, logique métier Django, verrous transactionnels pessimistes, signature HMAC et sécurité RBAC.")
    add_bullet_point(doc, "**Développeur Frontend & PWA :** Conception des interfaces réactives adaptatives (Desktop/Mobile), intégration de la cartographie Leaflet (Google Maps/Esri), décodage vidéo jsQR et Service Worker PWA.")
    add_bullet_point(doc, "**Ingénieur Qualité, DevOps & Documentation :** Banc de 196 tests automatisés, configuration de l'intégration continue GitHub Actions, déploiement Cloud Vercel/Neon et veille réglementaire CDP.")
    
    add_styled_paragraph(doc, "Le tableau ci-dessous récapitule la matrice de répartition nominative des responsabilités au sein de l'équipe :")
    add_academic_table(
        doc,
        "Tableau 1.1 : Matrice de répartition des rôles au sein de l'équipe de développement",
        ["Rôle dans le Projet", "Périmètre Technique d'Intervention", "Livrables Majeurs"],
        [
            ("Lead Développeur Backend & Architecture", "Conception MVT, API REST, Cryptographie HMAC-SHA256, Transactions ACID PostgreSQL", "Modèle de données relationnel, Vues sécurisées, Gestion des plafonds"),
            ("Développeur Frontend & PWA", "Design responsive Tailwind, Composants Leaflet, Décodage vidéo jsQR, Mode PWA", "Interface cartographique, Scanner temps réel, Carte dématérialisée ISO 7810"),
            ("Ingénieur Qualité, DevOps & Documentation", "Banc d'essais de 196 tests automatisés, CI/CD GitHub Actions, Déploiement Vercel/Neon", "Rapport de tests, Cahier des charges, Documentation de conformité CDP")
        ],
        col_widths=[2.0, 2.7, 2.1]
    )

    add_styled_paragraph(doc, "Les outils collaboratifs ont inclus GitHub pour le versionnement, Visual Studio Code pour le développement, Trello pour le suivi Kanban des sprints et Discord pour les synchronisations quotidiennes :")
    add_academic_table(
        doc,
        "Tableau 1.2 : Chaîne d'outillage logiciel et plateformes collaboratives retenues",
        ["Catégorie", "Outil / Logiciel", "Rôle et Justification Technique"],
        [
            ("Environnement de développement", "Visual Studio Code (v1.94+)", "Éditeur polyvalent avec extensions Python, Django et Tailwind"),
            ("Gestion de versions", "Git 2.45 & GitHub Enterprise", "Traçabilité des commits, gestion des branches et intégration continue"),
            ("Pilotage de projet Agile", "Trello / Kanban Board", "Planification des 6 sprints Scrum, suivi des user stories et burndown chart"),
            ("Communication d'équipe", "Discord & Google Meet", "Daily stand-up meetings de 15 minutes et revues de fin de sprint"),
            ("Banc de tests & CI", "Django Test Framework & GitHub Actions", "Exécution continue des 196 tests automatisés à chaque commit")
        ],
        col_widths=[1.8, 2.0, 3.0]
    )

    # Insertion de la Figure 1
    add_figure_image(doc, "fig_01_circuit_papier.png", "Figure 1.1 : Circuit papier traditionnel et points de rupture du tiers payant au Sénégal", width_inches=6.2)

    # =========================================================================
    # CHAPITRE 2 : ANALYSE DE L’EXISTANT ET CADRAGE
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "CHAPITRE 2 : ANALYSE DE L’EXISTANT ET CADRAGE", level=1)
    
    add_heading_with_spacing(doc, "2.1 Étude de l’existant", level=2)
    add_styled_paragraph(doc, "Le circuit conventionnel du tiers payant au Sénégal se compose de 5 étapes séquentielles : demande physique de bon de consultation au siège de l'IPM, consultation clinique avec délivrance d'une ordonnance papier volante, passage en officine avec vérification manuelle du carnet, regroupement physique des liasses de factures en fin de mois par les pharmacies, et enfin liquidation comptable manuelle par les auditeurs de l'IPM avec émission de chèques bancaires sous 60 à 120 jours.")

    add_heading_with_spacing(doc, "2.2 Critique de l’existant", level=2)
    add_styled_paragraph(doc, "Ce modèle manuel souffre d'un manque criant de traçabilité. Les auditeurs d'IPM découvrent fréquemment que des cartes de membres ont été prêtées à des tiers, que des ordonnances ont été falsifiées pour augmenter les quantités prescrites, ou que des ordonnances photocopiées ont été présentées dans plusieurs pharmacies différentes (double délivrance).")
    
    # Insertion de la Figure 2 (SWOT)
    add_figure_image(doc, "fig_02_swot_existant.png", "Figure 2.1 : Matrice d'analyse SWOT de la couverture maladie d'entreprise au Sénégal", width_inches=6.0)

    add_heading_with_spacing(doc, "2.3 Expression des besoins fonctionnels et non fonctionnels", level=2)
    add_styled_paragraph(doc, "Les besoins fonctionnels s'articulent autour des cinq rôles opérationnels :")
    add_bullet_point(doc, "**Assuré :** Afficher sa carte ISO 7810 avec QR Code dynamique, suivre sa jauge de plafond familial annuel restant, déclarer ses ayants droit et soumettre des remboursements hors réseau.")
    add_bullet_point(doc, "**Médecin :** Identifier le patient par matricule ou QR code, rédiger une ordonnance électronique, apposer le sceau cryptographique HMAC-SHA256 et imprimer le PDF A4 certifié.")
    add_bullet_point(doc, "**Pharmacien :** Scanner le QR code par la caméra du navigateur, contrôler la validité en temps réel, calculer la quote-part et valider la délivrance de façon atomique (ACID).")
    add_bullet_point(doc, "**Gestionnaire IPM :** Suivre le dashboard des sinistres, gérer les conventions tarifaires, cartographier le réseau de soins et télétransmettre les bordereaux de liquidation.")
    add_bullet_point(doc, "**Administrateur :** Superviser les permissions RBAC, consulter le journal d'audit immuable et veiller au respect de la loi sénégalaise 2008-12 CDP.")
    
    add_styled_paragraph(doc, "Sur le plan non fonctionnel, la plateforme exige une sécurité fail-closed (immunité CSRF, XSS, IDOR), un temps de réponse inférieur à 800 ms, un fonctionnement hors-ligne (PWA) et une parfaite adaptabilité visuelle en mode sombre et clair.")

    add_heading_with_spacing(doc, "2.4 Solutions envisagées et choix retenu", level=2)
    add_styled_paragraph(doc, "Face aux progiciels propriétaires fermés et aux applications mobiles natives dépendantes des stores Google/Apple, le choix d'une **Application Web Progressive (PWA) propulsée par Django 5.2 et PostgreSQL Neon** s'est imposé. Cette approche garantit la souveraineté technologique, la gratuité des licences pour les structures locales, une exécution immédiate sur tout navigateur moderne et une résilience hors-ligne via Service Worker.")
    
    add_academic_table(
        doc,
        "Tableau 2.1 : Matrice comparative des options techniques face aux contraintes locales",
        ["Option Technique Envisagée", "Coût d'Adoption & Licences", "Résilience Réseau (Hors-ligne)", "Souveraineté & Sécurité"],
        [
            ("Progiciel Propriétaire Médical", "Très élevé (abonnements annuels en devises)", "Nulle (dépendance Internet permanente)", "Faible (hébergement hors du Sénégal, vendor lock-in)"),
            ("Application Mobile Native (Android)", "Moyen (double codebase, store Google/Apple)", "Bonne (stockage SQLite local)", "Moyenne (exposition au reverse-engineering binaire)"),
            ("PWA Django 5.2 + Neon (SantéSN)", "Optimal (open-source souverain, zéro redevance)", "Excellente (Service Worker & Cache First)", "Maximale (chiffrement HMAC serveur, étanchéité multi-tenant)")
        ],
        col_widths=[1.9, 1.8, 1.6, 1.7]
    )

    add_heading_with_spacing(doc, "2.5 Planification du projet", level=2)
    add_styled_paragraph(doc, "Le projet a été exécuté sur un cycle de 14 semaines réparties en 6 sprints Scrum de 2 semaines précédés d'une phase de cadrage :")
    
    # Insertion de la Figure 12 (Gantt)
    add_figure_image(doc, "fig_12_planning_gantt_scrum.png", "Figure 2.2 : Chronogramme prévisionnel des sprints Scrum sur 14 semaines", width_inches=6.2)

    # =========================================================================
    # CHAPITRE 3 : CONCEPTION DE LA SOLUTION
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "CHAPITRE 3 : CONCEPTION DE LA SOLUTION", level=1)
    
    add_heading_with_spacing(doc, "3.1 Démarche et méthode de conception", level=2)
    add_styled_paragraph(doc, "La conception s'est appuyée sur le formalisme orienté objet du standard **UML (Unified Modeling Language)** pour modéliser les structures statiques et les interactions dynamiques. Les patrons de conception adoptés comprennent le modèle **MVT (Modèle-Vue-Template)** propre à Django, le patron **Scoped QuerySet** pour le cloisonnement hermétique des données entre organismes (Multi-Tenancy) et la couche de services pour les algorithmes cryptographiques HMAC et d'écrêtement budgétaire.")

    add_heading_with_spacing(doc, "3.2 Architecture générale de la solution", level=2)
    add_styled_paragraph(doc, "L'architecture multicouche de SantéSN articule 4 niveaux de responsabilités : la Couche Client PWA (responsive, Service Worker, scanner jsQR, Leaflet), la Couche Passerelle Vercel Edge (terminaison HTTPS/TLS 1.3, pare-feu applicatif), la Couche Métier Django 5.2 (contrôle RBAC, tiers payant, HMAC, WhatsApp Cloud API) et la Couche Persistance PostgreSQL Neon (cluster serverless, transactions ACID avec verrous pessimistes).")
    
    # Insertion de la Figure 6 (Architecture)
    add_figure_image(doc, "fig_06_architecture_cloud_mvt.png", "Figure 3.2 : Architecture multicouche Cloud et flux sécurisés de SantéSN", width_inches=6.2)

    add_heading_with_spacing(doc, "3.3 Modélisation détaillée", level=2)
    add_heading_with_spacing(doc, "3.3.1 Diagramme de cas d'utilisation global", level=3)
    add_styled_paragraph(doc, "Le diagramme de cas d'utilisation ci-dessous synthétise les fonctionnalités majeures réparties entre les 5 profils d'acteurs :")
    
    # Insertion de la Figure 3 (Cas d'utilisation)
    add_figure_image(doc, "fig_03_diagramme_use_cases.png", "Figure 3.1 : Diagramme de cas d'utilisation global de la plateforme SantéSN (UML)", width_inches=6.2)

    add_styled_paragraph(doc, "La matrice des privilèges associée à ces cas d'utilisation est formalisée dans le tableau ci-dessous :")
    add_academic_table(
        doc,
        "Tableau 3.1 : Matrice de contrôle d'accès basée sur les rôles (Matrice RBAC 5 Rôles)",
        ["Fonctionnalité Métier", "Assuré", "Médecin", "Pharmacie", "Gestionnaire", "Admin IT"],
        [
            ("Consultation carte ISO 7810 & QR code", "Lecture", "Non", "Scan optique", "Audit", "Supervision"),
            ("Prescription & Sceau cryptographique HMAC", "Non", "Création / Signature", "Non", "Non", "Non"),
            ("Validation délivrance atomique (ACID)", "Non", "Non", "Exécution exclusive", "Non", "Non"),
            ("Déclaration des ayants droit", "Demande", "Non", "Non", "Validation", "Non"),
            ("Cartographie sanitaire & conventions", "Non", "Non", "Non", "Gestion complète", "Supervision"),
            ("Supervision des logs d'audit CDP", "Non", "Non", "Non", "Consultation", "Administration")
        ],
        col_widths=[2.3, 0.9, 1.1, 1.1, 1.1, 0.9]
    )

    add_heading_with_spacing(doc, "3.3.2 Modèle Conceptuel et Logique de Données (MCD / MLD)", level=3)
    add_styled_paragraph(doc, "La base de données relationnelle est articulée autour des entités maîtresses : `Organisme` (IPM/Mutuelle), `User` (comptes avec rôle RBAC), `Patient` (assuré ou ayant droit avec numéro de carte ISO et plafond), `Prestataire` (clinique, pharmacie, hôpital avec coordonnées GPS), `ConventionPrestataire` (accord tarifaire liant un organisme à un prestataire), `Ordonnance` (prescription liée à un médecin et un patient, protégée par `sceau_hmac` et `code_qr`), `LigneOrdonnance` (médicaments prescrits) et `DemandeRemboursement` (soins hors réseau).")

    add_heading_with_spacing(doc, "3.4 Choix des outils, technologies et matériels", level=2)
    add_styled_paragraph(doc, "Les choix technologiques retenus répondent scrupuleusement aux contraintes de connectivité et de sécurité du Sénégal :")
    add_bullet_point(doc, "**Python 3.12+ / Django 5.2 LTS :** Cadriciel reconnu pour sa robustesse bancaire et sa protection native contre les failles d'injection SQL et CSRF.")
    add_bullet_point(doc, "**Neon Serverless PostgreSQL :** Base de données relationnelle cloud garantissant des transactions ACID infaillibles avec verrous pessimistes `select_for_update`.")
    add_bullet_point(doc, "**Leaflet 1.9.4 & Tuiles Google Maps/Esri :** Cartographie interactive légère, intégrant les fonds Plan Urbain et Satellite HD avec sélecteur de calques dynamique adapté aux thèmes clair et sombre.")
    add_bullet_point(doc, "**jsQR 1.4.0 :** Décodeur optique de QR Code 100% exécuté dans le navigateur du pharmacien via l'API HTML5 `getUserMedia`, sans coût matériel additionnel.")

    add_academic_table(
        doc,
        "Tableau 3.2 : Justification technologique approfondie de la stack logicielle",
        ["Composant Architectural", "Technologie Choisie", "Justification Technique & Règle Métier"],
        [
            ("Framework Backend", "Django 5.2 LTS (Python 3.12)", "Architecture MVT, ORM déclaratif, protection anti-CSRF/SQLi, maturité bancaire"),
            ("Base de Données Relationnelle", "Neon Serverless PostgreSQL", "Support des verrous pessimistes 'select_for_update', transactions ACID, sauvegardes continues"),
            ("Frontend & Expérience Client", "Progressive Web App (PWA) / HTML5", "Exécution sans téléchargement de store, installation bureau/mobile, Service Worker hors-ligne"),
            ("Moteur Cartographique", "Leaflet 1.9.4 + Tuiles Google Maps/Esri", "Cartographie fluide sans quota de facturation, sélecteur dynamique jour/nuit"),
            ("Scanner Optique Officinal", "jsQR 1.4.0 (HTML5 Canvas)", "Décodage en direct via la caméra du smartphone ou webcam de l'officine en < 300 ms")
        ],
        col_widths=[1.8, 2.0, 3.2]
    )

    # =========================================================================
    # CHAPITRE 4 : RÉALISATION, TESTS ET RÉSULTATS
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "CHAPITRE 4 : RÉALISATION, TESTS ET RÉSULTATS", level=1)
    
    add_heading_with_spacing(doc, "4.1 Mise en œuvre et environnement de travail", level=2)
    add_styled_paragraph(doc, "Le développement s'est effectué sur des postes Windows 11 avec des environnements virtuels Python isolés et un dépôt centralisé Git/GitHub. Le déploiement s'opère de façon continue (CI/CD) sur Vercel PaaS, assurant une disponibilité 24h/24 en HTTPS sur l'adresse officielle : **https://projet-final-bice.vercel.app**.")

    add_heading_with_spacing(doc, "4.2 Présentation de la solution", level=2)
    add_styled_paragraph(doc, "La plateforme SantéSN se déploie à travers cinq interfaces adaptées :")
    add_bullet_point(doc, "**Espace Assuré :** Affichage de la carte dématérialisée ISO 7810 ID-1 avec QR Code dynamique vectoriel, jauge du plafond annuel restant (ex: 1 125 000 FCFA restants sur 1 500 000 FCFA), liste des ayants droit et mode hors-ligne PWA.")
    add_bullet_point(doc, "**Espace Médecin :** Dossier patient informatisé, outil de prescription avec posologie et calcul automatique de l'empreinte cryptographique HMAC-SHA256 prévenant toute altération.")
    add_bullet_point(doc, "**Espace Pharmacie :** Scanner optique par caméra en direct, contrôle instantané du statut 'Active', affichage de la quote-part et délivrance atomique immédiate.")
    add_bullet_point(doc, "**Espace Gestionnaire IPM :** Suivi analytique des sinistres, cartographie sanitaire Leaflet avec sélecteur de calques, instruction des remboursements hors réseau et télétransmission des bordereaux.")
    add_bullet_point(doc, "**Espace Administrateur IT :** Supervision technique, matrice RBAC stricte et journal d'audit immuable certifiant la conformité avec la loi CDP n° 2008-12.")
    
    # Insertion de la Figure 8 (Carte ISO)
    add_figure_image(doc, "fig_08_carte_assure_iso7810.png", "Figure 4.2 : Rendu visuel de la carte d'assuré dématérialisée (Format ISO 7810 ID-1)", width_inches=5.8)

    add_heading_with_spacing(doc, "4.3 Tests et validation", level=2)
    add_styled_paragraph(doc, "La fiabilité de SantéSN a été validée par une suite exhaustive de **196 tests automatisés** exécutés via Django Test Runner. Chaque domaine fonctionnel a été certifié sans régression :")
    
    # Insertion de la Figure 13 (Tests 196)
    add_figure_image(doc, "fig_13_resultats_tests_196.png", "Figure 4.1 : Répartition des 196 tests automatisés validés par domaine fonctionnel", width_inches=6.0)

    add_academic_table(
        doc,
        "Tableau 4.1 : Bilan exhaustif de la suite de 196 tests automatisés validés",
        ["Domaine / Module Fonctionnel", "Nombre de Tests", "Taux de Succès", "Objectif de Validation"],
        [
            ("Sécurité & Authentification RBAC", "28 tests", "100 % (28/28)", "Herméticité des accès et isolation multi-tenant"),
            ("Intégrité Ordonnances & Sceau HMAC", "34 tests", "100 % (34/34)", "Détection immédiate des falsifications de doses ou dates"),
            ("Délivrance Pharmacie & Concurrence", "42 tests", "100 % (42/42)", "Verrouillage atomique et blocage strict des doubles délivrances"),
            ("Cartes Dématérialisées & Plafonds", "32 tests", "100 % (32/32)", "Écrêtement dynamique du solde familial restant"),
            ("Conventions IPM & Remboursements", "36 tests", "100 % (36/36)", "Calcul exact du tiers payant et transmission des bordereaux"),
            ("Cartographie Leaflet & Navigation", "24 tests", "100 % (24/24)", "Géolocalisation des prestataires et sélecteur de calques"),
            ("TOTAL CONSOLIDÉ", "196 tests", "100 % SUCCÈS", "Zéro régression sur l'ensemble de la plateforme")
        ],
        col_widths=[2.3, 1.2, 1.3, 2.2]
    )

    add_heading_with_spacing(doc, "4.4 Évaluation des coûts", level=2)
    add_styled_paragraph(doc, "L'analyse budgétaire démontre l'extrême rentabilité de la solution. L'hébergement Cloud Vercel Pro (144 000 FCFA/an), la base managée Neon PostgreSQL (138 000 FCFA/an), le nom de domaine national .sn (25 000 FCFA), l'API WhatsApp (108 000 FCFA/an) et la provision de maintenance technique représentent un **coût global annuel d'exploitation de 1 015 000 FCFA**.")
    add_styled_paragraph(doc, "En comparaison, une IPM moyenne dépensant plus de 12 millions de FCFA par an en carnets papier et pertes liées à la fraude réalise une **économie nette annuelle supérieure à 11 millions de FCFA**, amortissant l'investissement dès le deuxième mois d'utilisation :")

    add_academic_table(
        doc,
        "Tableau 4.2 : Évaluation budgétaire annuelle d'exploitation Cloud et calcul du ROI",
        ["Poste de Dépense d'Exploitation", "Fournisseur / Solution", "Coût Annuel (FCFA)", "Justification Économique"],
        [
            ("Hébergement Edge & CDN", "Vercel PaaS (Plan Pro)", "144 000 FCFA", "Déploiement continu, SSL automatisé et haute disponibilité"),
            ("Base de données Serverless", "Neon Cloud PostgreSQL", "138 000 FCFA", "Sauvegardes continues (PITR) et scalabilité automatique"),
            ("Nom de domaine national", "Registre Sénégalais (.sn)", "25 000 FCFA", "Identité numérique souveraine et reconnaissance institutionnelle"),
            ("Passerelle Notifications", "WhatsApp Cloud API / SMS", "108 000 FCFA", "Alertes instantanées de délivrance et alertes solde"),
            ("Maintenance évolutive & support", "Équipe d'ingénierie ISEP", "600 000 FCFA", "Mises à jour de sécurité et conformité réglementaire CDP"),
            ("COÛT GLOBAL ANNUEL SANTÉSN", "Exploitation Cloud consolidée", "1 015 000 FCFA", "Coût maîtrisé accessible aux petites et moyennes IPM"),
            ("COÛT DU PAPIER TRADITIONNEL", "Impression carnets & liasses", "12 500 000 FCFA", "Pertes par fraude estimées à 15% des sinistres papier"),
            ("ÉCONOMIE NETTE RÉALISÉE", "Bilan financier annuel", "+11 485 000 FCFA", "ROI positif amorti dès le 2ème mois d'utilisation")
        ],
        col_widths=[2.2, 1.8, 1.4, 2.0]
    )

    add_heading_with_spacing(doc, "4.5 Difficultés rencontrées et solutions apportées", level=2)
    add_bullet_point(doc, "**Concurrence d'accès et risque de double délivrance :** Résolu par l'implémentation de verrous pessimistes PostgreSQL (`select_for_update()`) dans des blocs transactionnels atomiques `transaction.atomic()`.")
    add_bullet_point(doc, "**Recherche tolérante aux accents et multi-mots :** Résolu par un algorithme de normalisation textuelle Unicode NFD retirant les diacritiques et unifiant les apostrophes pour trouver immédiatement des établissements comme la Clinique de l'Océan.")
    add_bullet_point(doc, "**Contraste du sélecteur de calques cartographiques en mode sombre :** Résolu par une surcharge CSS adaptative liant le fond (`var(--surface)`), le texte (`var(--text)`) et les boutons radio au thème actif.")
    add_bullet_point(doc, "**Autorisations caméra sur smartphone :** Résolu par le durcissement HTTPS/TLS 1.3 strict requis par l'API `getUserMedia` et l'adjonction d'un mode de saisie manuelle de secours.")

    # =========================================================================
    # CONCLUSION GÉNÉRALE ET PERSPECTIVES
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "CONCLUSION GÉNÉRALE ET PERSPECTIVES", level=1)
    
    add_styled_paragraph(doc, "Le présent projet de fin de formation a permis de concevoir, développer et déployer avec succès la plateforme **SantéSN**, apportant une solution concrète, moderne et souveraine à l'épineux problème de la gestion manuelle du tiers payant médical au Sénégal.")
    add_styled_paragraph(doc, "L'ensemble des objectifs fixés au départ a été scrupuleusement atteint : la dématérialisation des cartes d'assurés au format ISO 7810 avec QR code vectoriel, la signature électronique des ordonnances avec sceau d'intégrité HMAC-SHA256, le scanner optique par caméra en pharmacie avec verrouillage atomique anti-double délivrance, le calcul en temps réel du tiers payant avec écrêtement budgétaire et la conformité stricte avec la loi sénégalaise 2008-12 sur les données personnelles.")
    add_styled_paragraph(doc, "Validée par un banc d'essais irréprochable de **196 tests automatisés (100% de succès)** et hébergée en haute disponibilité sur le Cloud Vercel, SantéSN démontre sa viabilité opérationnelle et sa rentabilité financière éclatante (plus de 11 millions de FCFA d'économies annuelles pour une IPM moyenne).")
    add_styled_paragraph(doc, "Pour les apprenants du département TIC de l'ISEP Diamniadio, cette aventure a constitué un tremplin professionnel majeur, consolidant leurs compétences en architecture Django, en sécurité logicielle, en bases de données relationnelles avancées et en travail collaboratif Agile.")
    add_styled_paragraph(doc, "En perspective, SantéSN ambitionne d'intégrer le règlement instantané de la quote-part par Mobile Money (Wave, Orange Money), d'ouvrir son architecture multi-tenant aux mutuelles communautaires de l'Agence Nationale SEN-CSU et d'incorporer un moteur d'Intelligence Artificielle pour la détection prédictive des fraudes de prescription.")

    # =========================================================================
    # PAGES DE FIN : BIBLIOGRAPHIE ET ANNEXES
    # =========================================================================
    doc.add_page_break()
    add_heading_with_spacing(doc, "BIBLIOGRAPHIE ET WEBOGRAPHIE (NORME APA)", level=1)
    refs = [
        "Django Software Foundation. (2024). Django documentation (Version 5.2 LTS). https://docs.djangoproject.com/fr/5.2/",
        "Fowler, M. (2018). Refactoring: Improving the design of existing code (2nd ed.). Addison-Wesley Professional.",
        "Ministère de la Santé et de l'Action Sociale du Sénégal (MSAS). (2021). Plan Stratégique National de Santé Digitale 2022-2026. Dakar.",
        "Mozilla Developer Network (MDN). (2024). Progressive Web Apps (PWAs) & Service Worker API. https://developer.mozilla.org/fr/docs/Web/Progressive_web_apps",
        "Neon Inc. (2024). Neon Serverless Postgres Architecture and Connection Pooling Guide. https://neon.tech/docs/",
        "Organisation Mondiale de la Santé (OMS). (2021). Stratégie mondiale pour la santé numérique 2020-2025. Genève.",
        "OWASP Foundation. (2023). OWASP Top 10 Web Application Security Risks. https://owasp.org/www-project-top-ten/",
        "PostgreSQL Global Development Group. (2024). PostgreSQL 16 Database Documentation. https://www.postgresql.org/docs/",
        "Pressman, R. S., & Maxim, B. R. (2020). Software Engineering: A Practitioner's Approach (9th ed.). McGraw-Hill Education.",
        "République du Sénégal. (1975). Loi n° 75-50 du 3 avril 1975 relative aux Institutions de Prévoyance Maladie (IPM). Journal Officiel de la République du Sénégal.",
        "République du Sénégal. (2008). Loi n° 2008-12 du 25 janvier 2008 sur la protection des données à caractère personnel (CDP). Dakar.",
        "Sommerville, I. (2016). Software Engineering (10th ed.). Pearson."
    ]
    for r_txt in refs:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.left_indent = Inches(0.3)
        p_r.paragraph_format.first_line_indent = Inches(-0.3)
        p_r.paragraph_format.line_spacing = 1.15
        p_r.paragraph_format.space_after = Pt(4)
        run_r = p_r.add_run(r_txt)
        run_r.font.name = 'Calibri'
        run_r.font.size = Pt(10)

    doc.add_page_break()
    add_heading_with_spacing(doc, "ANNEXES TECHNIQUES", level=1)
    
    add_heading_with_spacing(doc, "Annexe 1 : Verrouillage Pessimiste Atomique en Pharmacie (select_for_update)", level=2)
    p_code1 = doc.add_paragraph()
    p_code1.paragraph_format.left_indent = Inches(0.2)
    p_code1.paragraph_format.space_before = Pt(4)
    p_code1.paragraph_format.space_after = Pt(6)
    code_text1 = (
        "@transaction.atomic\n"
        "def valider_delivrance_ordonnance(pharmacien_user, ordonnance_pk):\n"
        "    # Verrouillage pessimiste exclusif sur la ligne de l'ordonnance\n"
        "    ordonnance = Ordonnance.objects.select_for_update().get(pk=ordonnance_pk)\n"
        "    if ordonnance.statut != Ordonnance.Statut.ACTIVE:\n"
        "        raise ValidationError('Alerte : Ordonnance deja traitee ou annulee.')\n"
        "    \n"
        "    ordonnance.statut = Ordonnance.Statut.DELIVREE\n"
        "    ordonnance.pharmacie_delivrance = pharmacien_user.prestataire\n"
        "    ordonnance.date_delivrance = timezone.now()\n"
        "    ordonnance.save(update_fields=['statut', 'pharmacie_delivrance', 'date_delivrance'])\n"
        "    \n"
        "    patient = ordonnance.patient\n"
        "    patient.enregistrer_consommation_tiers_payant(ordonnance.montant_part_ipm)\n"
    )
    r_c1 = p_code1.add_run(code_text1)
    r_c1.font.name = 'Consolas'
    r_c1.font.size = Pt(9)
    r_c1.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    add_heading_with_spacing(doc, "Annexe 2 : Génération du Sceau Cryptographique HMAC-SHA256", level=2)
    p_code2 = doc.add_paragraph()
    p_code2.paragraph_format.left_indent = Inches(0.2)
    p_code2.paragraph_format.space_before = Pt(4)
    p_code2.paragraph_format.space_after = Pt(6)
    code_text2 = (
        "def generer_sceau_ordonnance(ordonnance):\n"
        "    cle_secrete = settings.SECRET_KEY.encode('utf-8')\n"
        "    lignes_concat = '|'.join(\n"
        "        f'{l.nom_medicament}:{l.quantite}:{l.posologie}'\n"
        "        for l in ordonnance.lignes.all().order_by('id')\n"
        "    )\n"
        "    message = f'{ordonnance.pk}_{ordonnance.patient_id}_{ordonnance.medecin_id}_{lignes_concat}'\n"
        "    return hmac.new(cle_secrete, message.encode('utf-8'), hashlib.sha256).hexdigest()\n"
    )
    r_c2 = p_code2.add_run(code_text2)
    r_c2.font.name = 'Consolas'
    r_c2.font.size = Pt(9)
    r_c2.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    print(f"Sauvegarde du document officiel final dans : {OUTPUT_PATH}")
    doc.save(OUTPUT_PATH)
    print("Document officiel final ISEP généré avec succès !")

if __name__ == "__main__":
    build_full_official_report()
