"""
Managers et QuerySets multi-organismes pour SantéSN (Multi-tenant fail-closed).
Garantit qu'aucune requête ne peut accidentellement exposer les dossiers d'un organisme à un autre.
"""
from django.db import models


class OrganismeScopedQuerySet(models.QuerySet):
    """
    QuerySet avec filtrage strict par organisme.
    Mode fermé (fail-closed) par défaut :
    - Sans organisme spécifié et sans flag admin explicite : renvoie une queryset vide (.none()).
    - Pour un modèle non référencé dans les chemins d'isolation : lève NotImplementedError.
    """

    CHEMINS_ORGANISME = {
        "Patient": "organisme",
        "Consultation": "patient__organisme",
        "Paiement": "consultation__patient__organisme",
        "PriseEnCharge": "patient__organisme",
        "DemandeRemboursement": "organisme",
        "DemandeSupport": "patient__organisme",
        "ConventionPrestataire": "organisme",
        "FacturePrestataire": "organisme",
    }

    def for_organisme(self, organisme, allow_admin=False):
        """
        Filtre les enregistrements pour l'organisme donné.
        Si organisme est None et allow_admin=False -> renvoie .none() (fail-closed).
        Si le modèle n'a pas de chemin d'isolation connu -> lève NotImplementedError.
        """
        if not organisme:
            if allow_admin:
                return self.all()
            return self.none()

        nom_modele = self.model.__name__
        champ = self.CHEMINS_ORGANISME.get(nom_modele)
        if not champ:
            raise NotImplementedError(
                f"Le modèle {nom_modele} n'a pas de chemin d'isolation multi-organismes configuré."
            )

        return self.filter(**{champ: organisme})

    def for_user(self, user):
        """
        Filtre selon le rôle et le rattachement de l'utilisateur :
        - GESTIONNAIRE : restreint à user.organisme
        - ADMIN : accès complet plateforme (self.all())
        - Autre : vide par défaut (self.none())
        """
        if not user or not user.is_authenticated:
            return self.none()

        role = getattr(user, "role", None)
        if role == "GESTIONNAIRE":
            organisme = getattr(user, "organisme", None)
            if not organisme or not getattr(organisme, "actif", False):
                return self.none()
            return self.for_organisme(organisme)
        elif role == "ADMIN":
            return self.all()

        return self.none()


class OrganismeScopedManager(models.Manager.from_queryset(OrganismeScopedQuerySet)):
    """Manager appliquant OrganismeScopedQuerySet."""
    pass
