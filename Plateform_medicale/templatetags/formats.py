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
