import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("pretixbase", "0118_auto_20190423_0839"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistrationID",
            fields=[
                ("regid", models.PositiveIntegerField(verbose_name="RegistrationID")),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="regids",
                        to="pretixbase.Event",
                    ),
                ),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="regids",
                        to="pretixbase.Order",
                    ),
                ),
            ],
            options={
                "unique_together": {("event", "order")},
            },
        )
    ]
