"""
Caso de uso: Cantidad Económica de Pedido (EOQ, HU17) y su ajuste a cajas
cerradas (HU20).

Fórmula: EOQ = raiz(2 * D * S / H)  (domain/formulas.py)
  D = demanda anual estimada (catálogo)
  S = costo de hacer un pedido
  H = costo de almacenamiento por unidad al año

D sale del catálogo (la misma que usa el panel). Además se informa la
demanda OBSERVADA (salidas reales de los últimos 12 meses, HU21) para
compararla con la estimada; ajustes y transferencias no cuentan como venta.

Puro: recibe repositorios como interfaces y la hora actual como parámetro.
"""

from datetime import datetime, timedelta

from apps.catalogo.domain.entities import Herramienta
from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import TIPOS_QUE_CUENTAN_COMO_DEMANDA

from ..domain import formulas
from ..domain.entities import PERIODO_DEMANDA_DIAS, ResultadoEOQ


def _a_float(valor):
    return None if valor is None else float(valor)


def resultado_eoq(herramienta: Herramienta, demanda_observada: int = 0) -> ResultadoEOQ:
    """Cálculo puro para una herramienta ya cargada (lo reutiliza el panel)."""
    demanda = herramienta.demanda_anual
    costo_pedido = _a_float(herramienta.costo_pedido)
    costo_almacenamiento = _a_float(herramienta.costo_almacenamiento_unitario)

    faltantes = []
    if demanda is None:
        faltantes.append("demanda_anual")
    if costo_pedido is None:
        faltantes.append("costo_pedido")
    if costo_almacenamiento is None or costo_almacenamiento <= 0:
        # Sin costo de almacenamiento (o en 0) la fórmula no tiene sentido.
        faltantes.append("costo_almacenamiento_unitario")

    eoq = formulas.calcular_eoq(_a_float(demanda), costo_pedido, costo_almacenamiento)
    return ResultadoEOQ(
        herramienta_id=herramienta.id,
        codigo=herramienta.codigo,
        nombre=herramienta.nombre,
        demanda_anual=demanda,
        costo_pedido=costo_pedido,
        costo_almacenamiento_unitario=costo_almacenamiento,
        unidades_por_caja=herramienta.unidades_por_caja,
        eoq=None if eoq is None else round(eoq, 2),
        eoq_ajustado_cajas=None if eoq is None else formulas.ajustar_a_cajas(eoq, herramienta.unidades_por_caja),
        demanda_observada=demanda_observada,
        datos_faltantes=tuple(faltantes),
    )


def calcular_eoq(
    herramientas: HerramientaRepository,
    movimientos: MovimientoRepository,
    herramienta_id: int,
    ahora: datetime,
) -> ResultadoEOQ:
    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaNoEncontradaError(herramienta_id)
    vendidas = movimientos.unidades_por_herramienta(
        TIPOS_QUE_CUENTAN_COMO_DEMANDA, desde=ahora - timedelta(days=PERIODO_DEMANDA_DIAS)
    )
    return resultado_eoq(herramienta, vendidas.get(herramienta_id, 0))
