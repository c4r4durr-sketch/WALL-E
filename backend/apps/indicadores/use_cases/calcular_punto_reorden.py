"""
Caso de uso: Punto de Reorden (ROP, HU18).

Fórmula: ROP = (D / 365) * tiempo de entrega en días  (domain/formulas.py)

Se compara con el stock TOTAL de la herramienta (todas las sucursales):
si stock_total <= ROP, hay que pedir al proveedor. Es la misma regla que
usa el panel de inicio para sus alertas.

Puro: recibe repositorios como interfaces; no importa Django.
"""

from apps.catalogo.domain.entities import Herramienta
from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import stock_desde_totales

from ..domain import formulas
from ..domain.entities import ResultadoROP


def resultado_rop(herramienta: Herramienta, stock_total: int) -> ResultadoROP:
    """Cálculo puro para una herramienta ya cargada (lo reutiliza el panel)."""
    demanda = herramienta.demanda_anual
    entrega = herramienta.tiempo_entrega_dias
    faltantes = tuple(
        campo for campo, valor in (("demanda_anual", demanda), ("tiempo_entrega_dias", entrega))
        if valor is None
    )
    rop = formulas.calcular_rop(None if demanda is None else float(demanda), entrega)
    return ResultadoROP(
        herramienta_id=herramienta.id,
        codigo=herramienta.codigo,
        nombre=herramienta.nombre,
        demanda_anual=demanda,
        demanda_diaria_promedio=None if demanda is None else round(demanda / formulas.DIAS_POR_ANIO, 4),
        lead_time_dias=entrega,
        punto_reorden=None if rop is None else round(rop, 2),
        stock_total=stock_total,
        requiere_reorden=rop is not None and stock_total <= rop,
        datos_faltantes=faltantes,
    )


def calcular_punto_reorden(
    herramientas: HerramientaRepository,
    movimientos: MovimientoRepository,
    herramienta_id: int,
) -> ResultadoROP:
    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaNoEncontradaError(herramienta_id)
    stock_total = sum(
        stock_desde_totales(fila.unidades_por_tipo)
        for fila in movimientos.resumen_inventario()
        if fila.herramienta_id == herramienta_id
    )
    return resultado_rop(herramienta, stock_total)
