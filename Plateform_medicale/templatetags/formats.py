from django import template

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
