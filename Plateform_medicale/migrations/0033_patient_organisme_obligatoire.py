import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Plateform_medicale", "0032_peupler_organisme_defaut"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patient",
            name="organisme",
            field=models.ForeignKey(
                help_text="Organisme (IPM / assureur) de rattachement de l'assuré.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="patients",
                to="Plateform_medicale.organisme",
                verbose_name="organisme",
            ),
        ),
    ]
