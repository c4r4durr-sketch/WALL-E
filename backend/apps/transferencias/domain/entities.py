"""Entidad pura de dominio para una transferencia entre sucursales."""

from dataclasses import dataclass
from typing import Optional

from apps.movimientos.domain.value_objects import TipoUnidad

from .value_objects import EstadoTransferencia

# Reutiliza TipoUnidad del dominio de movimientos en vez de duplicarlo: es
# un import domain -> domain entre bounded contexts, cero dependencia de
# Django, así que sigue respetando la regla de "use_cases/domain no
# importan Django".


@dataclass(frozen=True)
class Transferencia:
    id: Optional[int]
    herramienta_id: int
    sucursal_origen_id: int
    sucursal_destino_id: int
    cantidad: int
    tipo_unidad: TipoUnidad
    estado: EstadoTransferencia
    usuario_id: int
