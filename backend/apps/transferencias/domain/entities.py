"""Entidad pura de dominio para una transferencia entre sucursales."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from apps.movimientos.domain.value_objects import TipoUnidad

from .value_objects import EstadoTransferencia

# Reutiliza TipoUnidad del dominio de movimientos en vez de duplicarlo: es
# un import domain -> domain entre bounded contexts, cero dependencia de
# Django, así que sigue respetando la regla de "use_cases/domain no
# importan Django".


@dataclass(frozen=True)
class Transferencia:
    """
    Solicitud de mover stock de una sucursal a otra (HU12).

    Flujo: se SOLICITA (PENDIENTE, el stock no se mueve) y un Administrador
    o Supervisor la COMPLETA (se registran la salida en origen y la entrada
    en destino) o la RECHAZA con motivo. `cantidad_unidades` se fija al
    solicitar, igual que en los movimientos.
    """

    id: Optional[int]
    herramienta_id: int
    sucursal_origen_id: int
    sucursal_destino_id: int
    cantidad: int
    tipo_unidad: TipoUnidad
    cantidad_unidades: int
    estado: EstadoTransferencia
    usuario_id: int  # quien la solicitó
    creado_en: Optional[datetime] = None
    # Resolución (completar o rechazar): quién, cuándo y, si se rechazó, por qué.
    resuelto_por_id: Optional[int] = None
    resuelto_en: Optional[datetime] = None
    motivo_rechazo: str = ""
    # Movimientos generados al completarla (trazabilidad con el historial).
    movimiento_salida_id: Optional[int] = None
    movimiento_entrada_id: Optional[int] = None
    # Solo para mostrar; los completa el repositorio al leer.
    usuario_username: Optional[str] = None
    resuelto_por_username: Optional[str] = None
