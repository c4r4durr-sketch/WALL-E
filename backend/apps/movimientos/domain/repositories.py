"""Puerto de repositorio de movimientos. Ver justificación en
apps/usuarios/domain/repositories.py.

No hay métodos de actualizar ni eliminar A PROPÓSITO: un movimiento
registrado es inmutable (HU13, auditable). Un error se corrige con un
movimiento nuevo, nunca editando el original."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Movimiento
from .value_objects import TipoMovimiento


class MovimientoRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, movimiento_id: int) -> Optional[Movimiento]:
        ...

    @abstractmethod
    def listar(
        self, herramienta_id: Optional[int] = None, sucursal_id: Optional[int] = None
    ) -> list[Movimiento]:
        """Historial, del más reciente al más antiguo, con filtros opcionales."""
        ...

    @abstractmethod
    def unidades_por_tipo(
        self, herramienta_id: int, sucursal_id: int
    ) -> dict[TipoMovimiento, int]:
        """Total de unidades registradas por tipo de movimiento para una
        herramienta en una sucursal (insumo de domain/stock.py)."""
        ...

    @abstractmethod
    def bloquear_stock(self, herramienta_id: int) -> None:
        """Impide que otra operación modifique el stock de esta herramienta
        hasta que termine la actual. Evita que dos salidas simultáneas
        pasen ambas la validación y dejen el stock en negativo."""
        ...

    @abstractmethod
    def guardar(self, movimiento: Movimiento) -> Movimiento:
        """Solo altas: el movimiento debe venir con id=None."""
        ...
