from django.shortcuts import render, redirect

from accounts.decorators import admin_required

from .models import (
    Consultation,
    Medecin,
    Ordonnance,
    Patient,
    PriseEnCharge,
    ServiceMedical,
)


@admin_required
def dashboard(request):
    contexte = {
        "total_patients": Patient.objects.count(),
        "total_medecins": Medecin.objects.count(),
        "total_services": ServiceMedical.objects.count(),
        "total_prises_en_charge": PriseEnCharge.objects.count(),
        "total_consultations": Consultation.objects.count(),
        "total_ordonnances": Ordonnance.objects.count(),
    }
    return render(request, "dashboard.html", contexte)


@admin_required
def liste_patients(request):
    patients = Patient.objects.all()
    return render(request, "liste_patients.html", {"patients": patients})


@admin_required
def ajouter_patient(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        date_naissance = request.POST.get("date_naissance")
        telephone = request.POST.get("telephone")
        adresse = request.POST.get("adresse")

        patient = Patient.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            telephone=telephone,
            adresse=adresse,
        )
        return redirect("liste_patients")

    return render(request, "ajouter_patient.html")


@admin_required
def liste_medecins(request):
    medecins = Medecin.objects.all()
    return render(request, "liste_medecins.html", {"medecins": medecins})


@admin_required
def ajouter_medecin(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        specialite = request.POST.get("specialite")
        telephone = request.POST.get("telephone")
        email = request.POST.get("email")

        medecin = Medecin.objects.create(
            nom=nom,
            prenom=prenom,
            specialite=specialite,
            telephone=telephone,
            email=email,
        )
        return redirect("liste_medecins")

    return render(request, "ajouter_medecin.html")


@admin_required
def liste_services(request):
    services = ServiceMedical.objects.all()
    return render(request, "liste_services.html", {"services": services})


@admin_required
def ajouter_service(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        description = request.POST.get("description")
        prix = request.POST.get("prix")

        service = ServiceMedical.objects.create(
            nom=nom,
            description=description,
            prix=prix,
        )
        return redirect("liste_services")

    return render(request, "ajouter_service.html")


@admin_required
def liste_prises_en_charge(request):
    prises_en_charge = PriseEnCharge.objects.select_related("patient").all()
    return render(
        request,
        "liste_prises_en_charge.html",
        {"prises_en_charge": prises_en_charge},
    )


@admin_required
def ajouter_prise_en_charge(request):
    if request.method == "POST":
        patient_id = request.POST.get("patient")
        motif = request.POST.get("motif")

        prise_en_charge = PriseEnCharge.objects.create(
            patient_id=patient_id,
            motif=motif,
            statut="en_attente",
        )
        return redirect("liste_prises_en_charge")

    patients = Patient.objects.all()
    return render(request, "ajouter_prise_en_charge.html", {"patients": patients})


@admin_required
def modifier_prise_en_charge(request, pk):
    prise_en_charge = PriseEnCharge.objects.get(pk=pk)
    if request.method == "POST":
        prise_en_charge.patient_id = request.POST.get("patient")
        prise_en_charge.motif = request.POST.get("motif")
        prise_en_charge.statut = request.POST.get("statut")
        prise_en_charge.save()
        return redirect("liste_prises_en_charge")
    
    contexte = {
        "prise_en_charge": prise_en_charge,
        "patients": Patient.objects.all(),
    }
    return render(request, "modifier_prise_en_charge.html", contexte)


@admin_required
def supprimer_prise_en_charge(request, pk):
    prise_en_charge = PriseEnCharge.objects.get(pk=pk)
    if request.method == "POST":
        prise_en_charge.delete()
        return redirect("liste_prises_en_charge")
    return render(request, "confirmer_suppression.html", {"objet": prise_en_charge, "type": "Prise en charge"})


@admin_required
def liste_consultations(request):
    consultations = Consultation.objects.select_related(
        "patient",
        "medecin",
        "service",
        "prise_en_charge",
    ).all()
    return render(request, "liste_consultations.html", {"consultations": consultations})


@admin_required
def ajouter_consultation(request):
    if request.method == "POST":
        patient_id = request.POST.get("patient")
        medecin_id = request.POST.get("medecin")
        service_id = request.POST.get("service")
        date_consultation = request.POST.get("date_consultation")
        diagnostic = request.POST.get("diagnostic")
        traitement = request.POST.get("traitement")
        prise_en_charge_id = request.POST.get("prise_en_charge")

        consultation = Consultation.objects.create(
            patient_id=patient_id,
            medecin_id=medecin_id,
            service_id=service_id if service_id else None,
            date_consultation=date_consultation,
            diagnostic=diagnostic,
            traitement=traitement,
            prise_en_charge_id=prise_en_charge_id if prise_en_charge_id else None,
        )
        return redirect("liste_consultations")

    contexte = {
        "patients": Patient.objects.all(),
        "medecins": Medecin.objects.all(),
        "services": ServiceMedical.objects.all(),
        "prises_en_charge": PriseEnCharge.objects.all(),
    }
    return render(request, "ajouter_consultation.html", contexte)


@admin_required
def liste_ordonnances(request):
    ordonnances = Ordonnance.objects.select_related(
        "consultation",
        "consultation__patient",
        "consultation__medecin",
    ).all()
    return render(request, "liste_ordonnances.html", {"ordonnances": ordonnances})


@admin_required
def ajouter_ordonnances(request):
    if request.method == "POST":
        consultation_id = request.POST.get("consultation")
        medicaments = request.POST.get("medicaments")

        ordonnance = Ordonnance.objects.create(
            consultation_id=consultation_id,
            medicaments=medicaments,
        )
        return redirect("liste_ordonnances")

    contexte = {
        "consultations": Consultation.objects.select_related("patient", "medecin").all(),
    }
    return render(request, "ajouter_ordonnances.html", contexte)


# MODIFIER VUES
@admin_required
def modifier_patient(request, pk):
    patient = Patient.objects.get(pk=pk)
    if request.method == "POST":
        patient.nom = request.POST.get("nom")
        patient.prenom = request.POST.get("prenom")
        patient.date_naissance = request.POST.get("date_naissance")
        patient.telephone = request.POST.get("telephone")
        patient.adresse = request.POST.get("adresse")
        patient.save()
        return redirect("liste_patients")
    return render(request, "modifier_patient.html", {"patient": patient})


@admin_required
def modifier_medecin(request, pk):
    medecin = Medecin.objects.get(pk=pk)
    if request.method == "POST":
        medecin.nom = request.POST.get("nom")
        medecin.prenom = request.POST.get("prenom")
        medecin.specialite = request.POST.get("specialite")
        medecin.telephone = request.POST.get("telephone")
        medecin.email = request.POST.get("email")
        medecin.save()
        return redirect("liste_medecins")
    return render(request, "modifier_medecin.html", {"medecin": medecin})


@admin_required
def modifier_service(request, pk):
    service = ServiceMedical.objects.get(pk=pk)
    if request.method == "POST":
        service.nom = request.POST.get("nom")
        service.description = request.POST.get("description")
        service.prix = request.POST.get("prix")
        service.save()
        return redirect("liste_services")
    return render(request, "modifier_service.html", {"service": service})


@admin_required
def modifier_consultation(request, pk):
    consultation = Consultation.objects.get(pk=pk)
    if request.method == "POST":
        consultation.patient_id = request.POST.get("patient")
        consultation.medecin_id = request.POST.get("medecin")
        consultation.service_id = request.POST.get("service") or None
        consultation.date_consultation = request.POST.get("date_consultation")
        consultation.diagnostic = request.POST.get("diagnostic")
        consultation.traitement = request.POST.get("traitement")
        consultation.prise_en_charge_id = request.POST.get("prise_en_charge") or None
        consultation.save()
        return redirect("liste_consultations")
    
    contexte = {
        "consultation": consultation,
        "patients": Patient.objects.all(),
        "medecins": Medecin.objects.all(),
        "services": ServiceMedical.objects.all(),
        "prises_en_charge": PriseEnCharge.objects.all(),
    }
    return render(request, "modifier_consultation.html", contexte)


@admin_required
def modifier_ordonnances(request, pk):
    ordonnance = Ordonnance.objects.get(pk=pk)
    if request.method == "POST":
        ordonnance.consultation_id = request.POST.get("consultation")
        ordonnance.medicaments = request.POST.get("medicaments")
        ordonnance.save()
        return redirect("liste_ordonnances")
    
    contexte = {
        "ordonnance": ordonnance,
        "consultations": Consultation.objects.select_related("patient", "medecin").all(),
    }
    return render(request, "modifier_ordonnances.html", contexte)


# SUPPRIMER VUES
@admin_required
def supprimer_patient(request, pk):
    patient = Patient.objects.get(pk=pk)
    if request.method == "POST":
        patient.delete()
        return redirect("liste_patients")
    return render(request, "confirmer_suppression.html", {"objet": patient, "type": "Patient"})


@admin_required
def supprimer_medecin(request, pk):
    medecin = Medecin.objects.get(pk=pk)
    if request.method == "POST":
        medecin.delete()
        return redirect("liste_medecins")
    return render(request, "confirmer_suppression.html", {"objet": medecin, "type": "Medecin"})


@admin_required
def supprimer_service(request, pk):
    service = ServiceMedical.objects.get(pk=pk)
    if request.method == "POST":
        service.delete()
        return redirect("liste_services")
    return render(request, "confirmer_suppression.html", {"objet": service, "type": "Service"})


@admin_required
def supprimer_consultation(request, pk):
    consultation = Consultation.objects.get(pk=pk)
    if request.method == "POST":
        consultation.delete()
        return redirect("liste_consultations")
    return render(request, "confirmer_suppression.html", {"objet": consultation, "type": "Consultation"})


@admin_required
def supprimer_ordonnances(request, pk):
    ordonnance = Ordonnance.objects.get(pk=pk)
    if request.method == "POST":
        ordonnance.delete()
        return redirect("liste_ordonnances")
    return render(request, "confirmer_suppression.html", {"objet": ordonnance, "type": "Ordonnance"})
