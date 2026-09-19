"""
Entidad pura de dominio para un movimiento de inventario.

A propósito NO incluye un método `cantidad_en_unidades()` todavía: esa
conversión (cantidad * unidades_por_caja cuando tipo_unidad es CAJA) es una
regla de negocio real, y la tarea actual es solo dejar el esqueleto sin
implementar lógica de negocio. Ese método (o un use_case aparte) es el
lugar correcto donde agregarla después.
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
    usuario_id: int
    creado_en: Optional[datetime] = None
