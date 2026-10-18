from django.db import migrations, models


class Migration(migrations.Migration):
    # 0001_initial didn't list the implicit primary key, but the table was created
    # with an "id" column anyway. Only record it in the migration state.

    dependencies = [
        ("pretix_regid", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="registrationid",
                    name="id",
                    field=models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
            ],
        ),
    ]
