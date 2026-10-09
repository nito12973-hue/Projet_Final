import io
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ..forms import PriseEnChargeForm
from ..models import JournalActivite, PriseEnCharge, User
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
                from ..models import Paiement
                from ..services.notifications import (
                    notifier_refus_prise_en_charge,
                    notifier_validation_prise_en_charge,
                )
                modifiees_list = list(modifiees)
                reussites = 0
                with transaction.atomic():
                    for item in modifiees_list:
                        item.statut = nouveau_statut
                        item.valide_par = request.user
                        item.date_validation = timezone.now()
                        try:
                            item.full_clean()
                            item.save()
                            reussites += 1
                        except ValidationError:
                            continue

                        if nouveau_statut == "validee":
                            notifier_validation_prise_en_charge(item)
                            for c in item.consultation_set.all():
                                if hasattr(c, "paiement"):
                                    if c.paiement.statut == Paiement.Statut.NON_REGLE:
                                        p_calc = Paiement.calculer_pour(c)
                                        c.paiement.montant_part_assurance = p_calc.montant_part_assurance
                                        c.paiement.montant_part_patient = p_calc.montant_part_patient
                                        c.paiement.taux_applique = p_calc.taux_applique
                                        c.paiement.save()
                                    else:
                                        paiement_id = c.paiement.pk
                                        part_patient_actuelle = c.paiement.montant_part_patient
                                        p_calc = Paiement.calculer_pour(c)
                                        trop_percu = part_patient_actuelle - p_calc.montant_part_patient
                                        if trop_percu > 0:
                                            journaliser(
                                                request,
                                                JournalActivite.Action.MODIFICATION,
                                                f"Régularisation comptable — Paiement #{paiement_id} ({c.patient})",
                                                f"Prise en charge #{item.pk} validée a posteriori. Trop-perçu constaté à rembourser : {trop_percu} FCFA (nouvelle part assurance : {p_calc.montant_part_assurance} FCFA)",
                                            )
                        elif nouveau_statut == "refusee":
                            notifier_refus_prise_en_charge(item)

                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    "Prises en charge (Traitement en masse)",
                    f"{reussites} demande(s) passée(s) au statut : {nouveau_statut}",
                )
                messages.success(request, f"{reussites} prise(s) en charge {libelle_statut}.")
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
def valider_prise_en_charge(request, pk):
    """Validation unitaire rapide d une prise en charge par l administration."""
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        from django.utils import timezone
        from ..models import Paiement
        from ..services.notifications import notifier_validation_prise_en_charge
        try:
            with transaction.atomic():
                prise_en_charge.statut = "validee"
                prise_en_charge.valide_par = request.user
                prise_en_charge.date_validation = timezone.now()
                prise_en_charge.full_clean()
                prise_en_charge.save()

                # Recalculer les paiements des consultations rattachées
                for c in prise_en_charge.consultation_set.all():
                    if hasattr(c, "paiement"):
                        if c.paiement.statut == Paiement.Statut.NON_REGLE:
                            p_calc = Paiement.calculer_pour(c)
                            c.paiement.montant_part_assurance = p_calc.montant_part_assurance
                            c.paiement.montant_part_patient = p_calc.montant_part_patient
                            c.paiement.taux_applique = p_calc.taux_applique
                            c.paiement.save()
                        else:
                            paiement_id = c.paiement.pk
                            part_patient_actuelle = c.paiement.montant_part_patient
                            p_calc = Paiement.calculer_pour(c)
                            trop_percu = part_patient_actuelle - p_calc.montant_part_patient
                            if trop_percu > 0:
                                journaliser(
                                    request,
                                    JournalActivite.Action.MODIFICATION,
                                    f"Régularisation comptable — Paiement #{paiement_id} ({c.patient})",
                                    f"Prise en charge validée a posteriori. Trop-perçu constaté à rembourser : {trop_percu} FCFA (nouvelle part assurance : {p_calc.montant_part_assurance} FCFA)",
                                )

                notifier_validation_prise_en_charge(prise_en_charge)
                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    f"Prise en charge validée : {prise_en_charge.patient}",
                    f"Motif : {prise_en_charge.motif}",
                )
                messages.success(request, f"La prise en charge de {prise_en_charge.patient} a été validée avec succès.")
        except ValidationError as e:
            messages.error(request, f"Validation impossible : {e}")
    return redirect("liste_prises_en_charge")


