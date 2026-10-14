from django.conf import settings
from django.db import models

from ..domain.value_objects import TipoMovimiento, TipoUnidad


class Movimiento(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="cod_movimiento")
    # Referencias por string ("app_label.Modelo") para no crear un import
    # circular entre apps; Django las resuelve en tiempo de app-loading.
    herramienta = models.ForeignKey(
        "catalogo.Herramienta",
        on_delete=models.PROTECT,
        related_name="movimientos",
        db_column="cod_herramienta",
    )
    sucursal = models.ForeignKey(
        "usuarios.Sucursal",
        on_delete=models.PROTECT,
        related_name="movimientos",
        db_column="cod_sucursal",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimientos",
        db_column="cod_usuario",
    )

    tipo_movimiento = models.CharField(
        max_length=25,
        choices=[(t.value, t.value.replace("_", " ").capitalize()) for t in TipoMovimiento],
        db_column="tipo_movimiento",
    )
    tipo_unidad = models.CharField(
        max_length=10,
        choices=[(t.value, t.value.title()) for t in TipoUnidad],
        db_column="tipo_unidad_movimiento",
    )
    cantidad = models.PositiveIntegerField(db_column="cantidad_movimiento")
    # Equivalente en unidades, fijado al registrar (ver domain/entities.py):
    # el stock se calcula con este campo, no recalculando cajas.
    cantidad_unidades = models.PositiveIntegerField(db_column="cantidad_unidades_movimiento")
    # Por qué se corrigió el stock. Obligatorio en ajustes (lo valida el
    # use_case, no la BD); vacío en entradas y salidas.
    motivo = models.CharField(max_length=255, blank=True, default="", db_column="motivo_movimiento")

    creado_en = models.DateTimeField(auto_now_add=True, db_column="fecha_movimiento")

    class Meta:
        app_label = "movimientos"
        db_table = "movimientos"
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.tipo_movimiento} {self.cantidad} {self.tipo_unidad} - {self.herramienta_id}"
