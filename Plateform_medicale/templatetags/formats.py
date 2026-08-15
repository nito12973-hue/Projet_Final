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


# Libelle affiche dans le fil d'ariane de la barre superieure, par nom de
# route. Une seule table ici plutot qu'un {% block %} a redefinir dans chaque
# template : les ecrans de formulaire (ajouter_/modifier_/supprimer_) sont
# volontairement rattaches au libelle de leur liste, c'est la section que
# l'utilisateur reconnait. Une route absente de la table n'affiche rien --
# le fil d'ariane se limite alors au role, jamais un libelle faux.
_LIBELLES_PAGE = {
    "dashboard": "Tableau de bord",
    "dashboard_assure": "Tableau de bord",
    "dashboard_medecin": "Tableau de bord",
    "dashboard_pharmacien": "Tableau de bord",
    "liste_utilisateurs": "Utilisateurs",
    "ajouter_utilisateur": "Utilisateurs",
    "modifier_utilisateur": "Utilisateurs",
    "importer_utilisateurs_excel": "Utilisateurs",
    "liste_patients": "Assurés",
    "ajouter_patient": "Assurés",
    "modifier_patient": "Assurés",
    "liste_medecins": "Médecins",
    "ajouter_medecin": "Médecins",
    "modifier_medecin": "Médecins",
    "liste_pharmaciens": "Pharmaciens",
    "modifier_pharmacien": "Pharmaciens",
    "liste_prestataires": "Prestataires",
    "ajouter_prestataire": "Prestataires",
    "modifier_prestataire": "Prestataires",
    "liste_services": "Services médicaux",
    "ajouter_service": "Services médicaux",
    "modifier_service": "Services médicaux",
    "liste_plans_couverture": "Plans de couverture",
    "ajouter_plan_couverture": "Plans de couverture",
    "modifier_plan_couverture": "Plans de couverture",
    "liste_prises_en_charge": "Prises en charge",
    "ajouter_prise_en_charge": "Prises en charge",
    "modifier_prise_en_charge": "Prises en charge",
    "liste_rendez_vous": "Rendez-vous",
    "liste_ordonnances": "Ordonnances",
    "liste_paiements": "Paiements",
    "rapports": "Rapports",
    "envoyer_notification": "Notifications",
    "liste_notifications_envoyees": "Notifications",
    "mes_notifications": "Notifications",
    "parametres": "Paramètres",
    "mon_compte": "Paramètres",
    "changer_mot_de_passe": "Paramètres",
}


@register.filter
def libelle_page(nom_route):
    """Libelle de section affiche dans le fil d'ariane, depuis
    request.resolver_match.url_name. Chaine vide si la route est inconnue :
    le gabarit masque alors le separateur (regle CSS .fil-ariane b:empty)."""
    return _LIBELLES_PAGE.get(nom_route, "")


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