@admin_required
def refuser_prise_en_charge(request, pk):
    """Refus unitaire rapide avec motif d une prise en charge."""
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        from django.utils import timezone
        from ..services.notifications import notifier_refus_prise_en_charge
        motif_refus = request.POST.get("motif_refus", "").strip() or "Non conforme aux critères de couverture"

        try:
            with transaction.atomic():
                prise_en_charge.statut = "refusee"
                prise_en_charge.motif_refus = motif_refus
                prise_en_charge.valide_par = request.user
                prise_en_charge.date_validation = timezone.now()
                prise_en_charge.full_clean()
                prise_en_charge.save()

                notifier_refus_prise_en_charge(prise_en_charge)
                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    f"Prise en charge refusée : {prise_en_charge.patient}",
                    f"Motif du refus : {motif_refus}",
                )
                messages.warning(request, f"La prise en charge de {prise_en_charge.patient} a été refusée.")
        except ValidationError as e:
            messages.error(request, f"Impossible de refuser cette prise en charge : {e}")
    return redirect("liste_prises_en_charge")


@admin_required
def ajouter_prise_en_charge(request):
    """A la creation, le statut est toujours 'en_attente' : le champ n'est pas propose."""
    if request.method == "POST":
        form = PriseEnChargeForm(request.POST, request.FILES)
        form.fields.pop("statut")
        if form.is_valid():
            prise_en_charge = form.save(commit=False)
            prise_en_charge.statut = "en_attente"
            prise_en_charge.save()
            form.save_m2m()
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
        form = PriseEnChargeForm(request.POST, request.FILES, instance=prise_en_charge)
        if form.is_valid():
            prise_en_charge = form.save()
            nouveau_statut_code = prise_en_charge.statut
            nouveau_statut = prise_en_charge.get_statut_display()

            if nouveau_statut_code != ancien_statut_code:
                from django.utils import timezone
                from ..models import Paiement
                from ..services.notifications import (
                    notifier_refus_prise_en_charge,
                    notifier_validation_prise_en_charge,
                )
                if nouveau_statut_code == "validee":
                    prise_en_charge.valide_par = request.user
                    prise_en_charge.date_validation = timezone.now()
                    prise_en_charge.save(update_fields=["valide_par", "date_validation"])
                    for c in prise_en_charge.consultation_set.all():
                        if hasattr(c, "paiement"):
                            if c.paiement.statut == Paiement.Statut.NON_REGLE:
                                p_calc = Paiement.calculer_pour(c)
                                c.paiement.montant_part_assurance = p_calc.montant_part_assurance
                                c.paiement.montant_part_patient = p_calc.montant_part_patient
                                c.paiement.taux_applique = p_calc.taux_applique
                                c.paiement.save()
                            else:
                                paiement_id = c.paiement.pk
                                part_patient_actuelle = c.paiement.montant_part_patient
                                p_calc = Paiement.calculer_pour(c)
                                trop_percu = part_patient_actuelle - p_calc.montant_part_patient
                                if trop_percu > 0:
                                    journaliser(
                                        request,
                                        JournalActivite.Action.MODIFICATION,
                                        f"Régularisation comptable — Paiement #{paiement_id} ({c.patient})",
                                        f"Prise en charge #{prise_en_charge.pk} validée a posteriori. Trop-perçu constaté à rembourser : {trop_percu} FCFA (nouvelle part assurance : {p_calc.montant_part_assurance} FCFA)",
                                    )
                    notifier_validation_prise_en_charge(prise_en_charge)
                elif nouveau_statut_code == "refusee":
                    prise_en_charge.valide_par = request.user
                    prise_en_charge.date_validation = timezone.now()
                    prise_en_charge.save(update_fields=["valide_par", "date_validation"])
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
    nb_consultations = prise_en_charge.consultation_set.count()
    est_protege = (nb_consultations > 0)

    if request.method == "POST":
        if est_protege:
            messages.error(
                request,
                f"Impossible de supprimer cette prise en charge : {nb_consultations} consultation(s) médicale(s) y sont rattachée(s).",
            )
            return redirect("liste_prises_en_charge")

        try:
            with transaction.atomic():
                nom_pec = str(prise_en_charge)
                prise_en_charge.delete()
                journaliser(request, JournalActivite.Action.SUPPRESSION, f"Prise en charge : {nom_pec}")
                messages.success(request, "Prise en charge supprimée.")
                return redirect("liste_prises_en_charge")
        except ProtectedError:
            messages.error(request, "Suppression impossible : des actes médicaux protégés y sont associés.")
            return redirect("liste_prises_en_charge")

    return render(
        request,
        "confirmer_suppression.html",
        {
            "objet": prise_en_charge,
            "type": "Prise en charge",
            "est_protege": est_protege,
            "motif_blocage": (
                "Des consultations médicales sont associées à cette prise en charge. "
                "Sa suppression est bloquée pour garantir la traçabilité des dossiers de soins."
            ) if est_protege else None,
        },
    )


