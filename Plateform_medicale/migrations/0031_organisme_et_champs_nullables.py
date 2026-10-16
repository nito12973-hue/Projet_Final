import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Plateform_medicale", "0030_audit_acces_dpi_cdp"),
    ]

    operations = [
        migrations.CreateModel(
            name="Organisme",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nom",
                    models.CharField(max_length=150, verbose_name="nom de l'organisme"),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="code unique"
                    ),
                ),
                (
                    "type_organisme",
                    models.CharField(
                        choices=[
                            ("IPM", "Institution de Prévoyance Maladie (IPM)"),
                            ("ASSURANCE", "Compagnie d'assurance"),
                            ("MUTUELLE", "Mutuelle de santé"),
                            ("ENTREPRISE", "Entreprise"),
                        ],
                        default="IPM",
                        max_length=20,
                        verbose_name="type d'organisme",
                    ),
                ),
                (
                    "adresse",
                    models.CharField(
                        blank=True, default="", max_length=255, verbose_name="adresse"
                    ),
                ),
                (
                    "telephone",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=30,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Numero de telephone invalide (chiffres, espaces, tirets et + uniquement).",
                                regex="^\\+?[0-9 \\-]{7,20}$",
                            )
                        ],
                        verbose_name="téléphone",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        default="",
                        max_length=254,
                        verbose_name="adresse email",
                    ),
                ),
                (
                    "actif",
                    models.BooleanField(default=True, verbose_name="organisme actif"),
                ),
                (
                    "date_creation",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="date de création"
                    ),
                ),
            ],
            options={
                "verbose_name": "organisme",
                "verbose_name_plural": "organismes",
                "ordering": ["nom"],
            },
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Administrateur Général"),
                    ("GESTIONNAIRE", "Gestionnaire"),
                    ("ASSURE", "Assuré"),
                    ("MEDECIN", "Médecin"),
                    ("PHARMACIEN", "Pharmacien"),
                ],
                db_index=True,
                max_length=20,
                verbose_name="rôle",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="organisme",
            field=models.ForeignKey(
                blank=True,
                help_text="Obligatoire pour un compte Gestionnaire.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="utilisateurs",
                to="Plateform_medicale.organisme",
                verbose_name="organisme",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="organisme",
            field=models.ForeignKey(
                blank=True,
                help_text="Organisme (IPM / assureur) de rattachement de l'assuré.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="patients",
                to="Plateform_medicale.organisme",
                verbose_name="organisme",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="entreprise",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Entreprise employeur de l'assuré (optionnel).",
                max_length=150,
                verbose_name="entreprise",
            ),
        ),
        migrations.AddField(
            model_name="journalactivite",
            name="organisme",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="journaux",
                to="Plateform_medicale.organisme",
                verbose_name="organisme",
            ),
        ),
        migrations.AddField(
            model_name="journalactivite",
            name="organisme_libelle",
            field=models.CharField(
                blank=True,
                default="",
                max_length=200,
                verbose_name="organisme (figé)",
            ),
        ),
    ]
