from django.conf import settings
from django.db import models

from apps.movimientos.domain.value_objects import TipoUnidad

from ..domain.value_objects import EstadoTransferencia


class Transferencia(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="cod_transferencia")
    herramienta = models.ForeignKey(
        "catalogo.Herramienta",
        on_delete=models.PROTECT,
        related_name="transferencias",
        db_column="cod_herramienta",
    )
    sucursal_origen = models.ForeignKey(
        "usuarios.Sucursal",
        on_delete=models.PROTECT,
        related_name="transferencias_salientes",
        db_column="cod_sucursal_origen",
    )
    sucursal_destino = models.ForeignKey(
        "usuarios.Sucursal",
        on_delete=models.PROTECT,
        related_name="transferencias_entrantes",
        db_column="cod_sucursal_destino",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transferencias",
        db_column="cod_usuario",
    )

    cantidad = models.PositiveIntegerField(db_column="cantidad_transferencia")
    tipo_unidad = models.CharField(
        max_length=10,
        choices=[(t.value, t.value.title()) for t in TipoUnidad],
        db_column="tipo_unidad_transferencia",
    )
    # Equivalente en unidades fijado al solicitar (ver domain/entities.py).
    cantidad_unidades = models.PositiveIntegerField(db_column="cantidad_unidades_transferencia")
    estado = models.CharField(
        max_length=12,
        choices=[(e.value, e.value.title()) for e in EstadoTransferencia],
        default=EstadoTransferencia.PENDIENTE.value,
        db_column="estado_transferencia",
    )

    # Resolución: quién la completó o rechazó, cuándo y (si se rechazó) por qué.
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        db_column="cod_usuario_resuelve",
    )
    resuelto_en = models.DateTimeField(null=True, blank=True, db_column="fecha_resolucion_transferencia")
    motivo_rechazo = models.CharField(
        max_length=255, blank=True, default="", db_column="motivo_rechazo_transferencia"
    )
    # Movimientos generados al completarla: une la transferencia con el
    # historial de stock de cada sucursal.
    movimiento_salida = models.OneToOneField(
        "movimientos.Movimiento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        db_column="cod_movimiento_salida",
    )
    movimiento_entrada = models.OneToOneField(
        "movimientos.Movimiento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        db_column="cod_movimiento_entrada",
    )

    creado_en = models.DateTimeField(auto_now_add=True, db_column="fecha_registro_transferencia")

    class Meta:
        app_label = "transferencias"
        db_table = "transferencias"
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.herramienta_id}: {self.sucursal_origen_id} -> {self.sucursal_destino_id}"
