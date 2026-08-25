"""Pages publiques : landing, robots.txt, sitemap.xml."""

from django.http import HttpResponse
from django.shortcuts import render

def landing(request):
    """Page d'accueil publique de SantéSN (vitrine)."""
    return render(request, "landing.html")

def robots_txt(request):
    """Une seule page publique (landing) : tout le reste (espaces authentifies)
    n'a pas vocation a etre indexe."""
    contenu = (
        "User-agent: *\n"
        "Allow: /$\n"
        "Disallow: /\n\n"
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}\n"
    )
    return HttpResponse(contenu, content_type="text/plain")

def sitemap_xml(request):
    contenu = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{request.build_absolute_uri('/')}</loc>"
        "<changefreq>monthly</changefreq><priority>1.0</priority></url>\n"
        "</urlset>\n"
    )
    return HttpResponse(contenu, content_type="application/xml")

