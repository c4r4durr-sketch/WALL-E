from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("movimientos", "0003_cantidad_unidades"),
    ]

    operations = [
        migrations.AlterField(
            model_name="movimiento",
            name="cantidad_unidades",
            field=models.PositiveIntegerField(),
        ),
    ]
