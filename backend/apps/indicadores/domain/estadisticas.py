"""
Reportes estadísticos (página /reportes): DTOs, el periodo del reporte y
las reglas puras que no son una suma (Pareto ABC, meses del rango). Sin
Django: las sumas y conteos los hace el repositorio
(infrastructure/estadisticas.py) con el ORM, y los casos de uso
(use_cases/estadisticas.py) arman la respuesta.

Todos los reportes reciben el mismo filtro: desde, hasta (días de La Paz,
inclusive) y sucursal. Los que son una foto del inventario (stock por
sucursal, antigüedad, valor del inventario) se calculan al cierre del día
"hasta": "desde" no cambia cuánto stock había ese día.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Optional

from .entities import UMBRAL_A, UMBRAL_B


@dataclass(frozen=True)
class Periodo:
    desde: date
    hasta: date
    # None = todas las sucursales (solo el Administrador).
    sucursal_id: Optional[int]


def periodo_por_defecto(hoy: date) -> tuple[date, date]:
    """Los últimos 12 meses calendario, incluido el actual (el atajo
    "12 meses" de la pantalla)."""
    mes = hoy.year * 12 + hoy.month - 1 - 11
    return date(mes // 12, mes % 12 + 1, 1), hoy


def errores_de_periodo(desde: date, hasta: date, hoy: date) -> dict[str, str]:
    """campo -> mensaje; vacío si el periodo es válido."""
    errores = {}
    if desde > hoy:
        errores["desde"] = "La fecha no puede ser posterior a hoy."
    if hasta > hoy:
        errores["hasta"] = "La fecha no puede ser posterior a hoy."
    if "hasta" not in errores and hasta < desde:
        errores["hasta"] = "“Hasta” no puede ser anterior a “Desde”."
    return errores


def meses_del_rango(desde: date, hasta: date) -> list[date]:
    """Primer día de cada mes entre desde y hasta, los dos incluidos."""
    meses = []
    actual = date(desde.year, desde.month, 1)
    while actual <= hasta:
        meses.append(actual)
        actual = date(actual.year + actual.month // 12, actual.month % 12 + 1, 1)
    return meses


# --- Lo que devuelve el repositorio (sumas ya hechas por la base) ---


@dataclass(frozen=True)
class UnidadesDelMes:
    mes: date  # primer día del mes (La Paz)
    tipo_movimiento: str
    unidades: int


@dataclass(frozen=True)
class VentaHerramienta:
    """Salidas de una herramienta en el periodo. monto = unidades × costo
    unitario actual (None si no tiene costo cargado)."""

    herramienta_id: int
    codigo: str
    nombre: str
    unidades: int
    monto: Optional[Decimal]


@dataclass(frozen=True)
class StockSucursal:
    """Stock al cierre de "hasta". valor = stock × costo unitario, solo de
    las herramientas con costo; unidades_sin_costo dice cuántas quedan
    fuera del valor."""

    sucursal_id: int
    nombre: str
    unidades: int
    valor: Decimal
    unidades_sin_costo: int


@dataclass(frozen=True)
class InventarioHerramienta:
    """Stock de una herramienta en una sucursal al cierre de "hasta", con
    las fechas que necesita la antigüedad (domain/antiguedad.py)."""

    herramienta_id: int
    sucursal_id: int
    stock: int
    costo_unitario: Optional[Decimal]
    primer_movimiento: datetime
    ultima_salida: Optional[datetime]


@dataclass(frozen=True)
class TransferenciasDelMes:
    mes: date
    estado: str
    cantidad: int


# --- Lo que devuelven los casos de uso ---


@dataclass(frozen=True)
class MovimientosMes:
    mes: date
    entradas: int
    salidas: int
    ajustes_positivos: int
    ajustes_negativos: int


@dataclass(frozen=True)
class MovimientosPorMes:
    periodo: Periodo
    meses: tuple[MovimientosMes, ...]  # vacío si no hubo movimientos


@dataclass(frozen=True)
class TopHerramientas:
    periodo: Periodo
    herramientas: tuple[VentaHerramienta, ...]


@dataclass(frozen=True)
class StockPorSucursal:
    periodo: Periodo
    sucursales: tuple[StockSucursal, ...]
    total_unidades: int
    total_valor: Decimal


@dataclass(frozen=True)
class PuntoPareto:
    herramienta_id: int
    codigo: str
    nombre: str
    valor: Decimal
    porcentaje: float
    porcentaje_acumulado: float
    clase: str


@dataclass(frozen=True)
class TotalClase:
    clase: str
    herramientas: int
    valor: Decimal
    porcentaje_valor: float


@dataclass(frozen=True)
class EstadisticaABC:
    """ABC por valor vendido en el periodo (unidades × costo). Las
    herramientas sin ventas cuentan en C; las que vendieron sin costo
    cargado no se pueden valorar y se informan aparte."""

    periodo: Periodo
    clases: tuple[TotalClase, ...]  # A, B y C; vacío si no hubo ventas
    pareto: tuple[PuntoPareto, ...]
    valor_total: Decimal
    herramientas_sin_costo: int


@dataclass(frozen=True)
class TramoValor:
    tramo: str
    herramientas: int  # pares herramienta/sucursal con stock en el tramo
    unidades: int
    valor: Decimal


@dataclass(frozen=True)
class AntiguedadPorTramo:
    periodo: Periodo
    tramos: tuple[TramoValor, ...]  # los cuatro; vacío si no hay stock
    valor_total: Decimal
    lineas_sin_costo: int


@dataclass(frozen=True)
class TransferenciasMes:
    mes: date
    pendientes: int
    completadas: int
    rechazadas: int


@dataclass(frozen=True)
class CantidadEstado:
    estado: str
    cantidad: int


@dataclass(frozen=True)
class EstadisticaTransferencias:
    periodo: Periodo
    por_estado: tuple[CantidadEstado, ...]  # vacío si no hubo
    por_mes: tuple[TransferenciasMes, ...]
    total: int


@dataclass(frozen=True)
class ResumenEstadistico:
    periodo: Periodo
    total_movimientos: int
    unidades_vendidas: int
    valor_inventario: Decimal
    # Estado de hoy, como el panel: la alerta de reorden mira el stock de
    # todas las sucursales juntas.
    alertas_reorden: int
    herramientas_estancadas: int


# --- Regla pura: Pareto ABC por valor ---


def clasificar_por_valor(
    ventas: Iterable[VentaHerramienta], sin_ventas: int
) -> tuple[tuple[TotalClase, ...], tuple[PuntoPareto, ...], Decimal]:
    """Misma regla que la Clasificación ABC (use_cases/clasificar_abc.py),
    pero con dinero: se ordena de mayor a menor valor y se clasifica por el
    acumulado ANTERIOR a cada herramienta (A < 80 %, B < 95 %, C el resto).
    `sin_ventas` herramientas del catálogo suman a C con valor 0."""
    valoradas = sorted(
        (v for v in ventas if v.monto is not None and v.monto > 0),
        key=lambda v: (-v.monto, v.codigo),
    )
    total = sum((v.monto for v in valoradas), Decimal("0"))
    if not total:
        return (), (), Decimal("0")

    puntos = []
    acumulado = 0.0
    for venta in valoradas:
        clase = "A" if acumulado < UMBRAL_A else "B" if acumulado < UMBRAL_B else "C"
        porcentaje = float(venta.monto * 100 / total)
        acumulado += porcentaje
        puntos.append(PuntoPareto(
            herramienta_id=venta.herramienta_id,
            codigo=venta.codigo,
            nombre=venta.nombre,
            valor=venta.monto,
            porcentaje=round(porcentaje, 2),
            porcentaje_acumulado=round(min(acumulado, 100.0), 2),
            clase=clase,
        ))

    clases = []
    for clase in ("A", "B", "C"):
        de_la_clase = [p for p in puntos if p.clase == clase]
        valor = sum((p.valor for p in de_la_clase), Decimal("0"))
        clases.append(TotalClase(
            clase=clase,
            herramientas=len(de_la_clase) + (sin_ventas if clase == "C" else 0),
            valor=valor,
            porcentaje_valor=round(float(valor * 100 / total), 2),
        ))
    return tuple(clases), tuple(puntos), total
