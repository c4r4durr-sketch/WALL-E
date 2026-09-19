"""Puerto de repositorio de transferencias. Ver justificación en
apps/usuarios/domain/repositories.py."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Transferencia


class TransferenciaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, transferencia_id: int) -> Optional[Transferencia]:
        ...

    @abstractmethod
    def listar(self) -> list[Transferencia]:
        ...

    @abstractmethod
    def guardar(self, transferencia: Transferencia) -> Transferencia:
        ...
