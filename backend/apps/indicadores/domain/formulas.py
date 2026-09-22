"""
Fórmulas puras de inventario (EOQ, ROP y conversión caja <-> unidad).

Reemplazan a las funciones SQL fn_calcular_eoq, fn_calcular_rop y
fn_ajustar_a_cajas del script descartado
(docs/archivo/base_datos_descartado.sql). Se mantiene el mismo
comportamiento, incluidos los casos borde (devolver None cuando falta un
dato en vez de fallar), para que la regla de negocio sea la misma que se
documentó en el informe.

Son funciones de dominio puro: no importan Django ni tocan la base de
datos, así que se pueden probar con simples asserts y reutilizar desde
cualquier use_case (indicadores, movimientos, transferencias).
"""

import math
from typing import Optional

DIAS_POR_ANIO = 365


def calcular_eoq(
    demanda_anual: Optional[float],
    costo_pedido: Optional[float],
    costo_almacenamiento_unitario: Optional[float],
) -> Optional[float]:
    """HU17: Cantidad Económica de Pedido, EOQ = raiz(2 * D * S / H).

    Devuelve None si falta algún dato o si H <= 0 (igual que la función
    SQL original: sin costo de almacenamiento la fórmula no tiene sentido).
    """
    if demanda_anual is None or costo_pedido is None:
        return None
    if costo_almacenamiento_unitario is None or costo_almacenamiento_unitario <= 0:
        return None
    if demanda_anual < 0 or costo_pedido < 0:
        raise ValueError("La demanda anual y el costo de pedido no pueden ser negativos.")
    return math.sqrt((2 * demanda_anual * costo_pedido) / costo_almacenamiento_unitario)


def calcular_rop(
    demanda_anual: Optional[float],
    tiempo_entrega_dias: Optional[int],
) -> Optional[float]:
    """HU18: Punto de Reorden, ROP = (D / 365) * tiempo de entrega en días.

    Devuelve None si falta la demanda o el tiempo de entrega.
    """
    if demanda_anual is None or tiempo_entrega_dias is None:
        return None
    if demanda_anual < 0 or tiempo_entrega_dias < 0:
        raise ValueError("La demanda anual y el tiempo de entrega no pueden ser negativos.")
    return (demanda_anual / DIAS_POR_ANIO) * tiempo_entrega_dias


def ajustar_a_cajas(cantidad_unidades: float, unidades_por_caja: Optional[int]) -> float:
    """HU20: redondea una cantidad en unidades hacia ARRIBA al múltiplo de
    caja cerrada más cercano (no se le puede pedir media caja al proveedor).

    Ej: 30 unidades con cajas de 12 -> 36 unidades (3 cajas).
    Si la herramienta no tiene un factor de caja válido, se devuelve la
    cantidad tal cual.
    """
    if unidades_por_caja is None or unidades_por_caja <= 0:
        return cantidad_unidades
    return math.ceil(cantidad_unidades / unidades_por_caja) * unidades_por_caja


def cajas_a_unidades(cantidad_cajas: int, unidades_por_caja: int) -> int:
    """HU26: convierte cajas cerradas a unidades sueltas (1 caja = N unidades).

    Es la conversión que usan los movimientos registrados en CAJA: el stock
    siempre se lleva en unidades.
    """
    if unidades_por_caja <= 0:
        raise ValueError("unidades_por_caja debe ser mayor que 0.")
    if cantidad_cajas < 0:
        raise ValueError("La cantidad de cajas no puede ser negativa.")
    return cantidad_cajas * unidades_por_caja


def unidades_a_cajas(cantidad_unidades: int, unidades_por_caja: int) -> tuple[int, int]:
    """HU26: descompone unidades en (cajas completas, unidades sueltas).

    Ej: 30 unidades con cajas de 12 -> (2, 6).
    """
    if unidades_por_caja <= 0:
        raise ValueError("unidades_por_caja debe ser mayor que 0.")
    if cantidad_unidades < 0:
        raise ValueError("La cantidad de unidades no puede ser negativa.")
    return divmod(cantidad_unidades, unidades_por_caja)
