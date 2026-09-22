"""
Agrega cantidad_unidades (unidades equivalentes fijadas al registrar).

Se hace en dos migraciones: esta agrega la columna como NULL y completa
las filas que ya existan (CAJA -> cantidad * unidades_por_caja actual de
la herramienta; UNIDAD -> cantidad); la 0004 la vuelve NOT NULL en una
transacción aparte (PostgreSQL no permite ALTER TABLE en la misma
transacción que acaba de actualizar esas filas).
"""

from django.db import migrations, models


def completar_unidades(apps, schema_editor):
    Movimiento = apps.get_model("movimientos", "Movimiento")
    for movimiento in Movimiento.objects.select_related("herramienta").filter(cantidad_unidades__isnull=True):
        factor = movimiento.herramienta.unidades_por_caja if movimiento.tipo_unidad == "CAJA" else 1
        movimiento.cantidad_unidades = movimiento.cantidad * factor
        movimiento.save(update_fields=["cantidad_unidades"])


class Migration(migrations.Migration):
    dependencies = [
        ("movimientos", "0002_initial"),
        ("catalogo", "0002_campos_eoq_rop"),
    ]

    operations = [
        migrations.AddField(
            model_name="movimiento",
            name="cantidad_unidades",
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RunPython(completar_unidades, migrations.RunPython.noop),
    ]
