"""Pages publiques : vitrine, politique de confidentialité, CGU, robots.txt, sitemap.xml."""

from django.http import HttpResponse
from django.shortcuts import render


def landing(request):
    """Page d'accueil publique de SantéSN (vitrine)."""
    return render(request, "landing.html")


def politique_confidentialite(request):
    """Politique de protection des données et de confidentialité (Loi 2008-12 / CDP & RGPD)."""
    return render(request, "politique_confidentialite.html")


def cgu(request):
    """Conditions Générales d'Utilisation de la plateforme SantéSN."""
    return render(request, "cgu.html")


def robots_txt(request):
    """Robots.txt médical durci : interdiction stricte d'indexer les dossiers médicaux et espaces privés."""
    lignes = [
        "User-agent: *",
        "Allow: /$",
        "Allow: /politique-confidentialite/$",
        "Allow: /cgu/$",
        "Disallow: /admin/",
        "Disallow: /espace/",
        "Disallow: /tableau-de-bord/",
        "Disallow: /rapports/",
        "Disallow: /journal/",
        "Disallow: /connexion/",
        "Disallow: /deconnexion/",
        "Disallow: /installation/",
        "Disallow: /parametres/",
        "Disallow: /mon-compte/",
        "Disallow: /utilisateurs/",
        "Disallow: /patients/",
        "Disallow: /patient/",
        "Disallow: /medecins/",
        "Disallow: /medecin/",
        "Disallow: /pharmaciens/",
        "Disallow: /pharmacien/",
        "Disallow: /assure/",
        "Disallow: /assures/",
        "Disallow: /prestataires/",
        "Disallow: /services/",
        "Disallow: /rendez-vous/",
        "Disallow: /consultations/",
        "Disallow: /ordonnances/",
        "Disallow: /prises-en-charge/",
        "Disallow: /paiements/",
        "Disallow: /api/",
        "Disallow: /media/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
        "",
    ]
    return HttpResponse("\n".join(lignes), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    """Sitemap XML exposant uniquement les pages publiques d'information et légales."""
    urls = [
        ("/", "1.0", "weekly"),
        ("/politique-confidentialite/", "0.6", "monthly"),
        ("/cgu/", "0.6", "monthly"),
    ]
    xml_items = []
    for chemin, priorite, frequence in urls:
        uri = request.build_absolute_uri(chemin)
        xml_items.append(
            f"  <url>\n"
            f"    <loc>{uri}</loc>\n"
            f"    <changefreq>{frequence}</changefreq>\n"
            f"    <priority>{priorite}</priority>\n"
            f"  </url>"
        )
    corps = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(xml_items)
        + "\n</urlset>\n"
    )
    return HttpResponse(corps, content_type="application/xml; charset=utf-8")

