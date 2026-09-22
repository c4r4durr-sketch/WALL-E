"""
Reglas puras de stock (sin Django).

El stock no se guarda en ninguna tabla: se DERIVA de los movimientos
(entradas suman, salidas restan). Así no puede desincronizarse del
historial, que es la fuente de verdad auditable.
"""

from .value_objects import TipoMovimiento

# Cómo afecta cada tipo de movimiento al stock de su sucursal.
EFECTO_EN_STOCK = {
    TipoMovimiento.ENTRADA: +1,
    TipoMovimiento.SALIDA: -1,
}


def stock_desde_totales(unidades_por_tipo: dict[TipoMovimiento, int]) -> int:
    """Stock en unidades a partir del total de unidades de cada tipo de
    movimiento (ej. {ENTRADA: 50, SALIDA: 12} -> 38)."""
    return sum(
        EFECTO_EN_STOCK[TipoMovimiento(tipo)] * unidades
        for tipo, unidades in unidades_por_tipo.items()
    )
