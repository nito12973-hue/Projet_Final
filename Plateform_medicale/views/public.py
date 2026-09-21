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


def logo_dark_svg(request):
    """Logo officiel SantéSN (texte sombre pour fond clair)."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 36" fill="none">'
        '<g transform="translate(0, 2)">'
        '<rect x="12" y="4" width="8" height="24" rx="3" fill="#0E7C86"/>'
        '<rect x="4" y="12" width="24" height="8" rx="3" fill="#0E7C86"/>'
        '<path d="M4 16H9.3L11.3 10.7L14 21.3L16.7 12.7L18.3 16H28" fill="none" '
        'stroke="#E0824F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</g>'
        '<text x="38" y="24" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" '
        'font-size="20" font-weight="800" fill="#0B2027" letter-spacing="-0.4">'
        'Santé<tspan fill="#0E7C86">SN</tspan></text>'
        '</svg>'
    )
    resp = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
    resp["Cache-Control"] = "public, max-age=86400"
    return resp


def logo_light_svg(request):
    """Logo officiel SantéSN (texte clair pour fond sombre)."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 36" fill="none">'
        '<g transform="translate(0, 2)">'
        '<rect x="12" y="4" width="8" height="24" rx="3" fill="#4FB8AE"/>'
        '<rect x="4" y="12" width="24" height="8" rx="3" fill="#4FB8AE"/>'
        '<path d="M4 16H9.3L11.3 10.7L14 21.3L16.7 12.7L18.3 16H28" fill="none" '
        'stroke="#E0824F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</g>'
        '<text x="38" y="24" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" '
        'font-size="20" font-weight="800" fill="#FFFFFF" letter-spacing="-0.4">'
        'Santé<tspan fill="#4FB8AE">SN</tspan></text>'
        '</svg>'
    )
    resp = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
    resp["Cache-Control"] = "public, max-age=86400"
    return resp


def favicon_svg(request):
    """Favicon SVG officiel de SantéSN."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">'
        '<rect x="18" y="6" width="12" height="36" rx="4" fill="#0E7C86"/>'
        '<rect x="6" y="18" width="36" height="12" rx="4" fill="#0E7C86"/>'
        '<path d="M6 24H14L17 16L21 32L25 19L27.5 24H42" fill="none" '
        'stroke="#E0824F" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    resp = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
    resp["Cache-Control"] = "public, max-age=86400"
    return resp

