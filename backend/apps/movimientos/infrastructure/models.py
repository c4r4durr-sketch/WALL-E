from django.conf import settings
from django.db import models

from ..domain.value_objects import TipoMovimiento, TipoUnidad


class Movimiento(models.Model):
    # Referencias por string ("app_label.Modelo") para no crear un import
    # circular entre apps; Django las resuelve en tiempo de app-loading.
    herramienta = models.ForeignKey(
        "catalogo.Herramienta", on_delete=models.PROTECT, related_name="movimientos"
    )
    sucursal = models.ForeignKey(
        "usuarios.Sucursal", on_delete=models.PROTECT, related_name="movimientos"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos"
    )

    tipo_movimiento = models.CharField(
        max_length=10, choices=[(t.value, t.value.title()) for t in TipoMovimiento]
    )
    tipo_unidad = models.CharField(
        max_length=10, choices=[(t.value, t.value.title()) for t in TipoUnidad]
    )
    cantidad = models.PositiveIntegerField()
    # Equivalente en unidades, fijado al registrar (ver domain/entities.py):
    # el stock se calcula con este campo, no recalculando cajas.
    cantidad_unidades = models.PositiveIntegerField()

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "movimientos"
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.tipo_movimiento} {self.cantidad} {self.tipo_unidad} - {self.herramienta_id}"
