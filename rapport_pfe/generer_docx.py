import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

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

def create_report():
    doc = Document()

    # 1. Page setup - Standard A4 (21 x 29.7 cm), Marges 2.5 cm
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.different_first_page_header_footer = True

    # 2. Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11.5)
    normal_style.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # Couleurs du thème SantéSN & ISEP
    PRIMARY_COLOR = RGBColor(0x0E, 0x7C, 0x86)    # Teal médical SantéSN
    SECONDARY_COLOR = RGBColor(0x6A, 0x3E, 0x1E)  # Brun chaud ISEP
    DARK_TEXT = RGBColor(0x11, 0x18, 0x27)

    base_dir = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe"
    files = [
        "00_PAGES_PRELIMINAIRES.md",
        "01_INTRODUCTION_GENERALE.md",
        "02_CHAPITRE_1_CADRE_DU_PROJET.md",
        "03_CHAPITRE_2_ANALYSE_ET_CADRAGE.md",
        "04_CHAPITRE_3_CONCEPTION_DE_LA_SOLUTION.md",
        "05_CHAPITRE_4_REALISATION_TESTS_RESULTATS.md",
        "06_CONCLUSION_ET_PERSPECTIVES.md",
        "07_PAGES_DE_FIN_ET_ANNEXES.md"
    ]

    for f_idx, fname in enumerate(files):
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if f_idx > 0:
            doc.add_page_break()

        in_code_block = False
        code_lines = []
        in_table = False
        table_lines = []

        i = 0
        while i < len(lines):
            line = lines[i].rstrip("\r\n")

            # Gestion des blocs de code
            if line.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    # Écrire le bloc de code sous forme de paragraphe encadré
                    p_code = doc.add_paragraph()
                    p_code.paragraph_format.left_indent = Inches(0.2)
                    p_code.paragraph_format.right_indent = Inches(0.2)
                    p_code.paragraph_format.space_before = Pt(4)
                    p_code.paragraph_format.space_after = Pt(6)
                    run_code = p_code.add_run("\n".join(code_lines))
                    run_code.font.name = 'Consolas'
                    run_code.font.size = Pt(9.5)
                    run_code.font.color.rgb = RGBColor(0x27, 0x27, 0x2A)
                    code_lines = []
                else:
                    in_code_block = True
                    code_lines = []
                i += 1
                continue

            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # Gestion des tableaux Markdown
            if "|" in line and not line.strip().startswith(">"):
                table_lines.append(line)
                # Vérifier si la ligne suivante est encore du tableau
                if i + 1 < len(lines) and "|" in lines[i+1]:
                    i += 1
                    continue
                else:
                    # Traiter et générer le tableau
                    rows_data = []
                    for t_line in table_lines:
                        # Ignorer les lignes de séparation |---|---|
                        if re.match(r"^\s*\|?\s*:?-+:?\s*\|", t_line):
                            continue
                        cells = [c.strip() for c in t_line.split("|")]
                        if len(cells) >= 2:
                            if cells[0] == "": cells = cells[1:]
                            if len(cells) > 0 and cells[-1] == "": cells = cells[:-1]
                            if cells:
                                rows_data.append(cells)

                    if rows_data:
                        num_cols = max(len(r) for r in rows_data)
                        t_word = doc.add_table(rows=len(rows_data), cols=num_cols)
                        t_word.alignment = WD_TABLE_ALIGNMENT.CENTER
                        for r_idx, r_data in enumerate(rows_data):
                            row = t_word.rows[r_idx]
                            is_header = (r_idx == 0)
                            for c_idx in range(num_cols):
                                cell = row.cells[c_idx]
                                val = r_data[c_idx] if c_idx < len(r_data) else ""
                                # Nettoyer le format markdown brut (**texte**)
                                val_clean = re.sub(r"\*\*(.*?)\*\*", r"\1", val)
                                cell.text = val_clean
                                p_c = cell.paragraphs[0]
                                p_c.paragraph_format.space_before = Pt(3)
                                p_c.paragraph_format.space_after = Pt(3)
                                set_cell_margins(cell, top=120, bottom=120, left=160, right=160)

                                if is_header:
                                    set_cell_background(cell, "0E7C86")
                                    for r_c in p_c.runs:
                                        r_c.font.bold = True
                                        r_c.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                                        r_c.font.size = Pt(10)
                                else:
                                    bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
                                    set_cell_background(cell, bg_color)
                                    for r_c in p_c.runs:
                                        r_c.font.size = Pt(9.5)

                    table_lines = []
                    i += 1
                    continue

            # Titres
            if line.startswith("# "):
                h = doc.add_paragraph()
                h.paragraph_format.space_before = Pt(14)
                h.paragraph_format.space_after = Pt(8)
                h.paragraph_format.keep_with_next = True
                run = h.add_run(line[2:].strip())
                run.font.name = 'Calibri'
                run.font.size = Pt(19)
                run.font.bold = True
                run.font.color.rgb = PRIMARY_COLOR

            elif line.startswith("## "):
                h = doc.add_paragraph()
                h.paragraph_format.space_before = Pt(12)
                h.paragraph_format.space_after = Pt(6)
                h.paragraph_format.keep_with_next = True
                run = h.add_run(line[3:].strip())
                run.font.name = 'Calibri'
                run.font.size = Pt(15)
                run.font.bold = True
                run.font.color.rgb = SECONDARY_COLOR

            elif line.startswith("### "):
                h = doc.add_paragraph()
                h.paragraph_format.space_before = Pt(10)
                h.paragraph_format.space_after = Pt(4)
                h.paragraph_format.keep_with_next = True
                run = h.add_run(line[4:].strip())
                run.font.name = 'Calibri'
                run.font.size = Pt(12.5)
                run.font.bold = True
                run.font.color.rgb = DARK_TEXT

            elif line.startswith("#### "):
                h = doc.add_paragraph()
                h.paragraph_format.space_before = Pt(6)
                h.paragraph_format.space_after = Pt(2)
                h.paragraph_format.keep_with_next = True
                run = h.add_run(line[5:].strip())
                run.font.name = 'Calibri'
                run.font.size = Pt(11.5)
                run.font.bold = True
                run.font.italic = True
                run.font.color.rgb = DARK_TEXT

            elif line.startswith("> "):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.4)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                run = p.add_run(line[2:].strip().replace("*", ""))
                run.font.italic = True
                run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

            elif line.strip().startswith("* ") or line.strip().startswith("- "):
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(2)
                text_clean = line.strip()[2:]
                parts = re.split(r"(\*\*.*?\*\*)", text_clean)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        r = p.add_run(part[2:-2])
                        r.bold = True
                    else:
                        p.add_run(part)

            elif line.strip() == "---":
                # Ligne séparatrice
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(6)
                r = p.add_run("_______________________________________________________________________________")
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)

            elif line.strip():
                p = doc.add_paragraph()
                text_clean = line.strip()
                parts = re.split(r"(\*\*.*?\*\*)", text_clean)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        r = p.add_run(part[2:-2])
                        r.bold = True
                    else:
                        p.add_run(part)

            i += 1

    output_path = os.path.join(base_dir, "SanteSN_Rapport_PFE_ISEP_Diamniadio.docx")
    doc.save(output_path)
    print(f"Rapport PFE Word généré avec succès : {output_path}")

if __name__ == "__main__":
    create_report()
