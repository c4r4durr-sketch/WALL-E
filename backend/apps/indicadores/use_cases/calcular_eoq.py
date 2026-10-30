"""
Caso de uso: Cantidad Económica de Pedido (EOQ, HU17) y su ajuste a cajas
cerradas (HU20).

Fórmula: EOQ = raiz(2 * D * S / H)  (domain/formulas.py)
  D = demanda anual: la OBSERVADA (salidas reales de los últimos 12 meses,
      HU21) o, si no hubo ventas, la estimada del catálogo
  S = costo de hacer un pedido
  H = costo de almacenamiento por unidad al año

Se informan las dos demandas (estimada y observada) y cuál se usó. Ajustes
y transferencias no cuentan como venta. El panel y el ROP eligen D con la
misma regla (formulas.demanda_para_formulas).

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


def ventas_de_12_meses(movimientos: MovimientoRepository, ahora: datetime) -> dict[int, int]:
    """HU21: unidades vendidas por herramienta en los últimos
    PERIODO_DEMANDA_DIAS (solo salidas reales). Una consulta para todas."""
    return movimientos.unidades_por_herramienta(
        TIPOS_QUE_CUENTAN_COMO_DEMANDA, desde=ahora - timedelta(days=PERIODO_DEMANDA_DIAS)
    )


def resultado_eoq(herramienta: Herramienta, demanda_observada: int = 0) -> ResultadoEOQ:
    """Cálculo puro para una herramienta ya cargada (lo reutiliza el panel)."""
    demanda, fuente = formulas.demanda_para_formulas(herramienta.demanda_anual, demanda_observada)
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
        demanda_anual=herramienta.demanda_anual,
        costo_pedido=costo_pedido,
        costo_almacenamiento_unitario=costo_almacenamiento,
        unidades_por_caja=herramienta.unidades_por_caja,
        eoq=None if eoq is None else round(eoq, 2),
        eoq_ajustado_cajas=None if eoq is None else formulas.ajustar_a_cajas(eoq, herramienta.unidades_por_caja),
        demanda_observada=demanda_observada,
        demanda_usada=demanda,
        fuente_demanda=fuente,
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
    return resultado_eoq(herramienta, ventas_de_12_meses(movimientos, ahora).get(herramienta_id, 0))
