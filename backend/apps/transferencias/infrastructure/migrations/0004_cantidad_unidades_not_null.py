from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transferencias", "0003_flujo_aprobacion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transferencia",
            name="cantidad_unidades",
            field=models.PositiveIntegerField(),
        ),
    ]
