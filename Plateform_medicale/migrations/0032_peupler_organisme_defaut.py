from django.db import migrations


def peupler_organisme_defaut(apps, schema_editor):
    Organisme = apps.get_model("Plateform_medicale", "Organisme")
    Patient = apps.get_model("Plateform_medicale", "Patient")
    User = apps.get_model("Plateform_medicale", "User")

    organisme_defaut, _ = Organisme.objects.get_or_create(
        code="IPM-DEFAUT",
        defaults={
            "nom": "IPM SantéSN Défaut",
            "type_organisme": "IPM",
            "actif": True,
        },
    )
    Patient.objects.filter(organisme__isnull=True).update(organisme=organisme_defaut)
    User.objects.filter(
        role__in=["GESTIONNAIRE", "ASSURE"], organisme__isnull=True
    ).update(organisme=organisme_defaut)


def annuler_organisme_defaut(apps, schema_editor):
    Patient = apps.get_model("Plateform_medicale", "Patient")
    User = apps.get_model("Plateform_medicale", "User")
    Patient.objects.filter(organisme__code="IPM-DEFAUT").update(organisme=None)
    User.objects.filter(organisme__code="IPM-DEFAUT").update(organisme=None)


class Migration(migrations.Migration):

    dependencies = [
        ("Plateform_medicale", "0031_organisme_et_champs_nullables"),
    ]

    operations = [
        migrations.RunPython(peupler_organisme_defaut, annuler_organisme_defaut),
    ]
