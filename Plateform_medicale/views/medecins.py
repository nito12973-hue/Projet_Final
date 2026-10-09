"""CRUD Médecins (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import MedecinForm, generer_mot_de_passe
from ..models import JournalActivite, Medecin, Ordonnance, Paiement, User
from ..services.onboarding import construire_bilan_onboarding, envoyer_activation_utilisateur
from .utils import _avertissement_cascade, _paginer, _trier, admin_required, journaliser


@admin_required
def liste_medecins(request):
    medecins = Medecin.objects.select_related("prestataire")

    # Seul referentiel admin qui grandit sans filtre : au-dela d'une page,
    # retrouver un medecin obligeait a feuilleter.
    recherche = request.GET.get("q", "").strip()
    if recherche:
        medecins = medecins.filter(
            Q(nom__icontains=recherche)
            | Q(prenom__icontains=recherche)
            | Q(specialite__icontains=recherche)
            | Q(email__icontains=recherche)
        )

    medecins = _trier(request, medecins, ["nom", "specialite", "email"], ["nom", "prenom"])
    return render(request, "liste_medecins.html", {
        "medecins": _paginer(request, medecins),
        "recherche": recherche,
    })


@admin_required
def ajouter_medecin(request):
    if request.method == "POST":
        form = MedecinForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                medecin = form.save(commit=False)
                mot_de_passe = generer_mot_de_passe()
                utilisateur = User.objects.create_user(
                    email=medecin.email,
                    password=mot_de_passe,
                    role=User.Role.MEDECIN,
                    first_name=medecin.prenom,
                    last_name=medecin.nom,
                    phone_number=medecin.telephone,
                )
                medecin.user = utilisateur
                medecin.save()
                statut_onboarding = envoyer_activation_utilisateur(utilisateur, request=request)
                journaliser(request, JournalActivite.Action.CREATION, f"Médecin {utilisateur.email}", f"Dr {medecin.prenom} {medecin.nom}")
                bilan = statut_onboarding.get("bilan") or construire_bilan_onboarding(statut_onboarding, utilisateur, action="creation")
                if bilan["niveau"] == "success":
                    messages.success(request, bilan["texte_flash"])
                else:
                    messages.warning(request, bilan["texte_flash"])
                return redirect("liste_medecins")
    else:
        form = MedecinForm()
    return render(request, "ajouter_medecin.html", {"form": form})


@admin_required
def modifier_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)
    if request.method == "POST":
        form = MedecinForm(request.POST, instance=medecin)
        if form.is_valid():
            form.save()
            messages.success(request, "Médecin modifié.")
            return redirect("liste_medecins")
    else:
        form = MedecinForm(instance=medecin)
    return render(request, "modifier_medecin.html", {"form": form, "medecin": medecin})


@admin_required
def supprimer_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)
    nb_consultations = medecin.consultation_set.count()
    est_protege = (nb_consultations > 0)

    if request.method == "POST":
        if est_protege:
            messages.error(
                request,
                f"Impossible de supprimer le Dr {medecin.nom_complet} : {nb_consultations} consultation(s) "
                "médicale(s) lui sont associées. Pour des raisons réglementaires et médico-légales, ce praticien ne peut pas être supprimé.",
            )
            return redirect("liste_medecins")

        try:
            with transaction.atomic():
                user_associe = medecin.user
                nom_medecin = str(medecin)
                details_journal = "compte de connexion désactivé" if user_associe else "sans compte de connexion"

                if user_associe:
                    user_associe.is_active = False
                    user_associe.save(update_fields=["is_active"])

                medecin.delete()

                # Journalisation APRES la suppression effective
                journaliser(
                    request,
                    JournalActivite.Action.SUPPRESSION,
                    f"Médecin : {nom_medecin}",
                    details_journal,
                )
                messages.success(request, f"Médecin Dr {nom_medecin} supprimé avec succès.")
                return redirect("liste_medecins")
        except ProtectedError:
            messages.error(
                request,
                f"Suppression impossible : des actes médicaux protégés sont liés au {medecin}.",
            )
            return redirect("liste_medecins")

    avertissement = _avertissement_cascade({
        "consultation(s)": nb_consultations,
        "rendez-vous": medecin.rendez_vous.count(),
        "paiement(s)": Paiement.objects.filter(consultation__medecin=medecin).count(),
        "ordonnance(s)": Ordonnance.objects.filter(consultation__medecin=medecin).count(),
    })
    return render(
        request,
        "confirmer_suppression.html",
        {
            "objet": medecin,
            "type": "Medecin",
            "avertissement": avertissement,
            "est_protege": est_protege,
            "motif_blocage": (
                "Ce praticien a réalisé des consultations médicales archivées sur la plateforme. "
                "Pour des obligations de conservation médico-légale du dossier patient, la suppression définitive est bloquée."
            ) if est_protege else None,
        },
    )
