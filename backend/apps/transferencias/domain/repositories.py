"""Puerto de repositorio de transferencias. Ver justificación en
apps/usuarios/domain/repositories.py.

No hay eliminar A PROPÓSITO: una transferencia queda siempre en el
historial (completada o rechazada), igual que los movimientos."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Transferencia
from .value_objects import EstadoTransferencia


class TransferenciaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, transferencia_id: int) -> Optional[Transferencia]:
        ...

    @abstractmethod
    def obtener_para_resolver(self, transferencia_id: int) -> Optional[Transferencia]:
        """Como obtener_por_id, pero bloquea la transferencia hasta que
        termine la operación: evita que dos personas la completen a la vez
        (se moverían dos veces las unidades)."""
        ...

    @abstractmethod
    def listar(self, estado: Optional[EstadoTransferencia] = None) -> list[Transferencia]:
        """De la más reciente a la más antigua, con filtro opcional."""
        ...

    @abstractmethod
    def guardar(self, transferencia: Transferencia) -> Transferencia:
        """Crea si id es None; si no, actualiza el estado y la resolución."""
        ...
