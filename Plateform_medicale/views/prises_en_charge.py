"""CRUD Prises en charge (liste, ajout, modification, suppression)."""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PriseEnChargeForm
from ..models import JournalActivite, PriseEnCharge
from .utils import _paginer, _trier, admin_required, journaliser


@admin_required
def liste_prises_en_charge(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        pks = request.POST.getlist("selection")
        if action in ("valider_selection", "refuser_selection") and pks:
            nouveau_statut = "validee" if action == "valider_selection" else "refusee"
            libelle_statut = "validée(s)" if nouveau_statut == "validee" else "refusée(s)"
            modifiees = PriseEnCharge.objects.filter(pk__in=pks, statut="en_attente")
            count = modifiees.count()
            if count > 0:
                from django.utils import timezone
                from ..services.notifications import (
                    notifier_refus_prise_en_charge,
                    notifier_validation_prise_en_charge,
                )
                modifiees_list = list(modifiees)
                modifiees.update(
                    statut=nouveau_statut,
                    valide_par=request.user,
                    date_validation=timezone.now(),
                )
                for item in modifiees_list:
                    item.statut = nouveau_statut
                    if nouveau_statut == "validee":
                        notifier_validation_prise_en_charge(item)
                    elif nouveau_statut == "refusee":
                        notifier_refus_prise_en_charge(item)

                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    "Prises en charge (Traitement en masse)",
                    f"{count} demande(s) passa(ient) au statut : {nouveau_statut}",
                )
                messages.success(request, f"{count} prise(s) en charge {libelle_statut}.")
            else:
                messages.warning(request, "Aucune demande en attente sélectionnée.")
        return redirect("liste_prises_en_charge")

    prises_en_charge = PriseEnCharge.objects.select_related("patient")

    recherche = request.GET.get("q", "").strip()
    if recherche:
        prises_en_charge = prises_en_charge.filter(
            Q(patient__nom__icontains=recherche) | Q(patient__prenom__icontains=recherche)
        )

    statut = request.GET.get("statut", "")
    urgent = request.GET.get("urgent", "")

    if urgent == "1":
        from django.utils import timezone
        import datetime
        il_y_a_48h = timezone.now() - datetime.timedelta(hours=48)
        prises_en_charge = prises_en_charge.filter(statut="en_attente", date_demande__lte=il_y_a_48h)
    elif statut:
        prises_en_charge = prises_en_charge.filter(statut=statut)

    prises_en_charge = _trier(
        request, prises_en_charge, ["patient__nom", "date_demande", "statut"], "-date_demande",
    )
    return render(
        request,
        "liste_prises_en_charge.html",
        {
            "prises_en_charge": _paginer(request, prises_en_charge),
            "recherche": recherche,
            "statut_choisi": statut,
            "statuts": PriseEnCharge.STATUT_CHOICES,
            "urgent": urgent,
        },
    )


@admin_required
def ajouter_prise_en_charge(request):
    """A la creation, le statut est toujours 'en_attente' : le champ n'est pas propose."""
    if request.method == "POST":
        form = PriseEnChargeForm(request.POST)
        form.fields.pop("statut")
        if form.is_valid():
            prise_en_charge = form.save(commit=False)
            prise_en_charge.statut = "en_attente"
            prise_en_charge.save()
            from ..services.notifications import notifier_demande_prise_en_charge
            notifier_demande_prise_en_charge(prise_en_charge)
            messages.success(request, "Prise en charge ajoutée.")
            return redirect("liste_prises_en_charge")
    else:
        form = PriseEnChargeForm()
        form.fields.pop("statut")
    return render(request, "ajouter_prise_en_charge.html", {"form": form})


@admin_required
def modifier_prise_en_charge(request, pk):
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        ancien_statut_code = prise_en_charge.statut
        ancien_statut = prise_en_charge.get_statut_display()
        form = PriseEnChargeForm(request.POST, instance=prise_en_charge)
        if form.is_valid():
            prise_en_charge = form.save()
            nouveau_statut_code = prise_en_charge.statut
            nouveau_statut = prise_en_charge.get_statut_display()

            if nouveau_statut_code != ancien_statut_code:
                from ..services.notifications import (
                    notifier_refus_prise_en_charge,
                    notifier_validation_prise_en_charge,
                )
                if nouveau_statut_code == "validee":
                    notifier_validation_prise_en_charge(prise_en_charge)
                elif nouveau_statut_code == "refusee":
                    notifier_refus_prise_en_charge(prise_en_charge)

            journaliser(
                request,
                JournalActivite.Action.DECISION if nouveau_statut != ancien_statut else JournalActivite.Action.MODIFICATION,
                f"Prise en charge : {prise_en_charge}",
                "" if nouveau_statut == ancien_statut
                else f"statut : {ancien_statut} -> {nouveau_statut}",
            )
            messages.success(request, "Prise en charge modifiée.")
            return redirect("liste_prises_en_charge")
    else:
        form = PriseEnChargeForm(instance=prise_en_charge)
    return render(
        request,
        "modifier_prise_en_charge.html",
        {"form": form, "prise_en_charge": prise_en_charge},
    )


@admin_required
def supprimer_prise_en_charge(request, pk):
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        journaliser(request, JournalActivite.Action.SUPPRESSION, f"Prise en charge : {prise_en_charge}")
        prise_en_charge.delete()
        messages.success(request, "Prise en charge supprimée.")
        return redirect("liste_prises_en_charge")
    return render(request, "confirmer_suppression.html", {"objet": prise_en_charge, "type": "Prise en charge"})
