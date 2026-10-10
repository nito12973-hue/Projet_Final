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
    """Logo officiel SantéSN pour mode sombre (texte blanc pour fond sombre)."""
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
    resp["Cache-Control"] = "public, max-age=3600"
    return resp


def logo_light_svg(request):
    """Logo officiel SantéSN pour mode clair (texte sombre pour fond clair)."""
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
    resp["Cache-Control"] = "public, max-age=3600"
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


# ---------------------------------------------------------------------------
# Axe 3 : PWA (Progressive Web App) & Mode Carte Hors-Ligne
# ---------------------------------------------------------------------------

def manifest_json(request):
    """Manifest officiel PWA permettant l'installation de SantéSN sur mobile."""
    manifest = {
        "name": "SantéSN — Tiers-Payant & Carte Numérique",
        "short_name": "SantéSN",
        "description": "Système national de tiers-payant, carte d'assuré dématérialisée et ordonnance médicale sécurisée.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "theme_color": "#0E7C86",
        "background_color": "#0B2027",
        "lang": "fr-SN",
        "icons": [
            {
                "src": "/favicon.svg",
                "sizes": "48x48 72x72 96x96 128x128 192x192 256x256 512x512",
                "type": "image/svg+xml",
                "purpose": "any",
            },
            {
                "src": "/favicon.svg",
                "sizes": "192x192 512x512",
                "type": "image/svg+xml",
                "purpose": "maskable",
            },
        ],
    }
    import json
    corps = json.dumps(manifest, ensure_ascii=False, indent=2)
    resp = HttpResponse(corps, content_type="application/manifest+json; charset=utf-8")
    resp["Cache-Control"] = "public, max-age=86400"
    return resp


def service_worker_js(request):
    """Service Worker PWA avec mise en cache locale et résilience hors-ligne pour la carte d'assuré."""
    js = """
const CACHE_NAME = 'santesn-pwa-v1';
const RESSOURCES_ESSENTIELLES = [
    '/',
    '/offline/',
    '/manifest.json',
    '/favicon.svg',
    '/logo-dark.svg',
    '/logo-light.svg',
    '/assure/carte/',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(RESSOURCES_ESSENTIELLES).catch(() => {});
        }).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((noms) => {
            return Promise.all(
                noms.map((nom) => {
                    if (nom !== CACHE_NAME) {
                        return caches.delete(nom);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    const url = new URL(event.request.url);

    // 1. Stratégie Stale-While-Revalidate pour la carte d'assuré et les médias vectoriels
    if (url.pathname.includes('/carte') || url.pathname.endsWith('.svg') || url.pathname.includes('/static/')) {
        event.respondWith(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.match(event.request).then((reponseEnCache) => {
                    const fetchPromise = fetch(event.request).then((reponseReseau) => {
                        if (reponseReseau && reponseReseau.status === 200) {
                            cache.put(event.request, reponseReseau.clone());
                        }
                        return reponseReseau;
                    }).catch(() => reponseEnCache);
                    return reponseEnCache || fetchPromise;
                });
            })
        );
        return;
    }

    // 2. Stratégie Réseau avec repli sur le cache pour la navigation
    event.respondWith(
        fetch(event.request)
            .then((reponseReseau) => {
                if (reponseReseau.status === 200 && event.request.mode === 'navigate') {
                    const clone = reponseReseau.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return reponseReseau;
            })
            .catch(() => {
                return caches.match(event.request).then((trouve) => {
                    if (trouve) return trouve;
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline/');
                    }
                    return new Response('Connexion réseau indisponible.', {
                        status: 503,
                        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                    });
                });
            })
    );
});
"""
    resp = HttpResponse(js.strip(), content_type="application/javascript; charset=utf-8")
    resp["Service-Worker-Allowed"] = "/"
    resp["Cache-Control"] = "public, max-age=3600"
    return resp


def offline_view(request):
    """Page affichée lors d'une perte totale de connectivité réseau."""
    return render(request, "offline.html")


