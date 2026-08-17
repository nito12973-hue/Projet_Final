from django import template
from django.utils import timezone
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
# le fil d'ariane reste alors vide, jamais un libelle faux (le role n'y
# figure plus : il etait deja affiche deux fois ailleurs a l'ecran).
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
    "journal_activite": "Journal d'activité",
    "envoyer_notification": "Notifications",
    "liste_notifications_envoyees": "Notifications",
    "liste_consultations": "Consultations",
    "carte_patient": "Assurés",
    "carte_scan": "Carte de prise en charge",
    "mes_prises_en_charge_assure": "Mes prises en charge",
    "mes_notifications": "Notifications",
    "parametres": "Paramètres",
    "parametres_section": "Paramètres",
    "mon_compte": "Paramètres",
    "changer_mot_de_passe": "Paramètres",
}


@register.simple_tag
def salutation():
    """Salutation selon l'heure REELLE, dans le fuseau de la plateforme.

    Le texte etait fige a "Bonjour" sur deux tableaux de bord, et absent des
    deux autres : un utilisateur qui ouvre SantéSN a 21 h etait accueilli
    par un "Bonjour". timezone.localtime() suit TIME_ZONE (Africa/Dakar),
    pas l'heure du serveur ni celle du navigateur.
    """
    heure = timezone.localtime().hour
    if 5 <= heure < 12:
        return "Bonjour"
    if 12 <= heure < 18:
        return "Bon après-midi"
    return "Bonsoir"


@register.simple_tag
def nom_accueil(utilisateur, personne=None):
    """Prenom a afficher dans la salutation, avec un repli propre.

    On prefere la fiche metier (Patient/Medecin) au compte : c'est le nom
    que la personne reconnait. A defaut, le prenom du compte, puis son nom,
    puis la partie locale de son adresse. JAMAIS de chaine vide, de None,
    ni de variable brute -- l'ecran affichait "Bonjour " suivi de rien pour
    un assure qui n'avait pas encore complete son profil.
    """
    for candidat in (getattr(personne, "prenom", None),
                     getattr(utilisateur, "first_name", None),
                     getattr(personne, "nom", None),
                     getattr(utilisateur, "last_name", None)):
        if candidat and str(candidat).strip():
            return str(candidat).strip()
    courriel = getattr(utilisateur, "email", "") or ""
    return courriel.split("@")[0] if "@" in courriel else "bienvenue"


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
def entete_tri(get_params, champ, libelle, classe=""):
    """En-tete <th> cliquable pour trier une liste admin (parametre GET
    'tri', ex. 'nom' ou '-nom' pour l'ordre inverse). Meme chevron dans les
    trois etats : au repos (discret, sens neutre), actif ascendant (tourne
    vers le haut) et actif descendant (vers le bas) -- une rotation CSS,
    pas trois icones a maintenir. Conserve les autres filtres actifs, mais
    pas 'page' : changer le tri revient a la premiere page.

    `classe` marque une colonne SECONDAIRE ("col-optionnelle") : masquee sous
    900 px, ou une liste admin de 8 colonnes devient illisible et rejette la
    colonne Actions hors de l'ecran. La meme classe doit alors etre posee sur
    les <td> correspondants."""
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

    classe_th = f' class="{escape(classe)}"' if classe else ""

    if not actif:
        return mark_safe(
            f'<th scope="col"{classe_th}><a href="{href}" class="lien-tri">{texte} '
            f'<span class="icone-tri">{chevron}</span></a></th>'
        )

    classe_lien = "lien-tri lien-tri-actif lien-tri-desc" if descendant else "lien-tri lien-tri-actif lien-tri-asc"
    aria = "descending" if descendant else "ascending"
    return mark_safe(
        f'<th scope="col" aria-sort="{aria}"{classe_th}><a href="{href}" class="{classe_lien}">{texte} '
        f'<span class="icone-tri">{chevron}</span></a></th>'
    )
