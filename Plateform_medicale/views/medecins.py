"""CRUD Médecins (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import MedecinForm, generer_mot_de_passe, lier_fiche_medecin
from ..models import JournalActivite, Medecin, Ordonnance, Paiement, User
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
            return render(
                request,
                "mot_de_passe_genere.html",
                {"utilisateur": utilisateur, "mot_de_passe": mot_de_passe, "action": "creation"},
            )
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
    if request.method == "POST":
        # Desactive le User lie : sinon la fiche Medecin disparait mais le
        # compte de connexion reste actif (voir supprimer_patient, meme raisonnement).
        if medecin.user:
            medecin.user.is_active = False
            medecin.user.save(update_fields=["is_active"])
        journaliser(
            request, JournalActivite.Action.SUPPRESSION, f"Médecin : {medecin}",
            "compte de connexion désactivé" if medecin.user else "sans compte de connexion",
        )
        medecin.delete()
        messages.success(request, "Médecin supprimé.")
        return redirect("liste_medecins")
    avertissement = _avertissement_cascade({
        "consultation(s)": medecin.consultation_set.count(),
        "rendez-vous": medecin.rendez_vous.count(),
        "paiement(s)": Paiement.objects.filter(consultation__medecin=medecin).count(),
        "ordonnance(s)": Ordonnance.objects.filter(consultation__medecin=medecin).count(),
    })
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": medecin, "type": "Medecin", "avertissement": avertissement},
    )
