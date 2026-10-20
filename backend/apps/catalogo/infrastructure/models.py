from django.conf import settings
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
    # HU7: costo de compra de una unidad. Mayor que cero lo valida el caso
    # de uso; cada cambio se guarda en HistorialCosto.
    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Costo de compra de una unidad.",
        db_column="costo_unitario_herramienta",
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


class HistorialCosto(models.Model):
    """HU7: cada cambio del costo unitario de una herramienta, con quién y
    cuándo lo hizo. Solo se insertan filas (nunca se editan ni se borran).
    PROTECT: una herramienta o un usuario con historial no se borra, para
    no perder la trazabilidad de los costos."""

    id = models.BigAutoField(primary_key=True, db_column="cod_historial_costo")
    herramienta = models.ForeignKey(
        Herramienta, on_delete=models.PROTECT, related_name="historial_costos", db_column="cod_herramienta"
    )
    costo_anterior = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, db_column="costo_anterior_historial_costo"
    )
    costo_nuevo = models.DecimalField(max_digits=12, decimal_places=2, db_column="costo_nuevo_historial_costo")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", db_column="cod_usuario"
    )
    fecha = models.DateTimeField(auto_now_add=True, db_column="fecha_historial_costo")

    class Meta:
        app_label = "catalogo"
        db_table = "historial_costos"
        verbose_name = "Cambio de costo"
        verbose_name_plural = "Historial de costos"
        # Se consulta siempre por herramienta, del más reciente al más antiguo.
        indexes = [models.Index(fields=["herramienta", "-fecha"], name="historial_costo_herr_fecha_idx")]

    def __str__(self) -> str:
        return f"{self.herramienta_id}: {self.costo_anterior} -> {self.costo_nuevo}"
