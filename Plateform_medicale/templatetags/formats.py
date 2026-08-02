from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .icones import icone as _icone_svg

register = template.Library()


@register.filter
def franc_cfa(montant):
    """Formate un montant en francs CFA : separateur de milliers (espace
    insecable), sans decimales (le franc CFA n'a pas de sous-unite d'usage
    courant, meme si les champs modele restent des DecimalField)."""
    if montant is None or montant == "":
        return ""
    try:
        valeur = int(round(float(montant)))
    except (TypeError, ValueError):
        return montant
    signe = "-" if valeur < 0 else ""
    groupes = f"{abs(valeur):,}".replace(",", " ")
    return f"{signe}{groupes} FCFA"


@register.simple_tag
def prefixe_pagination(get_params):
    """Chaine de requete GET (filtres actifs, hors 'page') a placer devant
    page=N dans un lien de pagination, pour ne pas perdre les filtres en
    changeant de page. Retourne une chaine vide si aucun filtre actif."""
    params = get_params.copy()
    params.pop("page", None)
    chaine = params.urlencode()
    return f"{chaine}&" if chaine else ""


@register.simple_tag
def entete_tri(get_params, champ, libelle):
    """En-tete <th> cliquable pour trier une liste admin (parametre GET
    'tri', ex. 'nom' ou '-nom' pour l'ordre inverse). Meme chevron dans les
    trois etats : au repos (discret, sens neutre), actif ascendant (tourne
    vers le haut) et actif descendant (vers le bas) -- une rotation CSS,
    pas trois icones a maintenir. Conserve les autres filtres actifs, mais
    pas 'page' : changer le tri revient a la premiere page."""
    tri_actuel = get_params.get("tri", "")
    actif = tri_actuel.lstrip("-") == champ
    descendant = actif and tri_actuel.startswith("-")
    nouveau_tri = champ if not actif or descendant else f"-{champ}"

    params = get_params.copy()
    params.pop("page", None)
    params["tri"] = nouveau_tri
    href = escape(f"?{params.urlencode()}")
    texte = escape(libelle)
    chevron = _icone_svg("chevron-down")

    if not actif:
        return mark_safe(
            f'<th scope="col"><a href="{href}" class="lien-tri">{texte} '
            f'<span class="icone-tri">{chevron}</span></a></th>'
        )

    classe = "lien-tri lien-tri-actif lien-tri-desc" if descendant else "lien-tri lien-tri-actif lien-tri-asc"
    aria = "descending" if descendant else "ascending"
    return mark_safe(
        f'<th scope="col" aria-sort="{aria}"><a href="{href}" class="{classe}">{texte} '
        f'<span class="icone-tri">{chevron}</span></a></th>'
    )
