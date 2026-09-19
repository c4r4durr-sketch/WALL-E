"""
Caso de uso: Cantidad Económica de Pedido (EOQ).

Fórmula: EOQ = raiz(2 * D * S / H)
  D = demanda anual (unidades)
  S = costo de hacer un pedido
  H = costo de almacenamiento por unidad al año

Caso de uso puro: no importa Django ni toca la base de datos. Recibe D, S y
H ya calculados; quien arma esos valores (a partir del historial de
movimientos) es la vista o un caso de uso de más alto nivel.

Sin implementar todavía (solo el esqueleto y la fórmula documentada).
"""

from ..domain.entities import ResultadoEOQ


def calcular_eoq(
    herramienta_id: int,
    demanda_anual: int,
    costo_pedido: float,
    costo_almacenamiento_unitario: float,
) -> ResultadoEOQ:
    raise NotImplementedError
