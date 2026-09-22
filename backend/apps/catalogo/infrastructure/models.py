from django.core.validators import MinValueValidator
from django.db import models


class Herramienta(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=150)
    modelo = models.CharField(max_length=100, blank=True)
    # Mínimo 1: una caja de 0 unidades rompería la conversión caja <-> unidad.
    unidades_por_caja = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    # Datos de entrada para EOQ (HU15/HU17) y ROP (HU16/HU18). Opcionales:
    # las herramientas ya cargadas no los tienen, y sin ellos las fórmulas
    # de indicadores/domain/formulas.py simplemente devuelven None.
    demanda_anual = models.PositiveIntegerField(
        null=True, blank=True, help_text="D: unidades vendidas al año (estimado)."
    )
    costo_pedido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="S: costo fijo de hacer un pedido al proveedor.",
    )
    costo_almacenamiento_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="H: costo de almacenar una unidad durante un año.",
    )
    tiempo_entrega_dias = models.PositiveIntegerField(
        null=True, blank=True, help_text="Días que tarda el proveedor en entregar un pedido."
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "catalogo"
        verbose_name = "Herramienta"
        verbose_name_plural = "Herramientas"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"
