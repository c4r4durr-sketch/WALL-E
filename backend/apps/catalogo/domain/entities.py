"""Entidad pura de dominio para el catálogo. Sin dependencias de Django."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Herramienta:
    id: Optional[int]
    codigo: str
    nombre: str
    modelo: str
    # Cuántas unidades sueltas trae una caja por mayor de esta herramienta.
    # Lo usa movimientos/use_cases para convertir CAJA <-> UNIDAD; se
    # modela acá porque es un dato propio del producto, no del movimiento.
    unidades_por_caja: int
    # Datos de entrada para EOQ/ROP (ver indicadores/domain/formulas.py).
    # Opcionales: sin ellos el indicador correspondiente queda en None.
    demanda_anual: Optional[int] = None
    costo_pedido: Optional[Decimal] = None
    costo_almacenamiento_unitario: Optional[Decimal] = None
    tiempo_entrega_dias: Optional[int] = None