@login_required
def telecharger_bon_prise_en_charge_pdf(request, pk):
    """Génère le Bon de Prise en Charge officiel / Lettre de garantie en PDF (ReportLab)."""
    prise_en_charge = get_object_or_404(
        PriseEnCharge.objects.select_related(
            "patient",
            "patient__plan_couverture",
            "patient__assure_principal",
            "patient__assure_principal__plan_couverture",
            "valide_par",
        ),
        pk=pk,
    )

    user = request.user
    role = getattr(user, "role", None)
    est_admin = user.is_staff or role == User.Role.ADMIN
    est_assure = False
    if role == User.Role.ASSURE and hasattr(user, "patient"):
        patient_assure = user.patient
        est_assure = (
            prise_en_charge.patient == patient_assure
            or prise_en_charge.patient.assure_principal == patient_assure
        )
    est_medecin = (role == User.Role.MEDECIN)

    if not (est_admin or est_assure or est_medecin):
        raise PermissionDenied("Vous n'êtes pas autorisé à télécharger ce bon de prise en charge.")

    # Réponse HTTP PDF
    reponse = HttpResponse(content_type="application/pdf")
    num_bon = prise_en_charge.numero_pec or f"PEC-{prise_en_charge.pk:06d}"
    nom_fichier = f"Bon_PriseEnCharge_{num_bon}.pdf"
    reponse["Content-Disposition"] = f'inline; filename="{nom_fichier}"'

    doc = SimpleDocTemplate(
        reponse,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=f"Bon de Prise en Charge - {num_bon}",
        author="SantéSN Tiers Payant",
    )

    styles = getSampleStyleSheet()

    # Couleurs de la charte SantéSN
    c_primaire = colors.HexColor("#0e7c86")
    c_titre = colors.HexColor("#0b2027")
    c_fond = colors.HexColor("#f8fafc")
    c_bordure = colors.HexColor("#cbd5e1")
    c_vert = colors.HexColor("#059669")
    c_texte = colors.HexColor("#1e293b")
    c_muet = colors.HexColor("#64748b")

    s_titre_doc = ParagraphStyle("TitreDoc", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=c_titre, alignment=1)
    s_sous_titre = ParagraphStyle("SousTitre", fontName="Helvetica", fontSize=9, leading=13, textColor=c_primaire, alignment=1)
    s_section = ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=c_primaire, spaceBefore=4, spaceAfter=2)
    s_texte = ParagraphStyle("Texte", fontName="Helvetica", fontSize=8.5, leading=12, textColor=c_texte)
    s_gras = ParagraphStyle("Gras", fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=c_texte)
    s_valeur = ParagraphStyle("Valeur", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=c_titre)
    s_legal = ParagraphStyle("Legal", fontName="Helvetica", fontSize=7.2, leading=9.5, textColor=c_muet, alignment=1)

    patient = prise_en_charge.patient
    plan = patient.titulaire.plan_couverture
    taux = patient.taux_couverture or 80
    date_jour = timezone.now().strftime("%d/%m/%Y à %H:%M")
    date_demande_str = prise_en_charge.date_demande.strftime("%d/%m/%Y")
    date_val_str = prise_en_charge.date_validation.strftime("%d/%m/%Y à %H:%M") if prise_en_charge.date_validation else "En attente"
    valideur = prise_en_charge.valide_par.get_full_name() or prise_en_charge.valide_par.email if prise_en_charge.valide_par else "Administration IPM"

    # Statut libellé et couleur
    est_validee = (prise_en_charge.statut == "validee")
    statut_libelle = "VALIDÉ — GARANTIE TIERS PAYANT ACCORDÉE" if est_validee else f"DEMANDE EN COURS ({prise_en_charge.get_statut_display().upper()})"
    statut_couleur = c_vert if est_validee else colors.HexColor("#d97706")

    # QR Code d'authenticité (PNG en mémoire)
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(f"SantéSN PEC:{num_bon}|Patient:{patient.nom_complet}|Taux:{taux}%|Statut:{prise_en_charge.statut}")
    qr.make(fit=True)
    buf_qr = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf_qr, format="PNG")
    buf_qr.seek(0)
    image_qr = RLImage(buf_qr, width=64, height=64)

    elements = []

    # 1. En-tête officiel
    entete_data = [
        [
            Paragraph("<b>RÉPUBLIQUE DU SÉNÉGAL</b><br/><font size=7.5 color='#64748b'>Plateforme Nationale SantéSN de Tiers Payant Médical<br/>Commission des Données Personnelles (Loi 2008-12)</font>", s_texte),
            Paragraph(f"<font size=11 color='#0e7c86'><b>SANTÉ<font color='#0b2027'>SN</font></b></font><br/><font size=7.5 color='#64748b'>Réf : <b>{num_bon}</b><br/>Émis le {date_jour}</font>", ParagraphStyle("EnteteD", fontName="Helvetica", fontSize=8, leading=11, alignment=2)),
        ]
    ]
    t_entete = Table(entete_data, colWidths=[340, 183])
    t_entete.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_entete)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_primaire, spaceBefore=4, spaceAfter=8))

    # 2. Titre du document
    elements.append(Paragraph("BON DE PRISE EN CHARGE MÉDICALE", s_titre_doc))
    elements.append(Paragraph("ATTESTATION DE DISPENSE D'AVANCE DE FRAIS (TIERS PAYANT)", s_sous_titre))
    elements.append(Spacer(1, 6))

    # 3. Badge Statut
    badge_data = [[
        Paragraph(f"<b>STATUT : {statut_libelle}</b>", ParagraphStyle("BStatut", fontName="Helvetica-Bold", fontSize=9, textColor=statut_couleur, alignment=1))
    ]]
    t_badge = Table(badge_data, colWidths=[523])
    t_badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4") if est_validee else colors.HexColor("#fffbeb")),
        ('BOX', (0, 0), (-1, -1), 1, statut_couleur),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_badge)
    elements.append(Spacer(1, 8))

    # 4. Bloc Bénéficiaire & Couverture
    elements.append(Paragraph("1. IDENTIFICATION DU BÉNÉFICIAIRE & COUVERTURE", s_section))
    qualite_txt = "Assuré principal" if not patient.est_ayant_droit else f"Ayant droit ({patient.get_lien_parente_display()}) de {patient.assure_principal.nom_complet}"
    benef_data = [
        [
            Paragraph("<b>Nom & Prénom :</b>", s_gras),
            Paragraph(patient.nom_complet.upper(), s_valeur),
            Paragraph("<b>N° Carte Assuré :</b>", s_gras),
            Paragraph(f"<font color='#0e7c86'><b>{patient.numero_carte or 'N/A'}</b></font>", s_valeur),
        ],
        [
            Paragraph("<b>Qualité :</b>", s_gras),
            Paragraph(qualite_txt, s_texte),
            Paragraph("<b>Date de naissance :</b>", s_gras),
            Paragraph(f"{patient.date_naissance.strftime('%d/%m/%Y')} ({patient.age} ans)" if patient.date_naissance else "N/A", s_texte),
        ],
        [
            Paragraph("<b>Régime / Plan IPM :</b>", s_gras),
            Paragraph(str(plan.nom) if plan else "Régime Conventionné SantéSN", s_texte),
            Paragraph("<b>Taux Garanti :</b>", s_gras),
            Paragraph(f"<font color='#059669'><b>{taux}% pris en charge</b></font>", s_valeur),
        ],
    ]
    t_benef = Table(benef_data, colWidths=[110, 160, 110, 143])
    t_benef.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_fond),
        ('BOX', (0, 0), (-1, -1), 0.5, c_bordure),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t_benef)
    elements.append(Spacer(1, 8))

    # 5. Bloc Devis & Actes Médicaux Pris en Charge
    elements.append(Paragraph("2. DÉTAILS DU DEVIS MÉDICAL & PRESTATIONS ACCORDÉES", s_section))
    motif_affiche = prise_en_charge.motif.strip() or "Soins et consultations selon devis remis."

    # Formatage montants si renseignés
    montant_devis_txt = f"{int(prise_en_charge.montant_estime):,} FCFA".replace(",", " ") if prise_en_charge.montant_estime else "Sur justificatif de facture"
    part_ass_txt = f"{int(prise_en_charge.montant_part_assurance):,} FCFA".replace(",", " ") if prise_en_charge.montant_part_assurance else f"{taux}% du montant facturé"
    part_pat_txt = f"{int(prise_en_charge.montant_part_patient):,} FCFA".replace(",", " ") if prise_en_charge.montant_part_patient else f"{100 - taux}% (Ticket modérateur)"
    devis_joint_txt = "Devis numérisé certifié disponible sur SantéSN" if prise_en_charge.devis_fichier else "Devis papier vérifié"

    devis_data = [
        [
            Paragraph("<b>Objet des soins / Actes :</b>", s_gras),
            Paragraph(motif_affiche, s_texte),
        ],
        [
            Paragraph("<b>Montant estimé du devis :</b>", s_gras),
            Paragraph(f"<b>{montant_devis_txt}</b>", s_valeur),
        ],
        [
            Paragraph("<b>Part prise en charge IPM :</b>", s_gras),
            Paragraph(f"<font color='#059669'><b>{part_ass_txt}</b> (Dispense d'avance)</font>", s_valeur),
        ],
        [
            Paragraph("<b>Part restant au patient :</b>", s_gras),
            Paragraph(f"<font color='#dc2626'><b>{part_pat_txt}</b> (Ticket modérateur à régler au guichet)</font>", s_valeur),
        ],
        [
            Paragraph("<b>Document du devis :</b>", s_gras),
            Paragraph(devis_joint_txt, s_texte),
        ],
    ]
    t_devis = Table(devis_data, colWidths=[160, 363])
    t_devis.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_fond),
        ('BOX', (0, 0), (-1, -1), 0.5, c_bordure),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t_devis)
    elements.append(Spacer(1, 8))

    # 6. Bloc Validation, Cachet & QR Code
    elements.append(Paragraph("3. CERTIFICATION & AUTHENTICITÉ DU BON", s_section))
    certif_data = [
        [
            Paragraph(
                f"<b>Décision administrative IPM</b><br/>"
                f"• Demande soumise le : <b>{date_demande_str}</b><br/>"
                f"• Décision validée le : <b>{date_val_str}</b><br/>"
                f"• Validateur agréé : <b>{valideur}</b><br/>"
                f"• Signature électronique : <b>SHA256:{num_bon}-SANTE-SN</b><br/>"
                f"<font size=7 color='#64748b'>Cachet électronique faisant foi auprès des établissements partenaires.</font>",
                s_texte,
            ),
            image_qr,
        ]
    ]
    t_certif = Table(certif_data, colWidths=[430, 93])
    t_certif.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.5, c_bordure),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
    ]))
    elements.append(t_certif)
    elements.append(Spacer(1, 10))

    # 7. Mentions légales et cadre conventionnel
    legal_txt = (
        "<b>CONDITIONS D'UTILISATION DU BON DE PRISE EN CHARGE :</b><br/>"
        "1. Le présent bon est strictement personnel et incessible. Il dispense le bénéficiaire de l'avance des frais de santé à concurrence de la part prise en charge garantie.<br/>"
        "2. L'établissement de soins conventionné s'engage à pratiquer les tarifs de la convention IPM et à transmettre sa facture avec le présent bon.<br/>"
        "3. Données de santé protégées conformément à la Loi 2008-12 sur les données à caractère personnel (CDP Sénégal) · SantéSN © 2026."
    )
    elements.append(Paragraph(legal_txt, s_legal))

    doc.build(elements)
    return reponse
