from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Icones de navigation en trait fin (24x24, stroke uniquement, sans dependance
# externe). Une seule source pour toute l'application : voir base.html.
_ICONES = {
    "grid": (
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
    ),
    "users": (
        '<circle cx="9" cy="8" r="3"/>'
        '<path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/>'
        '<circle cx="17" cy="9" r="2.3"/>'
        '<path d="M15.5 20c.3-2.8 2.2-5 4.8-5.6"/>'
    ),
    "id-card": (
        '<rect x="2.5" y="5" width="19" height="14" rx="2"/>'
        '<circle cx="8" cy="12" r="2.2"/>'
        '<line x1="13" y1="10" x2="18" y2="10"/>'
        '<line x1="13" y1="14" x2="18" y2="14"/>'
    ),
    "stethoscope": (
        '<path d="M5 3v5a3 3 0 0 0 6 0V3"/>'
        '<path d="M8 11v3a6 6 0 0 0 12 0v-3.5"/>'
        '<circle cx="20" cy="9.5" r="2.2"/>'
    ),
    "pill": (
        '<rect x="3" y="9" width="18" height="6" rx="3" transform="rotate(-45 12 12)"/>'
        '<line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/>'
    ),
    "building": (
        '<rect x="4" y="3" width="16" height="18" rx="1.5"/>'
        '<path d="M12 7v4M10 9h4"/>'
        '<path d="M9 21v-3h6v3"/>'
    ),
    "shield-check": (
        '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"/>'
        '<path d="M9 12l2 2 4-4"/>'
    ),
    "bar-chart": (
        '<line x1="4" y1="21" x2="20" y2="21"/>'
        '<rect x="6" y="14" width="3" height="7"/>'
        '<rect x="11" y="9" width="3" height="12"/>'
        '<rect x="16" y="5" width="3" height="16"/>'
    ),
    "bell": (
        '<path d="M6 10a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6z"/>'
        '<path d="M10 20a2 2 0 0 0 4 0"/>'
    ),
    "calendar": (
        '<rect x="3" y="5" width="18" height="16" rx="2"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/>'
        '<line x1="8" y1="3" x2="8" y2="7"/>'
        '<line x1="16" y1="3" x2="16" y2="7"/>'
    ),
    "clipboard-list": (
        '<rect x="6" y="4" width="12" height="17" rx="2"/>'
        '<rect x="9" y="2.5" width="6" height="3" rx="1"/>'
        '<line x1="9" y1="11" x2="15" y2="11"/>'
        '<line x1="9" y1="15" x2="15" y2="15"/>'
    ),
    "qr-scan": (
        '<path d="M4 8V5a1 1 0 0 1 1-1h3"/>'
        '<path d="M16 4h3a1 1 0 0 1 1 1v3"/>'
        '<path d="M20 16v3a1 1 0 0 1-1 1h-3"/>'
        '<path d="M8 20H5a1 1 0 0 1-1-1v-3"/>'
        '<rect x="9" y="9" width="2.2" height="2.2"/>'
        '<rect x="12.8" y="9" width="2.2" height="2.2"/>'
        '<rect x="9" y="12.8" width="2.2" height="2.2"/>'
    ),
    "clock-history": (
        '<circle cx="12" cy="13" r="8"/>'
        '<path d="M12 9v4l3 2"/>'
        '<path d="M9 2h6"/>'
    ),
    "user-circle": (
        '<circle cx="12" cy="12" r="9"/>'
        '<circle cx="12" cy="9.5" r="2.8"/>'
        '<path d="M6 18c1-3 3.2-4.5 6-4.5s5 1.5 6 4.5"/>'
    ),
    "lock": (
        '<rect x="5" y="11" width="14" height="9" rx="2"/>'
        '<path d="M8 11V7a4 4 0 0 1 8 0v4"/>'
    ),
    "download": (
        '<path d="M12 3v12"/>'
        '<path d="M7 10l5 5 5-5"/>'
        '<path d="M4 19h16"/>'
    ),
    "family": (
        '<circle cx="8.5" cy="7" r="2.6"/>'
        '<circle cx="17" cy="8" r="2.1"/>'
        '<circle cx="12.5" cy="17.5" r="1.8"/>'
        '<path d="M3.5 19c0-3 2.2-5.4 5-5.4s5 2.4 5 5.4"/>'
        '<path d="M14.8 13.6c2.3.3 4.2 2.2 4.2 4.7"/>'
    ),
    "receipt": (
        '<path d="M6 2.5h12v19l-2.4-1.6L13.2 21l-1.2-1.1-1.2 1.1-2.4-1.1L6 21.5z"/>'
        '<line x1="8.5" y1="7" x2="15.5" y2="7"/>'
        '<line x1="8.5" y1="11" x2="15.5" y2="11"/>'
        '<line x1="8.5" y1="15" x2="13" y2="15"/>'
    ),
    "map-pin": (
        '<path d="M12 21s7-6.4 7-11.5A7 7 0 0 0 5 9.5C5 14.6 12 21 12 21z"/>'
        '<circle cx="12" cy="9.5" r="2.4"/>'
    ),
    "phone": (
        '<path d="M5 4h3.2l1.3 4.4-2 1.6a13 13 0 0 0 6.5 6.5l1.6-2 4.4 1.3V19a2 2 0 0 1-2.2 2A16 16 0 0 1 3 5.2 2 2 0 0 1 5 4z"/>'
    ),
    "mail": (
        '<rect x="3" y="5" width="18" height="14" rx="2"/>'
        '<path d="M4 6.5l8 6 8-6"/>'
    ),
    "check": (
        '<path d="M4.5 12.5l5 5 10-10"/>'
    ),
    "zap": (
        '<path d="M13 2 4.5 13.5H11l-1 8.5L19.5 10.5H13z"/>'
    ),
}


@register.simple_tag
def icone(nom):
    """Icone de navigation en trait fin (SVG inline, sans dependance externe)."""
    contenu = _ICONES.get(nom, "")
    return mark_safe(
        '<svg class="icone-nav" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{contenu}</svg>"
    )
