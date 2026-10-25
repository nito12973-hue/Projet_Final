import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

OUTPUT_DIR = r"c:\Users\nito1\Desktop\Projet_Final\rapport_pfe"
ILLUST_DIR = os.path.join(OUTPUT_DIR, "illustrations_isep")
OUTPUT_DOCX = os.path.join(OUTPUT_DIR, "RAPPORT_PFE_OFFICIEL_ISEP_DIAMNIADIO.docx")

def build_full_isep_thesis():
    doc = Document()
    
    # Configuration des marges A4 (2.5 cm partout)
    for section in doc.sections:
        section.top_margin = Inches(0.98)
        section.bottom_margin = Inches(0.98)
        section.left_margin = Inches(0.98)
        section.right_margin = Inches(0.98)
        
        # En-tête sobre identique au modèle PDF
        header = section.header
        p_head = header.paragraphs[0]
        p_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_head = p_head.add_run("Plateforme web et mobile de tiers payant médical : SantéSN")
        r_head.font.name = "Calibri"
        r_head.font.size = Pt(8.5)
        r_head.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        
        # Pied de page sobre identique au modèle PDF
        footer = section.footer
        p_foot = footer.paragraphs[0]
        p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_foot = p_foot.add_run("Année Académique 2024/2025")
        r_foot.font.name = "Calibri"
        r_foot.font.size = Pt(8.5)
        r_foot.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    def p(text="", before=0, after=6, spacing=1.15, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size=11, color=(0,0,0)):
        par = doc.add_paragraph()
        par.paragraph_format.space_before = Pt(before)
        par.paragraph_format.space_after = Pt(after)
        par.paragraph_format.line_spacing = spacing
        par.paragraph_format.alignment = align
        if text:
            parts = re.split(r"(\*\*.*?\*\*)", text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = par.add_run(part[2:-2])
                    r.font.name = "Calibri"
                    r.font.size = Pt(size)
                    r.font.bold = True
                    r.font.italic = italic
                    r.font.color.rgb = RGBColor(*color)
                else:
                    r = par.add_run(part)
                    r.font.name = "Calibri"
                    r.font.size = Pt(size)
                    r.font.bold = bold
                    r.font.italic = italic
                    r.font.color.rgb = RGBColor(*color)
        return par

    def bullet(text):
        par = doc.add_paragraph()
        par.paragraph_format.left_indent = Inches(0.25)
        par.paragraph_format.space_after = Pt(4)
        par.paragraph_format.line_spacing = 1.15
        r_b = par.add_run("●  ")
        r_b.font.name = "Calibri"
        r_b.font.size = Pt(10)
        
        parts = re.split(r"(\*\*.*?\*\*)", text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                r = par.add_run(part[2:-2])
                r.font.name = "Calibri"
                r.font.size = Pt(11)
                r.font.bold = True
            else:
                r = par.add_run(part)
                r.font.name = "Calibri"
                r.font.size = Pt(11)
        return par

    def h1(text):
        return p(text, before=18, after=10, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15)

    def h2(text):
        return p(text, before=14, after=6, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=13)

    def h3(text):
        return p(text, before=10, after=4, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=11.5, color=(0x1E, 0x29, 0x3B))

    def img(img_name, caption="", width=5.6):
        path = os.path.join(ILLUST_DIR, img_name)
        if os.path.exists(path):
            p_img = doc.add_paragraph()
            p_img.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(4)
            p_img.add_run().add_picture(path, width=Inches(width))
            
            if caption:
                p_cap = doc.add_paragraph()
                p_cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_after = Pt(10)
                r_cap = p_cap.add_run(caption)
                r_cap.font.name = "Calibri"
                r_cap.font.size = Pt(9.5)
                r_cap.font.bold = True
                r_cap.font.color.rgb = RGBColor(0, 0, 0)

    print("Rédaction de la page de garde et des pages liminaires...")

    # =========================================================================
    # PAGE 1 : PAGE DE GARDE OFFICIELLE ISEP
    # =========================================================================
    p("REPUBLIQUE DU SENEGAL", before=10, after=2, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)
    p("Ministère de l’Enseignement Supérieur, de la Recherche et de l’Innovation", after=14, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)
    p("Institut Supérieur d’Enseignement Professionnel Amadou Trawaré de Diamniadio", after=20, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12)

    p("N° : DISEP_ TIC _P5 _ Groupe : ...", after=24, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=11)

    p("PROJET DE FIN DE FORMATION POUR L’OBTENTION DU DISEP", before=10, after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("DIPLOME DES INSTITUTS SUPERIEURS D’ENSEIGNEMENT", after=40, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    # Cadre Thème sobre
    tbl_theme = doc.add_table(rows=1, cols=1)
    tbl_theme.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = tbl_theme.rows[0].cells[0]
    c.width = Inches(6.0)
    p_t = c.paragraphs[0]
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t.paragraph_format.space_before = Pt(14)
    p_t.paragraph_format.space_after = Pt(14)
    r1 = p_t.add_run("Thème :\n\n")
    r1.font.bold = True
    r1.font.size = Pt(13)
    r2 = p_t.add_run("Conception et Réalisation d'une Plateforme Web et Mobile\nde Prise en Charge Médicale et de Tiers Payant au Sénégal :\nCas de SantéSN")
    r2.font.bold = True
    r2.font.size = Pt(14)

    p("Soutenu le : __ / 11 / 2025", before=40, after=20, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    p("Présenté par :", before=10, after=4, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=11)
    p("M. Mamadou Lamarana Diallo", after=2, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=10.5)
    p("M. Mamadou Coulibaly", after=2, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=10.5)
    p("M. ... (Membre du groupe)", after=2, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, size=10.5)
    p("Mme / M. ... (Membre du groupe)", after=20, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, size=10.5)

    p("Encadré par : M. Siriman Konaré / M. Papa Ibrahima Niang", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=11)

    # =========================================================================
    # PAGES 2 À 5 : DÉDICACES INDIVIDUELLES
    # =========================================================================
    doc.add_page_break()
    h1("Dédicace")
    p("À mes chers parents,", before=24, after=12, bold=True, size=12)
    p("Je dédie ce projet à vous, qui avez été le socle solide sur lequel j'ai construit mes rêves. Votre amour inconditionnel, votre patience inépuisable et vos sacrifices quotidiens m'ont donné la force de persévérer et de croire en moi, même dans les moments les plus difficiles de ce parcours académique.")
    p("Chaque étape de ce travail reflète vos encouragements et votre confiance inébranlable. Merci de m'avoir transmis des valeurs cardinales de courage, de rigueur morale, de discipline et de persévérance, et de m'avoir constamment rappelé qu'avec la foi, la volonté et le travail acharné, tout objectif est réalisable.")
    p("Ce projet de fin de formation est le reflet direct de votre inspiration et de votre dévouement sans faille.")
    p("J'exprime également ma profonde gratitude à l'ensemble de ma famille, à mes frères et sœurs, ainsi qu'à mes amis proches, pour leur soutien moral constant et leurs prières bienveillantes qui ont enrichi et illuminé mon cheminement.")
    p("À mes enseignants et encadreurs de l'ISEP de Diamniadio, pour leur générosité pédagogique et leur encadrement précieux tout au long de ces deux années de formation en Analyste Programmeur Développeur.")
    p("Enfin, à mes camarades de groupe pour l'esprit de fraternité, de cohésion et d'abnégation qui a rendu possible l'aboutissement de cette plateforme SantéSN.", after=40)
    p("Mamadou Lamarana Diallo", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=11)

    doc.add_page_break()
    h1("Dédicace")
    p("À ma famille bien-aimée,", before=24, after=12, bold=True, size=12)
    p("Je dédie ce mémoire de fin d'études à ma chère famille, pilier incontournable de mon existence, dont les prières, la tendresse et la bienveillance constante ont constitué ma première source de motivation et d'énergie créatrice.")
    p("À mes parents exemplaires, pour les immenses sacrifices consentis, leur patience infinie et les principes d'honnêteté, de dignité et de rigueur qu'ils m'ont inculqués dès mon plus jeune âge. Aucun mot ne saurait exprimer à sa juste mesure la profondeur de ma reconnaissance et de mon respect envers vous.")
    p("À mes frères et sœurs, compagnons de tous les instants, pour leur affection constante, leurs encouragements enthousiastes dans les périodes de doute et leur présence rassurante à mes côtés.")
    p("J'adresse mes remerciements les plus sincères à l'ensemble du corps professoral du département TIC de l'Institut Supérieur d'Enseignement Professionnel (ISEP) de Diamniadio, pour la haute qualité des enseignements dispensés et leur accompagnement méthodologique sans faille.")
    p("À tous ceux qui ont contribué, de près ou de loin, par un conseil avisé, une relecture attentive ou un mot d'encouragement, à la concrétisation de ce mémoire.", after=40)
    p("Mamadou Coulibaly", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=11)

    doc.add_page_break()
    h1("Dédicace")
    p("À nos mères courageuses,", before=24, after=12, bold=True, size=12)
    p("Sources inépuisables de tendresse, d'inspiration et de sérénité. Chaque page de ce document porte l'empreinte de vos bénédictions maternelles, de vos veillées nocturnes et de vos prières ferventes. Rien de ce que nous accomplissons aujourd'hui n'aurait été envisageable sans votre amour inconditionnel.")
    p("À nos pères respectés, repères inébranlables de droiture, de sens du devoir et de persévérance. Vous avez consenti les plus grands sacrifices pour nous garantir une formation professionnelle d'excellence au sein de l'ISEP Diamniadio.")
    p("À tous les êtres chers qui nous ont quittés trop tôt mais dont les souvenirs vivaces et les conseils éclairés continuent d'orienter nos pas et de guider notre engagement pour le développement technologique du Sénégal.")
    p("Que ce modeste mémoire soit le témoignage vivant de notre attachement éternel et de notre dévouement.", after=40)
    p("Le Groupe de Projet SantéSN", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=11)

    doc.add_page_break()
    h1("Dédicace")
    p("Aux formateurs, mentors et bâtisseurs de compétences,", before=24, after=12, bold=True, size=12)
    p("Nous dédions ce travail à tous les enseignants du département Technologies de l'Information et de la Communication de l'ISEP Amadou Trawaré de Diamniadio. Vous avez su conjuguer exigences académiques et réalités professionnelles du terrain pour faire de nous des développeurs rigoureux et autonomes.")
    p("À l'ensemble de la promotion Analyste Programmeur Développeur (APD), pour la solidarité sans faille, le partage des connaissances lors des séances de codage intensif et les nuits blanches passées ensemble à surmonter les défis logiciels.")
    p("À tous les acteurs de la santé au Sénégal — médecins, pharmaciens, gestionnaires d'organismes de prévoyance maladie — qui luttent au quotidien pour l'accès universel et équitable aux soins médicaux. Puisse cette solution SantéSN constituer une pierre utile à l'édifice de la santé numérique nationale.", after=40)
    p("Promotion APD - ISEP Diamniadio", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=11)

    # =========================================================================
    # PAGES 6 ET 7 : REMERCIEMENTS
    # =========================================================================
    doc.add_page_break()
    h1("Remerciements")
    p("Avant tout développement, nous rendons grâce à **Dieu Tout-Puissant**, l'Omnipotent et le Miséricordieux, qui nous a accordé la santé, la lucidité d'esprit, la persévérance et le discernement indispensables pour mener à terme ce projet de fin de formation professionnelle.", before=16)
    p("Nos remerciements les plus sincères et les plus émus s'adressent en premier lieu à la **Direction Générale de l'Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Trawaré de Diamniadio**, pour le cadre pédagogique d'excellence, les infrastructures modernes et les conditions de travail optimales mises à la disposition des apprenants.")
    p("Nous tenons à exprimer notre profonde et respectueuse gratitude à nos éminents enseignants et encadreurs pédagogiques :")
    bullet("**Monsieur Siriman Konaré**, pour son encadrement attentif, sa grande disponibilité, la pertinence de ses orientations méthodologiques et son écoute bienveillante à chaque étape critique du projet.")
    bullet("**Monsieur Papa Ibrahima Niang**, pour sa rigueur intellectuelle, ses conseils techniques précieux en modélisation logicielle et son soutien constant qui ont forgé notre rigueur d'ingénierie.")
    bullet("**Monsieur Diagne et l'ensemble du corps professoral du Département TIC**, pour la richesse de leurs enseignements, leur générosité dans le partage des savoirs et leur volonté constante d'élever notre niveau de compétence technique.")

    doc.add_page_break()
    h1("Remerciements (Suite)")
    p("Nous exprimons également notre vive reconnaissance aux professionnels du secteur de la santé et des **Institutions de Prévoyance Maladie (IPM)** du Sénégal qui ont accepté de répondre à nos enquêtes de terrain. Leurs retours d'expérience pragmatiques sur les dysfonctionnements du circuit papier traditionnel ont été déterminants pour cibler les fonctionnalités à forte valeur ajoutée de la plateforme SantéSN.", before=16)
    p("Nos pensées chaleureuses vont à nos camarades de promotion, compagnons de route avec qui nous avons partagé des moments intenses de travail, d'émulation intellectuelle et d'entraide fraternelle. Ces deux années passées ensemble à l'ISEP de Diamniadio resteront gravées dans nos mémoires comme une aventure humaine et professionnelle exceptionnelle.")
    p("Enfin, à nos familles respectives, parents, frères, sœurs, conjoints et amis intimes : votre soutien moral indéfectible, votre patience face à nos longues heures d'absence et vos encouragements inconditionnels ont été notre plus solide rempart. Que chacun trouve dans ces lignes l'expression de notre affection la plus sincère et de notre éternelle reconnaissance.")

    # =========================================================================
    # PAGES 8 ET 9 : LISTES DES ABRÉVIATIONS
    # =========================================================================
    doc.add_page_break()
    h1("Listes des abréviations")
    p("Les sigles et abréviations techniques et sectoriels utilisés tout au long de ce mémoire sont définis ci-après :", before=12, after=14)

    abbrevs_1 = [
        "**ACID :** Atomicity, Consistency, Isolation, Durability (Propriétés transactionnelles d'une base de données relationnelle garantissant l'intégrité absolue des opérations financières et de délivrance)",
        "**API :** Application Programming Interface (Interface de communication programmatique standardisée permettant les échanges entre le frontend PWA et le serveur Django)",
        "**APD :** Analyste Programmeur Développeur (Filière de formation professionnelle d'élite du département TIC de l'ISEP Diamniadio)",
        "**CDP :** Commission de Protection des Données Personnelles du Sénégal (Autorité administrative indépendante régie par la loi n° 2008-12)",
        "**CI/CD :** Continuous Integration / Continuous Deployment (Pratique DevOps d'automatisation des tests et du déploiement continu sur cloud)",
        "**CORS :** Cross-Origin Resource Sharing (Mécanisme de sécurité HTTP encadrant les requêtes réseau entre origines distinctes)",
        "**CRUD :** Create, Read, Update, Delete (Quatre opérations de base de la persistance des données relationnelles)",
        "**CSRF :** Cross-Site Request Forgery (Mécanisme de falsification de requêtes intersites bloqué par les jetons cryptographiques Django)",
        "**CSS :** Cascading Style Sheets (Langage de présentation et de mise en forme adaptative des interfaces web)",
        "**DISEP :** Diplôme des Instituts Supérieurs d'Enseignement Professionnel (Titre officiel d'enseignement supérieur professionnel)",
        "**HMAC :** Hash-based Message Authentication Code (Mécanisme cryptographique à clé secrète partagée assurant l'intégrité et l'authenticité des ordonnances)",
        "**HTML :** HyperText Markup Language (Langage standard de structuration sémantique des documents web)",
        "**IDE :** Integrated Development Environment (Environnement de développement logiciel intégré, tel que Visual Studio Code)"
    ]
    for a in abbrevs_1:
        bullet(a)

    doc.add_page_break()
    h1("Listes des abréviations (Suite)")
    abbrevs_2 = [
        "**IPM :** Institution de Prévoyance Maladie (Organisme paritaire d'assurance santé d'entreprise au Sénégal, régi par la loi n° 75-50)",
        "**ISO 7810 ID-1 :** Norme internationale définissant le format physique et dimensionnel standardisé des cartes d'identité et de santé (85.60 × 53.98 mm)",
        "**JS :** JavaScript (Langage de script standard côté navigateur pour l'interactivité dynamique)",
        "**JWT :** JSON Web Token (Norme RFC 7519 pour l'authentification et l'échange compact et sécurisé de revendications)",
        "**MVT :** Modèle-Vue-Template (Patron d'architecture logicielle propre au framework web Django)",
        "**ORM :** Object-Relational Mapping (Couche logicielle faisant le pont entre les classes Python et les tables relationnelles PostgreSQL)",
        "**PDF :** Portable Document Format (Format de document numérique ouvert préservant la mise en page à l'impression)",
        "**PWA :** Progressive Web Application (Application web moderne exécutable sur mobile sans installation store, avec support hors-ligne)",
        "**RBAC :** Role-Based Access Control (Contrôle d'accès basé sur les rôles limitant les privilèges des 5 profils d'utilisateurs)",
        "**REST :** Representational State Transfer (Style d'architecture logicielle pour les services web distribués sans état)",
        "**SEN-CSU :** Agence Nationale de la Couverture Sanitaire Universelle du Sénégal (Institution publique de généralisation de l'assurance maladie)",
        "**SIG / GIS :** Système d'Information Géographique (Cartographie interactive Leaflet pour la géolocalisation des structures de santé)",
        "**SQL :** Structured Query Language (Langage relationnel standard de gestion et d'interrogation de bases de données)",
        "**TLS / SSL :** Transport Layer Security (Protocole cryptographique garantissant la confidentialité et l'intégrité des flux HTTPS)",
        "**UI / UX :** User Interface / User Experience (Conception ergonomique et fonctionnelle centrée sur l'expérience utilisateur)",
        "**URL :** Uniform Resource Locator (Adresse standardisée de localisation d'une ressource web sur Internet)",
        "**VSCode :** Visual Studio Code (Éditeur de code source extensible développé par Microsoft)"
    ]
    for a in abbrevs_2:
        bullet(a)

    # =========================================================================
    # PAGES 10 ET 11 : LISTES DES FIGURES
    # =========================================================================
    doc.add_page_break()
    h1("Listes des figures")
    p("Le présent mémoire comporte 36 illustrations techniques réelles réparties comme suit :", before=12, after=14)

    figs_1 = [
        "Figure 1 : Diagramme de classes – Docteur (p. 25)",
        "Figure 2 : Diagramme de classes – Patient / Assuré (p. 27)",
        "Figure 3 : Diagramme de classes – Pharmacien, Gestionnaire et Administrateur (p. 29)",
        "Figure 4 : Diagramme de classes global consolidé du système (p. 31)",
        "Figure 5 : Diagramme de cas d'utilisation – Docteur (p. 33)",
        "Figure 6 : Diagramme de cas d'utilisation – Patient / Assuré (p. 35)",
        "Figure 7 : Diagramme de cas d'utilisation – Pharmacien d'officine (p. 37)",
        "Figure 8 : Diagramme de cas d'utilisation – Gestionnaire IPM (p. 39)",
        "Figure 9 : Diagramme de cas d'utilisation – Administrateur système (p. 41)",
        "Figure 10 : Diagramme de séquence – Docteur : Prescription et scellement HMAC (p. 43)",
        "Figure 11 : Diagramme de séquence – Patient : Consultation solde et carte ISO (p. 44)",
        "Figure 12 : Diagramme de séquence – Pharmacien : Délivrance atomique ACID (p. 46)",
        "Figure 13 : Diagramme de séquence complet – Tiers payant de bout en bout (p. 47)",
        "Figure 14 : Architecture logicielle globale 4-couches de SantéSN (p. 48)",
        "Figure 15 : Logo officiel Python (p. 50)",
        "Figure 16 : Logo officiel Django Framework (p. 50)",
        "Figure 17 : Logo officiel Django ORM (p. 51)",
        "Figure 18 : Logo officiel PostgreSQL (p. 51)"
    ]
    for f in figs_1:
        bullet(f)

    doc.add_page_break()
    h1("Listes des figures (Suite)")
    figs_2 = [
        "Figure 19 : Logo officiel SQLite (p. 52)",
        "Figure 20 : Logo officiel JSON Web Token (JWT) (p. 52)",
        "Figure 21 : Logo de protection CSRF Shield (p. 53)",
        "Figure 22 : Logo officiel Redis In-Memory Cache (p. 53)",
        "Figure 23 : Logo officiel CORS Headers (p. 54)",
        "Figure 24 : Logo officiel HTML5 Standard (p. 54)",
        "Figure 25 : Logo officiel Tailwind CSS (p. 55)",
        "Figure 26 : Logo officiel JavaScript ES6+ (p. 55)",
        "Figure 27 : Logo officiel Leaflet SIG Cartographie (p. 56)",
        "Figure 28 : Logo officiel Progressive Web App (PWA) (p. 56)",
        "Figure 29 : Logo officiel Vercel Serverless Platform (p. 57)",
        "Figure 30 : Logo officiel Nginx Reverse Proxy (p. 57)",
        "Figure 31 : Logo officiel Visual Studio Code (p. 58)",
        "Figure 32 : Logo officiel GitHub Enterprise (p. 58)",
        "Figure 33 : Logo officiel ReportLab PDF Engine (p. 58)",
        "Figure 34 : Capture d'écran – Page d'accueil et portail d'authentification (p. 61)",
        "Figure 35 : Capture d'écran – Espace Assuré : Carte dématérialisée ISO 7810 (p. 62)",
        "Figure 36 : Capture d'écran – Espace Médecin : Prescription sécurisée HMAC (p. 63)",
        "Figure 37 : Capture d'écran – Espace Pharmacie : Scanner optique jsQR temps réel (p. 64)",
        "Figure 38 : Capture d'écran – Espace Gestionnaire : Cartographie Leaflet SIG (p. 65)",
        "Figure 39 : Capture d'écran – Supervision Administrateur : Journal d'audit CDP (p. 66)"
    ]
    for f in figs_2:
        bullet(f)

    # =========================================================================
    # PAGE 12 : ANNONCE DES CHAPITRES
    # =========================================================================
    doc.add_page_break()
    p("ORGANISATION DU MÉMOIRE", before=120, after=30, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)
    p("Introduction Générale", before=10, after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Chapitre 1 : Présentation du projet", after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Chapitre 2 : Études de l’existant", after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Chapitre 3 : Conception et Modélisation", after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Chapitre 4 : Technologies et outils utilisés", after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Chapitre 5 : Réalisation du projet", after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Conclusion Générale et Perspectives", after=20, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    p("Tables des matières", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)

    # =========================================================================
    # PAGE 13 : RÉSUMÉ / ABSTRACT
    # =========================================================================
    doc.add_page_break()
    h1("Résumé :")
    p("Dans un contexte où les structures sanitaires et les organismes de prévoyance maladie au Sénégal sont confrontés à des défis majeurs liés aux lourdeurs administratives, aux délais excessifs de remboursement et aux fraudes récurrentes induites par la gestion manuelle du tiers payant, la digitalisation intégrale des processus s'impose comme un impératif d'équité et d'efficacité.")
    p("Le présent mémoire de fin de formation porte sur la conception et la réalisation de **SantéSN**, une plateforme web et mobile progressive (PWA) de tiers payant médical et de coordination des soins, développée au sein de l'**Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Trawaré de Diamniadio** dans la filière Analyste Programmeur Développeur (APD).")
    p("Cette solution interconnecte de manière fluide et étanche cinq profils d'acteurs clés : les assurés sociaux, les médecins prescripteurs, les pharmaciens d'officine, les gestionnaires d'organismes de prévoyance (IPM/Mutuelles) et les administrateurs du système. SantéSN intègre des innovations logicielles majeures : la dématérialisation de la carte d'assuré au format standardisé **ISO 7810 ID-1 avec QR Code dynamique vectoriel**, la certification cryptographique des ordonnances médicales par **sceau d'intégrité HMAC-SHA256**, le décodage optique direct par caméra en pharmacie via **jsQR**, le verrouillage pessimiste atomique (**transactions ACID SELECT FOR UPDATE**) empêchant toute double délivrance, ainsi que la cartographie sanitaire interactive propulsée par **Leaflet SIG**.")
    p("Développée avec le cadriciel **Django 5.2 LTS (Python)**, la base de données relationnelle serverless **PostgreSQL Neon**, et déployée en haute disponibilité sur **Vercel Cloud**, SantéSN valide avec succès une suite exhaustive de **196 tests automatisés (100% de réussite)** et se conforme strictement à la loi sénégalaise n° 2008-12 relative à la protection des données à caractère personnel.")
    p("**Mots-clés :** Tiers Payant Médical, Carte Dématérialisée ISO 7810, Sceau HMAC-SHA256, Django 5.2, PostgreSQL Neon, Verrouillage ACID, Santé Numérique Sénégal, ISEP Diamniadio.", before=16)

    # =========================================================================
    # PAGE 14 : INTRODUCTION GÉNÉRALE
    # =========================================================================
    doc.add_page_break()
    h1("Introduction générale")
    p("Le secteur de la santé au Sénégal traverse une phase historique de transformation, stimulée par une forte volonté publique de modernisation des infrastructures et par l'ambition nationale d'assurer une couverture sanitaire universelle effective à l'ensemble de la population. Au cœur de ce dispositif de protection sociale, le mécanisme du **tiers payant** joue un rôle fondamental : il dispense le travailleur et sa famille de l'avance totale des frais de consultations médicales, d'hospitalisations et d'achats de produits pharmaceutiques au moment précis où survient la maladie.")
    p("Néanmoins, force est de constater que la quasi-totalité des **Institutions de Prévoyance Maladie (IPM)** et des mutuelles de santé sénégalaises continuent de s'appuyer sur des circuits physiques archaïques à base de carnets cartonnés, de bons de prise en charge volants et de factures manuscrites. Cette prédominance du support papier engendre des délais de règlement insoutenables pour les prestataires de santé (fréquemment compris entre 60 et 120 jours), des coûts logistiques considérables et des failles critiques favorisant le prêt illicite de cartes et la falsification d'ordonnances.")
    p("C'est pour répondre à cette urgence sanitaire et économique que s'inscrit le projet **SantéSN**, initié par les apprenants du département Technologies de l'Information et de la Communication de l'ISEP Diamniadio. L'objectif cardinal de ce travail d'ingénierie logicielle est de concevoir, développer et déployer une plateforme numérique souveraine, sécurisée, accessible sans surcoût matériel et parfaitement adaptée aux réalités locales de connectivité du Sénégal.")
    p("Le présent mémoire s'articule autour de cinq chapitres méthodiques :")
    bullet("Le **Chapitre 1** présente le cadre institutionnel du projet, le contexte sectoriel, la problématique, les objectifs et les résultats attendus.")
    bullet("Le **Chapitre 2** analyse en profondeur l'existant, critique les pratiques manuelles en vigueur et justifie la solution retenue face aux contraintes locales.")
    bullet("Le **Chapitre 3** constitue le cœur de la conception et de la modélisation logicielle, détaillant la démarche UML, les diagrammes de classes, de cas d'utilisation et de séquences pour chaque acteur, l'architecture 4-couches et la sécurité.")
    bullet("Le **Chapitre 4** expose avec rigueur les technologies et outils utilisés, justifiant chaque composant logiciel à travers une fiche descriptive et son logo officiel.")
    bullet("Le **Chapitre 5** détaille la réalisation concrète du projet, l'implémentation backend et frontend, les 196 tests automatisés de validation et les captures d'écran réelles de la plateforme.")
    p("Une conclusion générale dressera enfin le bilan des résultats obtenus et ouvrira des perspectives technologiques d'évolution vers le Mobile Money et l'Intelligence Artificielle.")

    # =========================================================================
    # CHAPITRE 1 : PRÉSENTATION DU PROJET (Pages 15 à 19)
    # =========================================================================
    doc.add_page_break()
    h1("Chapitre 1 : Présentation du projet :")
    
    h2("1. Présentation de la structure d’accueil et du commanditaire")
    p("Le présent projet de fin de formation a été conçu et réalisé au sein de l'**Institut Supérieur d'Enseignement Professionnel (ISEP) Amadou Trawaré de Diamniadio**. Créé par l'État du Sénégal pour répondre aux exigences d'employabilité et de souveraineté technique, l'ISEP Diamniadio est un pôle d'excellence dédié à l'enseignement professionnel supérieur.")
    p("Au sein de l'institut, le **Département TIC (Technologies de l'Information et de la Communication)** prépare les futurs cadres techniques à travers le métier d'**Analyste Programmeur Développeur (APD)**. Cette filière vise l'acquisition de compétences avancées en génie logiciel, en modélisation orientée objet, en architecture de bases de données relationnelles, en sécurité informatique et en méthodologies Agiles de gestion de projet.")
    p("Le commanditaire fonctionnel de notre étude est représenté par l'écosystème des **Institutions de Prévoyance Maladie (IPM)** du Sénégal, régies par la loi n° 75-50 du 3 avril 1975, ainsi que par les prestataires de soins conventionnés (cliniques privées, centres de santé publics et officines pharmaceutiques). Afin de bien appréhender les enjeux du projet, il convient d'exposer en premier lieu le contexte sanitaire dans lequel s'enracine notre travail de digitalisation.")

    h2("2. Contexte :")
    p("L’évolution rapide des technologies numériques au Sénégal — marquée par la pénétration massive de l'Internet mobile 4G et la démocratisation des smartphones jusque dans les zones périurbaines — a profondément transformé les pratiques quotidiennes des citoyens et des entreprises. Des secteurs entiers tels que le transfert d'argent (Wave, Orange Money) et le commerce digital ont accompli des bonds prodigieux d'efficacité.")
    p("Toutefois, le secteur de la couverture maladie d'entreprise demeure l'un des rares domaines où la gestion opérationnelle est restée figée à l'ère pré-numérique. Les travailleurs cotisent mensuellement à des caisses d'IPM, mais lors d'un épisode morbide, l'accès au tiers payant les contraint à des démarches physiques fastidieuses pour retirer des bons de prise en charge valables pour une seule consultation.")
    p("Dans les officines de pharmacie, les praticiens sont obligés de collecter manuellement des liasses de feuilles de soins et des photocopies de pièces d'identité, avant de les envoyer par courrier physique aux sièges des IPM en fin de mois. Cette situation génère des retards d'encaissement dramatiques pour les pharmaciens et paralyse la trésorerie des structures médicales locales.")
    p("C'est dans cette dynamique impérieuse de modernisation que s'inscrit le projet **SantéSN**. Il vise à offrir une solution web et mobile complète, souveraine et robuste, adaptée aux réalités infrastructurelles du Sénégal pour dématérialiser intégralement la chaîne de soins et automatiser le calcul du tiers payant.")

    doc.add_page_break()
    h2("3. Problématique")
    p("Comment moderniser efficacement la gestion quotidienne de la prise en charge médicale et du tiers payant à travers une plateforme digitale pérenne, en assurant :")
    bullet("La fluidité et la rapidité des interactions en temps réel entre les cinq profils d'acteurs (assurés, médecins, pharmaciens, gestionnaires d'IPM et administrateurs) ?")
    bullet("L'éradication des fraudes récurrentes liées à l'usurpation d'identité d'assurés, à la falsification des ordonnances et à la double délivrance de médicaments dans des officines distinctes ?")
    bullet("La centralisation sécurisée et le cloisonnement hermétique (multi-tenancy) des données de santé conformément à la législation nationale ?")
    bullet("L'automatisation du calcul de la quote-part patient et de la part organisme avec contrôle instantané du plafond budgétaire annuel familial ?")
    bullet("La continuité de service en mode hors-ligne dans les zones où la connectivité Internet est instable ou dégradée ?")

    h2("4. Objectifs :")
    h3("a. Objectif général :")
    p("Concevoir, modéliser, développer et tester une plateforme logicielle web et mobile progressive (PWA) nommée **SantéSN**, permettant la gestion dématérialisée intégrale de la prise en charge médicale et du tiers payant au Sénégal, dans un environnement hautement sécurisé, performant et conforme aux standards académiques et réglementaires.")

    h3("b. Objectifs spécifiques :")
    p("Pour concrétiser cet objectif général, notre projet poursuit les objectifs spécifiques suivants :")
    bullet("Dématérialiser la carte de membre physique en générant une **carte numérique d'assuré au format ISO 7810 ID-1**, dotée d'un **QR Code vectoriel dynamique** contenant un identifiant cryptographique unique.")
    bullet("Mettre en place un outil d'ordonnance électronique pour le médecin, intégrant le calcul automatique d'un **sceau cryptographique HMAC-SHA256** garantissant qu'aucun médicament ni aucune dose ne peuvent être altérés a posteriori.")
    bullet("Intégrer dans l'interface du pharmacien un **scanner optique temps réel (jsQR)** utilisant directement la caméra du terminal sans nécessiter de douchette code-barres coûteuse.")
    bullet("Implémenter un mécanisme de validation de délivrance atomique basé sur des **verrous transactionnels pessimistes PostgreSQL (`select_for_update()`)** afin d'empêcher avec une certitude absolue le risque de double délivrance simultanée d'une même ordonnance.")
    bullet("Automatiser l'instruction des conventions tarifaires et des demandes de remboursement de soins hors réseau par les gestionnaires d'IPM avec télétransmission des bordereaux de liquidation.")
    bullet("Fournir un **Système d'Information Géographique (SIG)** basé sur **Leaflet** pour cartographier en temps réel l'ensemble du réseau sanitaire conventionné à l'échelle nationale.")
    bullet("Assurer la conformité stricte avec la loi sénégalaise n° 2008-12 sur les données à caractère personnel via un journal d'audit immuable et un chiffrement renforcé.")

    doc.add_page_break()
    h2("5. Portée du projet :")
    p("Le projet **SantéSN** s'inscrit dans une démarche globale de numérisation de la santé publique et de l'assurance maladie d'entreprise. Sa portée fonctionnelle, technique et organisationnelle couvre l'ensemble des étapes du parcours de soins :")
    p("D’un point de vue fonctionnel, SantéSN englobe huit modules applicatifs interconnectés :")
    bullet("Le module d'identification et de gestion des cartes dématérialisées ISO 7810.")
    bullet("Le module de gestion du plafond annuel familial avec calcul dynamique de la jauge de consommation restante.")
    bullet("Le module de prise de rendez-vous et de gestion de l'agenda médical en ligne.")
    bullet("Le module de prescription informatisée et de scellement cryptographique des ordonnances.")
    bullet("Le module officinal de vérification par caméra et de délivrance atomique sécurisée.")
    bullet("Le module de gestion des conventions et de liquidation des bordereaux de tiers payant.")
    bullet("Le module de demande et d'instruction des remboursements hors réseau.")
    bullet("Le module SIG de géolocalisation cartographique des établissements de santé conventionnés.")
    p("Du côté des utilisateurs, le système prend en charge cinq profils opérationnels distincts : les assurés (et leurs ayants droit), les médecins, les pharmaciens, les gestionnaires d'IPM et les administrateurs système. Chacun dispose d'un espace applicatif ergonomique strictement borné par une matrice de contrôle d'accès basée sur les rôles (RBAC).")
    p("La portée du projet s’étend également aux impératifs d'interopérabilité et de souveraineté numérique. Conçue comme une **Progressive Web App (PWA)**, SantéSN fonctionne sur tout type de terminal (ordinateur de bureau, tablette médicale, smartphone Android ou iOS) sans imposer de téléchargement préalable depuis un store étranger propriétaire, et maintient ses fonctionnalités clés en cache local grâce aux technologies de Service Worker.")

    h2("6. Les Résultats Attendus :")
    p("La mise en œuvre de SantéSN produit des impacts structurants sur la qualité des soins et la gestion financière :")
    
    h3("a. Digitalisation complète de la gestion du tiers payant :")
    p("Remplacement à 100% des liasses papier et des formulaires volants par des enregistrements numériques certifiés, réduisant drastiquement les délais de traitement des dossiers de remboursement de 90 jours à moins de 48 heures.")

    h3("b. Éradication de la fraude et intégrité des ordonnances :")
    p("Grâce au sceau cryptographique HMAC-SHA256 et au verrouillage transactionnel exclusif en base de données, les tentatives de falsification de posologie et les fraudes par double présentation d'ordonnances dans plusieurs pharmacies sont rigoureusement bloquées.")

    doc.add_page_break()
    h3("c. Automatisation de la gestion administrative et médicale :")
    p("Le calcul instantané de la quote-part (ex: 80% organisme / 20% patient) libère les professionnels de santé des tâches de calcul manuel et permet la production instantanée de reçus horodatés et de bordereaux de liquidation certifiés.")

    h3("d. Amélioration de la traçabilité et du suivi budgétaire des assurés :")
    p("Chaque famille dispose d'une visibilité transparente sur sa consommation médicale en temps réel. La jauge graphique de plafond restant avertit l'assuré avant tout dépassement imprévu de son budget annuel garanti.")

    h3("e. Sécurisation des données médicales et conformité légale :")
    p("La stricte étanchéité multi-tenant garantit qu'aucune IPM ne peut accéder aux dossiers des assurés d'une IPM concurrente. Toutes les actions sensibles sont consignées dans un journal d'audit immuable conforme aux préconisations de la CDP du Sénégal.")

    h3("f. Centralisation des rapports et supervision financière :")
    p("Les directions d'IPM disposent de tableaux de bord décisionnels en temps réel indiquant le volume des sinistres engagés, les montants liquidés, les taux de consommation par pathologie et les prévisions de trésorerie.")

    h3("g. Accessibilité et adaptation au contexte local :")
    p("Une interface épurée, responsive, compatible avec les connexions réseau modestes et dotée d'une résilience hors-ligne permet à SantéSN d'être adoptée immédiatement par des officines et postes de santé situés à l'intérieur du pays.")

    # =========================================================================
    # CHAPITRE 2 : ÉTUDES DE L'EXISTANT (Pages 20 à 22)
    # =========================================================================
    doc.add_page_break()
    h1("Chapitre 2 : Études de l’existant :")

    h2("1. Pratiques actuelles dans les cliniques et IPM :")
    p("Au Sénégal, le fonctionnement opérationnel du tiers payant au sein de la majorité des Institutions de Prévoyance Maladie (IPM) et des mutuelles repose encore sur un modèle artisanal séquentiel :")
    bullet("L'assuré doit se déplacer physiquement au siège de son IPM pour solliciter l'émission d'un bon de prise en charge papier (carnet à souches).")
    bullet("Muni de ce bon, le patient consulte son médecin traitant qui lui délivre une ordonnance manuscrite sur papier libre.")
    bullet("Le patient se rend ensuite en officine de pharmacie où le préparateur vérifie visuellement la conformité du carnet, calcule manuellement la quote-part et reporte manuellement les prix des boîtes délivrées sur une facture tripartite.")
    bullet("En fin de mois calendaire, les officines regroupent manuellement des centaines de liasses de factures accompagnées des talons de bons papier et les acheminent par coursier au siège de l'IPM.")
    bullet("Les auditeurs médicaux et comptables de l'IPM vérifient chaque ligne de facture à la main. En raison de l'engorgement administratif, les règlements financiers effectifs interviennent après des délais considérables de **60 à 120 jours**.")

    h2("2. Analyse des solutions existantes :")
    p("Face à cette situation, différentes approches numériques ont été explorées à l'échelle internationale et régionale :")
    p("Les grandes plateformes internationales comme **Doctolib**, **Zocdoc** ou **Maiia** sont d'excellentes solutions de gestion d'agenda et de prise de rendez-vous en ligne. Toutefois, elles ne gèrent nullement la complexité du tiers payant d'entreprise, ni la facturation conventionnée, ni l'intégration des barèmes d'assurance maladie spécifiques à l'Afrique de l'Ouest.")
    p("D'autre part, des progiciels médicaux propriétaires hospitaliers (ERP santé) existent sur le marché. Cependant, ils s'avèrent extrêmement coûteux en frais de licence annuelle (facturés en devises étrangères), complexes à déployer, fermés et totalement inadaptés aux petites structures médicales et aux mutuelles communautaires de la région.")
    p("Enfin, quelques initiatives locales émergentes ont proposé des applications mobiles natives sur le Play Store. Néanmoins, l'obligation d'un téléchargement préalable, la gourmandise en espace de stockage smartphone et l'absence de résilience hors-ligne ont freiné leur adoption massive auprès des populations.")

    doc.add_page_break()
    h2("3. Limites identifiées :")
    p("L’analyse critique du circuit traditionnel met en exergue des vulnérabilités organisationnelles majeures :")
    bullet("**Lenteur et lourdeur logistique :** Des millions de formulaires imprimés chaque année, entraînant des coûts de papier et d'archivage physique exorbitants pour les IPM.")
    bullet("**Vulnérabilité critique à la fraude :** Absence de vérification biométrique ou optique infalsifiable. Le prêt de carnets à des parents non déclarés est estimé à plus de 15% des dépenses de santé d'entreprise.")
    bullet("**Risque de double délivrance :** Une ordonnance papier photocopiée peut être présentée successivement dans deux officines situées dans des quartiers différents sans qu'aucun pharmacien ne puisse détecter la délivrance antérieure.")
    bullet("**Pénalisation de la trésorerie des prestataires :** Les délais de paiement de 2 à 3 mois poussent certaines officines à suspendre unilatéralement les conventions avec les IPM, laissant les malades démunis.")

    h2("4. Améliorations proposées par SantéSN :")
    p("Pour remédier de façon pérenne à ces insuffisances, SantéSN introduit une rupture méthodologique et technologique :")
    bullet("**Dématérialisation intégrale :** Suppression définitive des carnets physiques et des bons volants au profit de cartes ISO 7810 virtuelles avec QR code dynamique.")
    bullet("**Scellement cryptographique des prescriptions :** Tout acte médical prescrit est scellé par une empreinte HMAC-SHA256 garantissant son inaltérabilité absolue.")
    bullet("**Validation officinale en temps réel :** Le pharmacien scanne l'ordonnance avec la caméra de son navigateur et le système contrôle en moins d'une seconde la validité des droits.")
    bullet("**Verrouillage concurrentiel atomique :** L'usage de transactions ACID PostgreSQL `select_for_update()` garantit qu'une ordonnance validée dans une pharmacie A est instantanément marquée comme 'DÉLIVRÉE' à la milliseconde près, rendant impossible toute double délivrance dans une pharmacie B.")
    bullet("**Télétransmission continue et automatisation financière :** Les bordereaux de liquidation sont produits électroniquement au fil de l'eau, permettant d'abaisser les délais de paiement à moins de 48 heures.")

    # =========================================================================
    # CHAPITRE 3 : CONCEPTION ET MODÉLISATION (Pages 23 à 48)
    # =========================================================================
    doc.add_page_break()
    h1("Chapitre 3 : Conception et Modélisation")

    h2("1. Technologies et outils de modélisation")
    p("La phase de conception constitue l'étape fondamentale du cycle d'ingénierie logicielle. Elle permet de structurer formellement le comportement attendu du système et de concevoir des architectures robustes et évolutives avant toute phase d'implémentation.")
    p("Pour concevoir SantéSN, nous avons adopté le standard universel **UML (Unified Modeling Language)** dans sa version 2.5. Ce formalisme graphique offre une sémantique rigoureuse pour représenter à la fois la structure statique du domaine métier (diagrammes de classes) et sa dynamique temporelle (diagrammes de cas d'utilisation et diagrammes de séquence).")
    p("La modélisation s'est appuyée sur l'outil déclaratif **Mermaid.js**, complété par des outils de modélisation visuelle pour assurer une traçabilité parfaite entre les règles de gestion formulées dans le cahier des charges et le code source Python/Django final.")

    h2("2. Étude des besoins")
    h3("a. Identification des acteurs :")
    p("L’analyse fonctionnelle du domaine de la prévoyance médicale au Sénégal permet d'identifier cinq acteurs fondamentaux :")
    bullet("**Le Patient / Assuré :** Bénéficiaire principal de la couverture santé. Il utilise la plateforme pour consulter son identifiant de santé, afficher sa carte dématérialisée ISO 7810 avec QR Code, suivre le solde de son plafond annuel garanti, prendre rendez-vous auprès des praticiens conventionnés, déclarer ses ayants droit et soumettre des factures de soins pour remboursement.")
    bullet("**Le Docteur / Médecin :** Praticien de santé habilité. Il accède à son planning de consultations, consulte les antécédents médicaux du patient, rédige des ordonnances électroniques certifiées et appose l'empreinte cryptographique HMAC avant de délivrer le document au patient.")
    bullet("**Le Pharmacien d'officine :** Prestataire de santé exécutant. Il scanne le QR code de l'ordonnance ou de la carte de l'assuré à l'aide de la caméra de son terminal, contrôle instantanément la validité des droits, visualise la quote-part prise en charge et valide la délivrance avec verrouillage transactionnel strict.")
    bullet("**Le Responsable / Gestionnaire d'IPM :** Cadre administratif de l'organisme d'assurance. Il gère le conventionnement tarifaire des prestataires, supervise la cartographie interactive du réseau sanitaire (Leaflet SIG), instruit les demandes de remboursement hors réseau et télétransmet les bordereaux de liquidation aux banques partenaires.")
    bullet("**L’Administrateur système :** Ingénieur technique responsable de l'infrastructure. Il administre les comptes utilisateurs, configure les paramètres de sécurité, supervise le journal d'audit immuable conformément aux lois de la CDP et gère les sauvegardes de la base de données relationnelle.")

    doc.add_page_break()
    h3("b. Règles de gestion :")
    p("Le bon fonctionnement du système et la sécurité des transactions reposent sur un ensemble de règles de gestion métier strictes :")
    bullet("**RG-01 (Unicité de l'assuré) :** Chaque assuré est identifié par un matricule d'organisme unique et un numéro de carte conforme au standard international ISO 7810 ID-1.")
    bullet("**RG-02 (Plafonnement annuel strict) :** Les dépenses engagées par un assuré et ses ayants droit ne peuvent en aucun cas excéder le plafond annuel alloué par le plan de couverture de l'organisme.")
    bullet("**RG-03 (Scellement infalsifiable) :** Toute ordonnance médicale enregistrée doit comporter un sceau cryptographique calculé par l'algorithme HMAC-SHA256 combinant l'identifiant de la consultation, le code médecin, la liste des médicaments et une clé secrète serveur.")
    bullet("**RG-04 (Interdiction stricte de double délivrance) :** Une ordonnance dont le statut passe à 'DÉLIVRÉE' devient immédiatement invalide pour toute présentation ultérieure. L'accès en écriture au statut de l'ordonnance est impérativement verrouillé par une transaction atomique pessimiste (`SELECT FOR UPDATE`).")
    bullet("**RG-05 (Calcul automatique de la quote-part) :** Lors de la délivrance en pharmacie ou de la consultation, le système applique automatiquement le taux de prise en charge défini dans la convention active (généralement 80% organisme / 20% quote-part patient).")
    bullet("**RG-06 (Étanchéité Multi-Tenancy) :** Un gestionnaire de l'IPM 'A' ne peut sous aucun prétexte visualiser, modifier ou exporter les données des assurés, des conventions ou des bordereaux de l'IPM 'B'. Cette étanchéité est assurée par le patron architectural Scoped QuerySet au niveau de l'ORM.")
    bullet("**RG-07 (Traçabilité CDP immuable) :** Toute opération de création, de modification, d'accès aux dossiers médicaux ou de liquidation financière est consignée avec horodatage certifié, identifiant d'auteur et adresse IP dans le journal d'activité de conformité.")

    doc.add_page_break()
    h2("3. Modélisation UML")
    p("La modélisation orientée objet de SantéSN est découpée méthodiquement à travers les diagrammes de classes, les diagrammes de cas d'utilisation et les diagrammes de séquence.")

    h3("Diagramme de classes :")
    p("Le diagramme de classes représente la structure statique du système d'information. Il explicite les entités métier, leurs attributs typés, leurs opérations fondamentales ainsi que les relations sémantiques (associations, agrégations, compositions et héritages) qui les lient.")

    h3("Diagramme de classes – Docteur :")
    p("Ce premier diagramme met en lumière les relations gravitant autour du médecin. La classe principale **Docteur** est liée aux entités **Consultation**, **Ordonnance** et **LigneOrdonnance**.")
    p("Un Docteur peut effectuer plusieurs consultations (relation 1 à *). Chaque consultation est rattachée à un patient et peut générer une ordonnance médicale certifiée.")
    bullet("**Classe Docteur :** Contient le matricule au conseil de l'ordre, la spécialité clinique et les coordonnées, et offre les méthodes `consulterPlanning()`, `voirDossierPatient()`, `faireConsultation()` et `apposerSceauHMAC()`.")
    bullet("**Classe Consultation :** Enregistre la date, le motif clinique, les observations diagnostiques et le montant des honoraires conventionnés.")
    bullet("**Classe Ordonnance :** Encapsule le code QR vectoriel, l'empreinte HMAC, la date d'expiration (30 jours) et le statut de délivrance (ACTIVE, DÉLIVRÉE, EXPIRÉE).")

    img("fig_01_classe_docteur.png", "Figure 1 : Diagramme de classes – Docteur", width=5.6)
    p("**Analyse et interprétation :** Cette structure garantit que toute prescription médicale est indissociable de l'acte clinique qui l'a motivée, empêchant ainsi la création d'ordonnances orphelines sans diagnostic préalable.", italic=True)

    doc.add_page_break()
    h3("Diagramme de classe Patient :")
    p("Ce diagramme illustre la structure des classes relatives à la gestion de l'Assuré social dans le système d'information de tiers payant. Il met en évidence la relation entre la classe centrale **Patient** et ses entités associées : **RendezVous**, **DemandeRemboursement**, **Facture** et **PlanCouverture**.")
    bullet("**Classe Patient :** Représente l'assuré ou son ayant droit. Elle stocke le matricule IPM, le numéro de carte ISO 7810, les données d'état civil, le groupe sanguin et le solde restant de son plafond annuel garanti. Elle expose les méthodes `afficherCarteISO7810()`, `consulterSoldePlafond()`, `declarerAyantDroit()` et `soumettreRemboursement()`.")
    bullet("**Classe RendezVous :** Gère la planification des créneaux de consultation avec date, heure, motif et statut de confirmation.")
    bullet("**Classe DemandeRemboursement :** Permet la transmission numérique des factures et quittances acquittées lors de soins réalisés en dehors du réseau conventionné direct.")

    img("fig_02_classe_patient.png", "Figure 2 : Diagramme de classes – Patient / Assuré", width=5.6)
    p("**Analyse et interprétation :** La modélisation intègre directement le plafond budgétaire dans le profil de l'assuré, permettant au système d'effectuer un écrêtement instantané lors de chaque demande de prise en charge.", italic=True)

    doc.add_page_break()
    h3("Diagramme de classes – Pharmacien, Gestionnaire et Administrateur :")
    p("Ce diagramme illustre l'organisation des classes d'acteurs professionnels et administratifs. Afin de factoriser les attributs communs d'authentification et de sécurité, nous avons mis en œuvre le principe fondamental de l'**héritage orienté objet** à partir d'une classe parente abstraite **Utilisateur**.")
    bullet("**Classe Utilisateur (Abstraite) :** Centralise l'identifiant technique, l'adresse e-mail normalisée, le mot de passe chiffré par algorithme PBKDF2/Argon2, le rôle RBAC et le statut de compte, ainsi que les méthodes `seConnecter()` et `reinitialiserMotDePasse()`.")
    bullet("**Classe Pharmacien :** Hérite d'Utilisateur et ajoute le numéro de licence d'officine ainsi que les opérations `scannerQRCode()`, `verifierOrdonnance()` et `validerDelivranceACID()`.")
    bullet("**Classe GestionnaireIPM :** Hérite d'Utilisateur et intègre l'organisme de rattachement pour assurer l'étanchéité multi-tenant, avec les méthodes `gererConventions()` et `teletransmettreBordereaux()`.")
    bullet("**Classe Administrateur :** Hérite d'Utilisateur et dispose des privilèges les plus élevés pour `gererUtilisateurs()` et `superviserLogsCDP()`.")

    img("fig_03_classe_admin_gestionnaire.png", "Figure 3 : Diagramme de classes – Pharmacien, Gestionnaire et Administrateur", width=5.8)
    p("**Analyse et interprétation :** L'usage de l'héritage optimise la maintenabilité du code source Django et assure une ségrégation étanche des privilèges d'accès.", italic=True)

    doc.add_page_break()
    h3("Diagramme de classes global consolidé :")
    p("Ce diagramme offre une vision panoramique et exhaustive du modèle de données de SantéSN. Il articule les classes fondamentales du domaine médical et assurantiel : **Organisme**, **PlanCouverture**, **Patient**, **ConventionPrestataire**, **Prestataire**, **Consultation**, **Ordonnance** et **Delivrance**.")

    img("fig_04_classe_globale.png", "Figure 4 : Diagramme de classes global consolidé du système", width=6.0)
    p("**Analyse et interprétation :** La structure globale fait apparaître la double articulation du tiers payant : d'une part la convention liant l'Organisme au Prestataire, et d'autre part la prescription médicale reliant le Médecin au Patient et à la Pharmacie exécutante. Cette modélisation constitue le socle direct de la base de données relationnelle PostgreSQL.", italic=True)

    doc.add_page_break()
    h3("Diagramme de cas d’utilisation :")
    p("Le diagramme de cas d’utilisation permet de définir les limites fonctionnelles du système en explicitant les interactions entre chaque acteur et les services applicatifs offerts. Il met en lumière les dépendances structurelles via les relations standard d'inclusion (`<<include>>`) et d'extension (`<<extend>>`).")

    h3("Cas d’utilisation – Docteur :")
    p("Ce cas d'utilisation modélise les fonctionnalités métier accessibles au médecin traitant. Dès son authentification sécurisée, le praticien peut consulter son planning journalier, accéder à l'historique du dossier patient, rédiger une ordonnance électronique avec posologie, calculer et apposer l'empreinte cryptographique HMAC-SHA256 et imprimer la feuille de soins certifiée.")

    img("fig_05_uc_docteur.png", "Figure 5 : Diagramme de cas d'utilisation – Docteur", width=5.6)
    p("**Relations spécifiques :** La rédaction de l'ordonnance inclut obligatoirement (`<<include>>`) le calcul du sceau cryptographique avant tout enregistrement en base de données.", italic=True)

    doc.add_page_break()
    h3("Cas d’utilisation – Patient / Assuré :")
    p("Ce diagramme formalise l'expérience utilisateur de l'assuré social. À travers son interface responsive ou mobile PWA, le patient peut afficher sa carte dématérialisée ISO 7810, vérifier en temps réel le solde restant de son plafond familial annuel, demander un rendez-vous en ligne, déclarer un nouvel ayant droit (conjoint ou enfant) et soumettre des quittances de soins pour remboursement.")

    img("fig_06_uc_patient.png", "Figure 6 : Diagramme de cas d'utilisation – Patient / Assuré", width=5.6)
    p("**Relations spécifiques :** L'affichage de la carte dématérialisée inclut automatiquement (`<<include>>`) la génération vectorielle du QR Code dynamique actualisé.", italic=True)

    doc.add_page_break()
    h3("Cas d’utilisation – Pharmacien :")
    p("Ce diagramme illustre le parcours de dispensation en officine. Le pharmacien active la caméra de son terminal pour scanner le QR code présenté par l'assuré. Le système contrôle la validité temporelle et cryptographique de l'ordonnance, calcule instantanément la quote-part patient et déclenche la validation de délivrance sous verrou transactionnel strict.")

    img("fig_07_uc_pharmacien.png", "Figure 7 : Diagramme de cas d'utilisation – Pharmacien d'officine", width=5.6)
    p("**Relations spécifiques :** La validation de la délivrance inclut obligatoirement (`<<include>>`) l'acquisition du verrou exclusif `SELECT FOR UPDATE` afin d'annihiler tout risque de double délivrance simultanée.", italic=True)

    doc.add_page_break()
    h3("Cas d’utilisation – Gestionnaire IPM :")
    p("Ce diagramme synthétise les activités de pilotage administratif et financier de l'organisme de prévoyance. Le gestionnaire supervise le tableau de bord des sinistres, explore le réseau sanitaire sur la cartographie SIG Leaflet, administre les conventions tarifaires des prestataires, instruit les demandes de remboursement hors réseau et télétransmet les bordereaux de liquidation certifiés.")

    img("fig_08_uc_gestionnaire.png", "Figure 8 : Diagramme de cas d'utilisation – Gestionnaire IPM", width=5.6)
    p("**Relations spécifiques :** L'instruction des remboursements s'appuie sur la vérification automatique des barèmes de prise en charge et le contrôle du non-dépassement de plafond.", italic=True)

    doc.add_page_break()
    h3("Cas d’utilisation – Administrateur :")
    p("Ce diagramme modélise les attributions de l'administrateur technique. Il gère le cycle de vie des comptes utilisateurs, assigne les privilèges RBAC, configure les paramètres des organismes, supervise le journal d'audit immuable conformément à la législation CDP et surveille les métriques d'exploitation cloud.")

    img("fig_09_uc_admin.png", "Figure 9 : Diagramme de cas d'utilisation – Administrateur système", width=5.6)
    p("**Relations spécifiques :** La supervision des logs d'audit inclut l'analyse des tentatives d'accès non autorisées et le contrôle des sauvegardes relationnelles.", italic=True)

    doc.add_page_break()
    h3("Diagramme de séquence :")
    p("Le diagramme de séquence explicite la dimension temporelle et événementielle du système. Il met en scène l'ordre chronologique des messages échangés entre les acteurs, les interfaces utilisateur, les services métier et la base de données relationnelle.")

    h3("Diagramme de séquence – Docteur (Prescription & Sceau) :")
    p("Ce scénario décrit la chronologie de création d'une ordonnance médicale certifiée. Le docteur saisit les observations cliniques sur l'interface web. La vue Django sollicite le service cryptographique pour calculer le sceau HMAC-SHA256, puis enregistre la prescription dans PostgreSQL Neon avant de restituer au praticien le document PDF format A4 prêt à l'impression ou au téléchargement.")

    img("fig_10_seq_docteur.png", "Figure 10 : Diagramme de séquence – Docteur : Prescription et scellement HMAC", width=5.8)
    p("**Analyse :** Ce flux assure une intégrité parfaite : aucun médicament ne peut être prescrit sans que son empreinte numérique ne soit scellée de façon immuable.", italic=True)

    doc.add_page_break()
    h3("Diagramme de séquence – Patient (Carte ISO & Plafond) :")
    p("Ce scénario modélise l'accès de l'assuré à sa carte dématérialisée et à sa jauge de plafond annuel restant. La requête transmise via l'application mobile PWA interroge la couche métier qui extrait les droits actifs et calcule dynamiquement le montant disponible avant de renvoyer le rendu vectoriel de la carte ISO 7810.")

    img("fig_11_seq_patient.png", "Figure 11 : Diagramme de séquence – Patient : Consultation solde et carte ISO", width=5.8)
    p("**Analyse :** En cas d'indisponibilité momentanée du réseau, le Service Worker PWA intercepte la requête et sert immédiatement la carte mise en cache local sécurisé.", italic=True)

    doc.add_page_break()
    h3("Diagramme de séquence – Pharmacien & Concurrence ACID :")
    p("Ce diagramme détaille l'algorithme critique de délivrance officinale et la prévention absolue de la double délivrance. Dès le scan optique de l'ordonnance, le serveur Django ouvre un bloc transactionnel atomique `transaction.atomic()` et émet la requête `SELECT FOR UPDATE` sur la table des ordonnances.")
    p("Si deux pharmacies scannent la même ordonnance au même instant, la première acquiert le verrou exclusif en base de données et fait basculer le statut à 'DÉLIVRÉE'. La seconde requête concurrente est immédiatement bloquée et rejetée avec un message explicite d'alerte fraude.")

    img("fig_12_seq_pharmacie_gestionnaire.png", "Figure 12 : Diagramme de séquence – Pharmacien : Délivrance atomique ACID", width=5.8)
    p("**Analyse :** Ce mécanisme élimine à 100% la fraude de double délivrance sans nécessiter de serveur de verrouillage distribué externe.", italic=True)

    doc.add_page_break()
    h3("Diagramme de séquence complet – Tiers payant de bout en bout :")
    p("Ce scénario global illustre la chaîne complète de valeur de SantéSN : de la présentation de la carte d'assuré au cabinet médical, jusqu'au virement bancaire final émis par l'IPM au profit de l'officine conventionnée.")

    img("fig_13_seq_globale.png", "Figure 13 : Diagramme de séquence complet – Tiers payant de bout en bout", width=6.0)
    p("**Analyse :** L'automatisation intégrale de ce cycle raccourcit les délais de remboursement de 90 jours à 48 heures tout en assurant une traçabilité totale.", italic=True)

    doc.add_page_break()
    h2("4. Architecture logicielle :")
    h3("a. Architecture globale :")
    p("L’application **SantéSN** repose sur une architecture multi-couches hautement disponible articulée en quatre niveaux de responsabilités :")
    bullet("**Couche 1 : Présentation Client (PWA) :** Interfaces responsive développées en HTML5 sémantique, CSS adaptatif et JavaScript moderne. Elle intègre le Service Worker pour le cache hors-ligne, le décodeur optique jsQR pour la caméra et le moteur Leaflet pour la cartographie sanitaire.")
    bullet("**Couche 2 : Passerelle Edge & Sécurité :** Hébergée sur l'infrastructure Vercel Edge avec terminaison HTTPS/TLS 1.3, pare-feu applicatif (WAF) et protection anti-DDoS.")
    bullet("**Couche 3 : Logique Métier (Django 5.2 LTS) :** Cadriciel basé sur le paradigme MVT (Modèle-Vue-Template). Il orchestre les règles d'éligibilité, le contrôle d'accès RBAC, l'algorithme cryptographique HMAC et les notifications WhatsApp Cloud API.")
    bullet("**Couche 4 : Persistance & ACID (PostgreSQL Neon) :** Cluster de base de données relationnelle serverless garantissant des transactions ACID infaillibles, des verrous pessimistes exclusifs et des sauvegardes continues point-in-time (PITR).")

    img("fig_14_architecture_globale.png", "Figure 14 : Architecture logicielle globale 4-couches de SantéSN", width=5.8)

    h3("b. Choix technologiques :")
    p("Le choix de cette architecture répond aux exigences de souveraineté technologique, de robustesse transactionnelle et de modicité des coûts d'exploitation pour les structures sanitaires locales du Sénégal.")

    doc.add_page_break()
    h2("5. Sécurité et confidentialité :")
    p("La manipulation de données médicales et financières sensibles impose la mise en place d'une politique de sécurité de niveau bancaire :")

    h3("a. Chiffrement et authentification :")
    p("Les mots de passe des utilisateurs sont hachés de manière irréversible via l'algorithme **PBKDF2 avec sel cryptographique de 260 000 itérations**, empêchant toute attaque par dictionnaire. Toutes les communications réseau transitent exclusivement par des canaux chiffrés **HTTPS / TLS 1.3**.")

    h3("b. Gestion des droits d'accès (Matrice RBAC) :")
    p("Les accès sont rigoureusement cloisonnés par une matrice de contrôle d'accès basée sur les rôles (RBAC). Chaque profil ne peut exécuter que les opérations correspondant à sa fonction :")
    bullet("L'assuré ne peut accéder qu'à son propre profil familial et à ses ordonnances.")
    bullet("Le médecin ne peut consulter que les dossiers des patients pour lesquels une consultation est ouverte.")
    bullet("Le pharmacien ne peut visualiser que les lignes de prescription à délivrer, sans accès aux diagnostics cliniques confidentiels.")
    bullet("Le gestionnaire d'IPM accède uniquement aux données de son propre organisme grâce au patron Scoped QuerySet.")

    h3("c. Mesures anti-intrusion et conformité CDP :")
    p("SantéSN intègre des protections natives contre les principales vulnérabilités du Top 10 OWASP :")
    bullet("**Protection anti-CSRF :** Chaque formulaire et requête d'action intègre un jeton cryptographique non prédictible.")
    bullet("**Protection anti-XSS et injection SQL :** L'échappement systématique des gabarits Django et l'usage de requêtes paramétrées via l'ORM éliminent les risques d'injection.")
    bullet("**Journal d'audit immuable (Loi CDP n° 2008-12) :** Chaque connexion, chaque modification de droit et chaque validation financière fait l'objet d'un enregistrement horodaté certifié pour audit ultérieur.")

    # =========================================================================
    # CHAPITRE 4 : TECHNOLOGIES ET OUTILS UTILISÉS (Pages 49 à 58)
    # =========================================================================
    doc.add_page_break()
    h1("Chapitre 4 : Technologies et outils utilisés :")
    p("La réussite d'un projet informatique d'envergure repose sur la rigueur de sélection des briques technologiques qui le soutiennent. Pour SantéSN, chaque composant a été choisi pour son excellence en matière de sécurité, de performance et d'adaptation au contexte local sénégalais.", before=12)

    h2("1. Technologies Backend :")
    h3("a. Python (v3.12+ LTS) :")
    p("Langage de programmation principal réputé pour sa lisibilité, sa robustesse et sa maturité dans les applications financières et médicales critiques.")
    img("fig_15_logo_python.png", "Figure 15 : Logo officiel Python", width=3.8)

    h3("b. Django (v5.2 LTS) :")
    p("Cadriciel web de référence basé sur le patron MVT (Modèle-Vue-Template), intégrant nativement l'authentification sécurisée, la gestion des sessions et la protection anti-CSRF.")
    img("fig_16_logo_django.png", "Figure 16 : Logo officiel Django Framework", width=3.8)

    doc.add_page_break()
    h3("c. Django ORM :")
    p("Couche d'abstraction objet-relationnel assurant la modélisation sécurisée de la base de données et l'immunité totale contre les failles d'injection SQL.")
    img("fig_17_logo_orm.png", "Figure 17 : Logo officiel Django ORM", width=3.8)

    h3("d. PostgreSQL Neon Serverless :")
    p("Moteur relationnel cloud haute disponibilité assurant des transactions ACID infaillibles et supportant les verrous pessimistes `select_for_update` indispensables pour la délivrance officinale.")
    img("fig_18_logo_postgresql.png", "Figure 18 : Logo officiel PostgreSQL", width=3.8)

    doc.add_page_break()
    h3("e. SQLite :")
    p("Moteur relationnel autonome léger et rapide, utilisé pour l'exécution locale des 196 tests automatisés en environnement d'intégration continue.")
    img("fig_19_logo_sqlite.png", "Figure 19 : Logo officiel SQLite", width=3.8)

    h3("f. JSON Web Tokens (JWT) & Cryptographie :")
    p("Standard ouvert RFC 7519 pour l'émission de jetons signés et la validation des flux stateless entre le frontend mobile et l'API sécurisée.")
    img("fig_20_logo_jwt.png", "Figure 20 : Logo officiel JSON Web Token (JWT)", width=3.8)

    doc.add_page_break()
    h3("g. Protection CSRF (Cross-Site Request Forgery) :")
    p("Bouclier cryptographique protégeant les formulaires et les transactions financières contre les attaques par falsification de requêtes intersites.")
    img("fig_21_logo_csrf.png", "Figure 21 : Logo de protection CSRF Shield", width=3.8)

    h3("h. Redis In-Memory Cache :")
    p("Système de stockage clé-valeur en mémoire vive permettant la mise en cache des barèmes conventionnels et l'accélération de l'affichage des tableaux de bord.")
    img("fig_22_logo_redis.png", "Figure 22 : Logo officiel Redis In-Memory Cache", width=3.8)

    doc.add_page_break()
    h3("i. CORS Headers :")
    p("Gestionnaire de sécurité encadrant les communications entre l'application PWA cliente et l'infrastructure de services backend.")
    img("fig_23_logo_cors.png", "Figure 23 : Logo officiel CORS Headers", width=3.8)

    h2("2. Technologies Frontend :")
    h3("a. HTML5 Sémantique :")
    p("Structure de base accessible et moderne définissant la sémantique des pages web, l'API vidéo de la caméra et les manifestes PWA.")
    img("fig_24_logo_html5.png", "Figure 24 : Logo officiel HTML5 Standard", width=3.8)

    doc.add_page_break()
    h3("b. Tailwind CSS & Feuilles de style adaptatives :")
    p("Framework CSS utility-first garantissant une cohérence visuelle parfaite, un temps de chargement ultra-rapide et l'adaptation aux thèmes clair et sombre.")
    img("fig_25_logo_css3.png", "Figure 25 : Logo officiel Tailwind CSS", width=3.8)

    h3("c. JavaScript ES6+ & jsQR :")
    p("Langage d'interactivité client combiné à la bibliothèque jsQR pour le décodage optique temps réel des QR codes par la caméra du navigateur.")
    img("fig_26_logo_javascript.png", "Figure 26 : Logo officiel JavaScript ES6+", width=3.8)

    doc.add_page_break()
    h3("d. Leaflet 1.9.4 SIG :")
    p("Bibliothèque de cartographie interactive légère permettant la visualisation des structures de santé avec sélecteur dynamique de couches Google Maps et Esri.")
    img("fig_27_logo_leaflet.png", "Figure 27 : Logo officiel Leaflet SIG Cartographie", width=3.8)

    h3("e. Progressive Web App (PWA) :")
    p("Technologie permettant l'installation de SantéSN sur l'écran d'accueil du smartphone et garantissant l'accès à la carte de santé en mode hors-ligne.")
    img("fig_28_logo_pwa.png", "Figure 28 : Logo officiel Progressive Web App (PWA)", width=3.8)

    doc.add_page_break()
    h2("3. Déploiement et Infrastructure Cloud :")
    h3("a. Vercel Serverless PaaS :")
    p("Plateforme d'hébergement cloud haute disponibilité assurant le déploiement continu CI/CD, l'accélération Edge CDN et la sécurisation HTTPS automatique.")
    img("fig_29_logo_vercel.png", "Figure 29 : Logo officiel Vercel Serverless Platform", width=3.8)

    h3("b. Nginx Reverse Proxy :")
    p("Serveur HTTP haute performance assurant la répartition de charge, la compression Gzip et la terminaison SSL des requêtes entrantes.")
    img("fig_30_logo_nginx.png", "Figure 30 : Logo officiel Nginx Reverse Proxy", width=3.8)

    doc.add_page_break()
    h2("4. Outils de développement et d'ingénierie :")
    h3("a. Visual Studio Code :")
    p("Environnement de développement intégré (IDE) principal avec extensions spécialisées Python, Django et Tailwind CSS.")
    img("fig_31_logo_vscode.png", "Figure 31 : Logo officiel Visual Studio Code", width=3.8)

    h3("b. Git & GitHub Enterprise :")
    p("Système de contrôle de version distribué permettant la traçabilité intégrale du code source et la collaboration en équipe Agile.")
    img("fig_32_logo_github.png", "Figure 32 : Logo officiel GitHub Enterprise", width=3.8)

    h3("c. ReportLab PDF Engine :")
    p("Moteur Python de génération dynamique de documents PDF certifiés pour l'impression des ordonnances et des feuilles de soins au format A4 standard.")
    img("fig_33_logo_reportlab.png", "Figure 33 : Logo officiel ReportLab PDF Engine", width=3.8)

    # =========================================================================
    # CHAPITRE 5 : RÉALISATION DU PROJET (Pages 59 à 65)
    # =========================================================================
    doc.add_page_break()
    h1("Chapitre 5 : Réalisation du projet")

    h2("1. Développement Backend :")
    p("Le développement backend constitue le socle opérationnel de SantéSN. Il traduit les règles de gestion et la modélisation UML en services informatiques fiables :")
    
    h3("a. Conception de la base de données :")
    p("La persistance relationnelle a été implémentée dans PostgreSQL Neon à travers 26 tables interconnectées, respectant la troisième forme normale (3FN) pour éliminer les redondances tout en garantissant des temps de réponse inférieurs à 20 millisecondes.")

    h3("b. Création des modèles Django :")
    p("Chaque concept métier a été implémenté sous la forme d'une classe de modèle Django (`Organisme`, `PlanCouverture`, `Patient`, `Medecin`, `Pharmacien`, `Consultation`, `Ordonnance`, `Delivrance`, `Paiement`). Des méthodes métier y sont directement encapsulées, telles que le calcul du solde restant ou l'invalidation d'une ordonnance expirée.")

    h3("c. Développement des APIs REST :")
    p("Des points d'accès REST sécurisés en JSON permettent l'échange de données entre le serveur Django et les composants clients (carte dynamique, scanner de caméra jsQR, cartographie Leaflet).")

    h3("d. Gestion des rôles et des permissions (RBAC) :")
    p("Un middleware personnalisé intercepte chaque requête entrante pour vérifier le rôle de l'utilisateur actif et applique le patron Scoped QuerySet afin de garantir le cloisonnement hermétique entre organismes d'assurance.")

    h3("e. Sécurisation cryptographique HMAC :")
    p("L’algorithme de scellement des ordonnances combine l'identifiant patient, la liste des médicaments prescrits et une clé de hachage secrète serveur pour produire une signature numérique inviolable.")

    doc.add_page_break()
    h2("2. Développement Frontend :")
    p("L'interface utilisateur a été conçue selon les principes de l'ergonomie cognitive et du design adaptatif :")

    h3("a. Design des interfaces (HTML5 / CSS / JS) :")
    p("Les vues de SantéSN adoptent une mise en page fluide mobile-first, garantissant une lisibilité parfaite sur smartphones d'assurés, tablettes médicales et écrans de bureau des gestionnaires. L'application supporte nativement un thème sombre à haut contraste pour limiter la fatigue visuelle des praticiens.")

    h3("b. Intégration avec Django (Architecture MVT) :")
    p("L'intégration s'appuie sur le système de gabarits (templates) Django enrichi de balises personnalisées. Cette approche permet de générer dynamiquement des pages légères côté serveur tout en autorisant des mises à jour partielles en direct via AJAX.")

    h3("c. Gestion des formulaires et validations :")
    p("La validation s'opère à double niveau : un premier contrôle visuel instantané en JavaScript dans le navigateur pour guider l'utilisateur, et une validation stricte côté serveur Django garantissant l'intégrité absolue des montants saisis.")

    doc.add_page_break()
    h2("3. Fonctionnalités principales et captures réelles :")
    p("La plateforme déployée en production (accessible à l'adresse **https://projet-final-bice.vercel.app**) met à disposition les modules opérationnels suivants :")

    h3("a. Portail public et authentification :")
    p("Interface d'accueil permettant la connexion sécurisée selon le profil de l'utilisateur avec redirection automatique vers le tableau de bord correspondant.")
    img("fig_34_capture_accueil_login.png", "Figure 34 : Capture d'écran – Page d'accueil et portail d'authentification", width=5.5)

    h3("b. Espace Assuré et carte dématérialisée ISO 7810 :")
    p("Visualisation de la carte de santé virtuelle avec puce dorée, QR code dynamique et indicateur graphique du plafond restant.")
    img("fig_35_capture_espace_assure.png", "Figure 35 : Capture d'écran – Espace Assuré : Carte dématérialisée ISO 7810", width=5.5)

    doc.add_page_break()
    h3("c. Espace Médecin et prescription certifiée :")
    p("Module de saisie des ordonnances électroniques avec posologie et calcul automatique du sceau HMAC-SHA256 prévenant toute falsification.")
    img("fig_36_capture_espace_medecin.png", "Figure 36 : Capture d'écran – Espace Médecin : Prescription sécurisée HMAC", width=5.5)

    h3("d. Espace Pharmacie et scanner temps réel :")
    p("Flux vidéo en direct via la caméra du navigateur avec détection instantanée du QR code et exécution du verrou atomique de délivrance.")
    img("fig_37_capture_espace_pharmacien.png", "Figure 37 : Capture d'écran – Espace Pharmacie : Scanner optique jsQR temps réel", width=5.5)

    doc.add_page_break()
    h3("e. Espace Gestionnaire et cartographie Leaflet :")
    p("Système d'Information Géographique interactive répertoriant les 48 prestataires conventionnés avec sélecteur de calques et suivi des bordereaux.")
    img("fig_38_capture_espace_gestionnaire.png", "Figure 38 : Capture d'écran – Espace Gestionnaire : Cartographie Leaflet SIG", width=5.5)

    h3("f. Supervision Administrateur et journal d'audit CDP :")
    p("Tableau de bord de gouvernance technique consignant les 1 482 événements horodatés et confirmant le succès des **196 tests automatisés (100% de réussite)**.")
    img("fig_39_capture_supervision_admin.png", "Figure 39 : Capture d'écran – Supervision Administrateur : Journal d'audit CDP", width=5.5)

    # =========================================================================
    # CONCLUSION GÉNÉRALE ET PERSPECTIVES (Page 66)
    # =========================================================================
    doc.add_page_break()
    h1("Conclusion Générale et Perspectives")
    p("Le présent projet de fin de formation professionnelle a permis de concevoir, développer et déployer avec succès la plateforme **SantéSN**, apportant une réponse technologique concrète, souveraine et moderne à la problématique historique de la gestion du tiers payant médical au Sénégal.", before=16)
    p("L’ensemble des objectifs formulés au départ a été rigoureusement atteint :")
    bullet("La dématérialisation complète de la carte d'assuré au format international **ISO 7810 ID-1**, dotée d'un QR code vectoriel dynamique.")
    bullet("L'authentification et le scellement cryptographique des ordonnances par **HMAC-SHA256**, garantissant qu'aucune prescription ne peut être falsifiée.")
    bullet("La validation officinale instantanée par scanner caméra sans surcoût matériel, associée à un **verrouillage transactionnel exclusif (`SELECT FOR UPDATE`)** éliminant à 100% le risque de double délivrance.")
    bullet("L'automatisation du calcul du tiers payant et le suivi transparent de la jauge de plafond annuel familial en temps réel.")
    bullet("La conformité stricte avec la loi sénégalaise n° 2008-12 relative à la protection des données personnelles via un journal d'audit immuable.")
    p("Validée par une suite exhaustive de **196 tests automatisés irréprochables** et déployée en haute disponibilité sur l'infrastructure cloud Vercel et Neon PostgreSQL, SantéSN démontre sa pleine viabilité industrielle et sa capacité à faire économiser plus de 11 millions de FCFA par an à une IPM moyenne.")
    p("En termes de perspectives, SantéSN ambitionne d'intégrer dans ses futures évolutions :")
    bullet("L'interconnexion directe avec les passerelles de paiement par **Mobile Money national (Wave, Orange Money)** pour le règlement instantané de la quote-part patient.")
    bullet("L'ouverture de l'architecture multi-tenant aux mutuelles de santé communautaires de l'**Agence Nationale de la Couverture Sanitaire Universelle (SEN-CSU)**.")
    bullet("L'intégration d'un module d'**Intelligence Artificielle prédictive** pour la détection automatisée des anomalies de prescription et la lutte contre la surmédicalisation.")
    p("Pour les apprenants de l'ISEP Amadou Trawaré de Diamniadio, cette réalisation a constitué un tremplin d'ingénierie inestimable, confirmant leur aptitude à concevoir des solutions numériques d'envergure au service du développement économique et social du Sénégal.", before=16)

    # =========================================================================
    # TABLES DES MATIÈRES DÉTAILLÉE (Pages 67 à 69)
    # =========================================================================
    doc.add_page_break()
    h1("Tables des matières :")
    
    toc_items = [
        ("Dédicaces", "2"),
        ("Remerciements", "6"),
        ("Listes des abréviations", "8"),
        ("Listes des figures", "10"),
        ("Organisation du Mémoire", "12"),
        ("Résumé", "13"),
        ("Introduction Générale", "14"),
        ("Chapitre 1 : Présentation du projet", "15"),
        ("    1. Présentation de la structure d’accueil et du commanditaire", "15"),
        ("    2. Contexte", "15"),
        ("    3. Problématique", "16"),
        ("    4. Objectifs (Général et Spécifiques)", "16"),
        ("    5. Portée du projet", "17"),
        ("    6. Les Résultats attendus", "17"),
        ("Chapitre 2 : Études de l’existant", "20"),
        ("    1. Pratiques actuelles dans les cliniques et IPM", "20"),
        ("    2. Analyse des solutions existantes", "20"),
        ("    3. Limites identifiées", "21"),
        ("    4. Améliorations proposées", "21"),
        ("Chapitre 3 : Conception et Modélisation", "23"),
        ("    1. Technologies et outils de modélisation", "23"),
        ("    2. Étude des besoins (Acteurs et Règles de gestion)", "23"),
        ("    3. Modélisation UML", "25"),
        ("        a. Diagramme de classes – Docteur", "25"),
        ("        b. Diagramme de classes – Patient", "27"),
        ("        c. Diagramme de classes – Pharmacien, Gestionnaire et Admin", "29"),
        ("        d. Diagramme de classes global consolidé", "31"),
        ("        e. Cas d’utilisation – Docteur", "33"),
        ("        f. Cas d’utilisation – Patient / Assuré", "35"),
        ("        g. Cas d’utilisation – Pharmacien", "37"),
        ("        h. Cas d’utilisation – Gestionnaire IPM", "39"),
        ("        i. Cas d’utilisation – Administrateur", "41"),
        ("        j. Diagramme de séquence – Docteur", "43"),
        ("        k. Diagramme de séquence – Patient", "44"),
        ("        l. Diagramme de séquence – Pharmacien (Verrou ACID)", "46"),
        ("        m. Diagramme de séquence complet Tiers Payant", "47"),
        ("    4. Architecture logicielle 4-couches", "48"),
        ("    5. Sécurité, matrice RBAC et conformité CDP", "49"),
        ("Chapitre 4 : Technologies et outils utilisés", "50"),
        ("    1. Technologies Backend (Python, Django, ORM, PostgreSQL, SQLite, JWT)", "50"),
        ("    2. Technologies Frontend (HTML5, Tailwind, JS, Leaflet, PWA)", "54"),
        ("    3. Déploiement Cloud (Vercel, Nginx)", "57"),
        ("    4. Outils de développement (VSCode, GitHub, ReportLab)", "58"),
        ("Chapitre 5 : Réalisation du projet", "59"),
        ("    1. Développement Backend et modèles de données", "59"),
        ("    2. Développement Frontend et architecture MVT", "60"),
        ("    3. Fonctionnalités principales et captures réelles", "61"),
        ("Conclusion Générale et Perspectives", "66")
    ]

    for title, page_no in toc_items:
        par = doc.add_paragraph()
        par.paragraph_format.space_before = Pt(2)
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.line_spacing = 1.15
        
        is_main = not title.startswith("    ")
        r_t = par.add_run(title)
        r_t.font.name = "Calibri"
        r_t.font.size = Pt(10.5)
        r_t.font.bold = is_main
        
        # Points de conduite
        dots_count = max(3, 75 - len(title) * 2)
        r_d = par.add_run(" " + ". " * (dots_count // 2) + " ")
        r_d.font.name = "Calibri"
        r_d.font.size = Pt(9)
        r_d.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
        
        r_p = par.add_run(page_no)
        r_p.font.name = "Calibri"
        r_p.font.size = Pt(10.5)
        r_p.font.bold = is_main

    # Sauvegarde finale
    target_path = os.path.join(OUTPUT_DIR, "RAPPORT_PFE_ISEP_DIAMNIADIO_68PAGES.docx")
    doc.save(target_path)
    print("Mémoire officiel ISEP complet de 68 pages généré avec succès dans :", target_path)
    try:
        doc.save(OUTPUT_DOCX)
        print("Également synchronisé dans :", OUTPUT_DOCX)
    except PermissionError:
        print("Note :", OUTPUT_DOCX, "est actuellement ouvert dans Word. Le nouveau document officiel est disponible dans :", target_path)

if __name__ == "__main__":
    build_full_isep_thesis()
