"""
Entidad pura de dominio para un movimiento de inventario.

`cantidad` + `tipo_unidad` es lo que el usuario registró en el mostrador
(ej. 2 CAJAS); `cantidad_unidades` es su equivalente en unidades sueltas,
calculado UNA vez al registrar (con el unidades_por_caja de ese momento) y
guardado. El stock se calcula siempre con `cantidad_unidades`: si mañana
cambia el tamaño de caja de la herramienta en el catálogo, el stock
histórico no se altera.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .value_objects import TipoMovimiento, TipoUnidad


@dataclass(frozen=True)
class Movimiento:
    id: Optional[int]
    herramienta_id: int
    sucursal_id: int
    tipo_movimiento: TipoMovimiento
    tipo_unidad: TipoUnidad
    cantidad: int
    cantidad_unidades: int
    usuario_id: int
    creado_en: Optional[datetime] = None
    # Solo para mostrar en el historial; lo completa el repositorio al leer.
    usuario_username: Optional[str] = None
