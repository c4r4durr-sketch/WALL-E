"""
Reglas puras de stock y demanda (sin Django).

El stock no se guarda en ninguna tabla: se DERIVA de los movimientos
(entradas, ajustes positivos y transferencias recibidas suman; salidas,
ajustes negativos y transferencias enviadas restan).
Así no puede desincronizarse del historial, que es la fuente de verdad
auditable.
"""

from .value_objects import TipoMovimiento

# Cómo afecta cada tipo de movimiento al stock de su sucursal.
EFECTO_EN_STOCK = {
    TipoMovimiento.ENTRADA: +1,
    TipoMovimiento.SALIDA: -1,
    TipoMovimiento.AJUSTE_POSITIVO: +1,
    TipoMovimiento.AJUSTE_NEGATIVO: -1,
    TipoMovimiento.TRANSFERENCIA_SALIDA: -1,
    TipoMovimiento.TRANSFERENCIA_ENTRADA: +1,
}

# Solo las ventas/salidas reales del mostrador reflejan demanda. Un ajuste
# negativo corrige un error de conteo, no es una venta: si contara,
# inflaría la demanda que usan EOQ (HU17) y la clasificación ABC.
TIPOS_QUE_CUENTAN_COMO_DEMANDA = frozenset({TipoMovimiento.SALIDA})


def resta_stock(tipo: TipoMovimiento) -> bool:
    """True si el movimiento descuenta stock (y por lo tanto debe validarse
    que no lo deje en negativo)."""
    return EFECTO_EN_STOCK[TipoMovimiento(tipo)] < 0


def cuenta_como_demanda(tipo: TipoMovimiento) -> bool:
    return TipoMovimiento(tipo) in TIPOS_QUE_CUENTAN_COMO_DEMANDA


def stock_desde_totales(unidades_por_tipo: dict[TipoMovimiento, int]) -> int:
    """Stock en unidades a partir del total de unidades de cada tipo de
    movimiento (ej. {ENTRADA: 50, SALIDA: 12} -> 38)."""
    return sum(
        EFECTO_EN_STOCK[TipoMovimiento(tipo)] * unidades
        for tipo, unidades in unidades_por_tipo.items()
    )
