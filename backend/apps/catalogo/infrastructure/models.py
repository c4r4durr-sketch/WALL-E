from django.core.validators import MinValueValidator
from django.db import models


class Herramienta(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="cod_herramienta")
    codigo = models.CharField(max_length=30, unique=True, db_column="codigo_fabrica_herramienta")
    nombre = models.CharField(max_length=150, db_column="nombre_herramienta")
    modelo = models.CharField(max_length=100, blank=True, db_column="modelo_herramienta")
    # Mínimo 1: una caja de 0 unidades rompería la conversión caja <-> unidad.
    unidades_por_caja = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], db_column="unidades_por_caja_herramienta"
    )

    # Datos de entrada para EOQ (HU15/HU17) y ROP (HU16/HU18). Opcionales:
    # las herramientas ya cargadas no los tienen, y sin ellos las fórmulas
    # de indicadores/domain/formulas.py simplemente devuelven None.
    demanda_anual = models.PositiveIntegerField(
        null=True, blank=True, help_text="D: unidades vendidas al año (estimado).",
        db_column="demanda_anual_herramienta",
    )
    costo_pedido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="S: costo fijo de hacer un pedido al proveedor.",
        db_column="costo_pedido_herramienta",
    )
    costo_almacenamiento_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="H: costo de almacenar una unidad durante un año.",
        db_column="costo_almacenamiento_herramienta",
    )
    tiempo_entrega_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Días que tarda el proveedor en entregar un pedido.",
        db_column="dias_entrega_herramienta",
    )

    creado_en = models.DateTimeField(auto_now_add=True, db_column="fecha_registro_herramienta")
    actualizado_en = models.DateTimeField(auto_now=True, db_column="fecha_actualizacion_herramienta")

    class Meta:
        app_label = "catalogo"
        db_table = "herramientas"
        verbose_name = "Herramienta"
        verbose_name_plural = "Herramientas"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"
