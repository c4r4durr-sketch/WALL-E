"""Implementación (ORM) del repositorio de estadísticas.

Indicadores no tiene tablas propias: consulta los modelos de movimientos,
catálogo, transferencias y sucursales, siempre con agregaciones del ORM
(Sum, Count, TruncMonth), sin SQL a mano. Cada método es una o dos
consultas sin importar cuántos movimientos haya.

Los días son los de La Paz: __date y TruncMonth convierten creado_en (UTC
en la base) a TIME_ZONE antes de comparar o agrupar, como el cierre
diario."""

from datetime import date
from decimal import Decimal
from typing import Optional

from django.db.models import (
    Case,
    Count,
    DateField,
    DecimalField,
    F,
    IntegerField,
    Max,
    Min,
    Q,
    Sum,
    When,
)
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
from apps.movimientos.domain.stock import EFECTO_EN_STOCK, TIPOS_QUE_CUENTAN_COMO_DEMANDA
from apps.movimientos.domain.value_objects import TipoMovimiento
from apps.movimientos.infrastructure.models import Movimiento as MovimientoModel
from apps.transferencias.infrastructure.models import Transferencia as TransferenciaModel

from ..domain.estadisticas import (
    InventarioHerramienta,
    StockSucursal,
    TransferenciasDelMes,
    UnidadesDelMes,
    VentaHerramienta,
)
from ..domain.repositories import EstadisticasRepository

_MONTO = DecimalField(max_digits=18, decimal_places=2)
_TIPOS_QUE_SUMAN = [t.value for t, efecto in EFECTO_EN_STOCK.items() if efecto > 0]
_VENTAS = [t.value for t in TIPOS_QUE_CUENTAN_COMO_DEMANDA]

# Unidades con el signo que tienen en el stock (domain/stock.py): las
# entradas suman y las salidas restan, así Sum() da el stock.
_UNIDADES_CON_SIGNO = Case(
    When(tipo_movimiento__in=_TIPOS_QUE_SUMAN, then=F("cantidad_unidades")),
    default=F("cantidad_unidades") * -1,
    output_field=IntegerField(),
)
_CON_COSTO = Q(herramienta__costo_unitario__isnull=False)


def _movimientos(sucursal_id: Optional[int]):
    consulta = MovimientoModel.objects.all()
    return consulta if sucursal_id is None else consulta.filter(sucursal_id=sucursal_id)


def _del_periodo(desde: date, hasta: date, sucursal_id: Optional[int]):
    return _movimientos(sucursal_id).filter(creado_en__date__gte=desde, creado_en__date__lte=hasta)


def _mes():
    # Primer día del mes en hora de La Paz (Django pasa TIME_ZONE a date_trunc).
    return TruncMonth("creado_en", output_field=DateField())


class EstadisticasRepositoryDjango(EstadisticasRepository):
    def unidades_por_mes(self, desde, hasta, sucursal_id):
        filas = (
            _del_periodo(desde, hasta, sucursal_id)
            .annotate(mes=_mes())
            .values("mes", "tipo_movimiento")
            .annotate(unidades=Sum("cantidad_unidades"))
            .order_by("mes", "tipo_movimiento")
        )
        return [UnidadesDelMes(f["mes"], f["tipo_movimiento"], f["unidades"]) for f in filas]

    def total_movimientos(self, desde, hasta, sucursal_id):
        return _del_periodo(desde, hasta, sucursal_id).count()

    def ventas_por_herramienta(self, desde, hasta, sucursal_id):
        filas = (
            _del_periodo(desde, hasta, sucursal_id)
            .filter(tipo_movimiento__in=_VENTAS)
            .values("herramienta_id", "herramienta__codigo", "herramienta__nombre")
            .annotate(
                unidades=Sum("cantidad_unidades"),
                # Sin costo cargado, el producto es NULL y Sum da None.
                monto=Sum(F("cantidad_unidades") * F("herramienta__costo_unitario"), output_field=_MONTO),
            )
            .order_by("-unidades", "herramienta__codigo")
        )
        return [
            VentaHerramienta(
                herramienta_id=f["herramienta_id"],
                codigo=f["herramienta__codigo"],
                nombre=f["herramienta__nombre"],
                unidades=f["unidades"],
                monto=f["monto"],
            )
            for f in filas
        ]

    def total_herramientas(self):
        return HerramientaModel.objects.count()

    def stock_por_sucursal(self, hasta, sucursal_id):
        filas = (
            _movimientos(sucursal_id)
            .filter(creado_en__date__lte=hasta)
            .values("sucursal_id", "sucursal__nombre")
            .annotate(
                unidades=Sum(_UNIDADES_CON_SIGNO),
                # valor = Σ stock × costo; como es lineal, se puede sumar
                # movimiento por movimiento.
                valor=Sum(_UNIDADES_CON_SIGNO * F("herramienta__costo_unitario"), filter=_CON_COSTO, output_field=_MONTO),
                unidades_sin_costo=Sum(_UNIDADES_CON_SIGNO, filter=~_CON_COSTO),
            )
            .order_by("sucursal__nombre")
        )
        return [
            StockSucursal(
                sucursal_id=f["sucursal_id"],
                nombre=f["sucursal__nombre"],
                unidades=f["unidades"],
                valor=f["valor"] or Decimal("0"),
                unidades_sin_costo=f["unidades_sin_costo"] or 0,
            )
            for f in filas
        ]

    def inventario(self, hasta, sucursal_id):
        filas = (
            _movimientos(sucursal_id)
            .filter(creado_en__date__lte=hasta)
            .values("herramienta_id", "sucursal_id", "herramienta__costo_unitario")
            .annotate(
                stock=Sum(_UNIDADES_CON_SIGNO),
                primero=Min("creado_en"),
                ultima_salida=Max("creado_en", filter=Q(tipo_movimiento=TipoMovimiento.SALIDA.value)),
            )
            .order_by("herramienta_id", "sucursal_id")
        )
        return [
            InventarioHerramienta(
                herramienta_id=f["herramienta_id"],
                sucursal_id=f["sucursal_id"],
                stock=f["stock"],
                costo_unitario=f["herramienta__costo_unitario"],
                # En hora local, como resumen_inventario de movimientos.
                primer_movimiento=timezone.localtime(f["primero"]),
                ultima_salida=timezone.localtime(f["ultima_salida"]) if f["ultima_salida"] else None,
            )
            for f in filas
        ]

    def transferencias_por_mes(self, desde, hasta, sucursal_id):
        consulta = TransferenciaModel.objects.filter(creado_en__date__gte=desde, creado_en__date__lte=hasta)
        if sucursal_id is not None:
            consulta = consulta.filter(Q(sucursal_origen_id=sucursal_id) | Q(sucursal_destino_id=sucursal_id))
        filas = (
            consulta.annotate(mes=_mes())
            .values("mes", "estado")
            .annotate(cantidad=Count("id"))
            .order_by("mes", "estado")
        )
        return [TransferenciasDelMes(f["mes"], f["estado"], f["cantidad"]) for f in filas]
