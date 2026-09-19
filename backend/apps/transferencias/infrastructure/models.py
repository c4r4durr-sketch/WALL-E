from django.conf import settings
from django.db import models

from apps.movimientos.domain.value_objects import TipoUnidad

from ..domain.value_objects import EstadoTransferencia


class Transferencia(models.Model):
    herramienta = models.ForeignKey(
        "catalogo.Herramienta", on_delete=models.PROTECT, related_name="transferencias"
    )
    sucursal_origen = models.ForeignKey(
        "usuarios.Sucursal", on_delete=models.PROTECT, related_name="transferencias_salientes"
    )
    sucursal_destino = models.ForeignKey(
        "usuarios.Sucursal", on_delete=models.PROTECT, related_name="transferencias_entrantes"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transferencias"
    )

    cantidad = models.PositiveIntegerField()
    tipo_unidad = models.CharField(
        max_length=10, choices=[(t.value, t.value.title()) for t in TipoUnidad]
    )
    estado = models.CharField(
        max_length=12,
        choices=[(e.value, e.value.title()) for e in EstadoTransferencia],
        default=EstadoTransferencia.PENDIENTE.value,
    )

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "transferencias"
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.herramienta_id}: {self.sucursal_origen_id} -> {self.sucursal_destino_id}"
