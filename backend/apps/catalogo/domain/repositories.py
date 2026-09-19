"""Puerto de repositorio del catálogo. Ver justificación en
apps/usuarios/domain/repositories.py."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Herramienta


class HerramientaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, herramienta_id: int) -> Optional[Herramienta]:
        ...

    @abstractmethod
    def obtener_por_codigo(self, codigo: str) -> Optional[Herramienta]:
        ...

    @abstractmethod
    def listar(self) -> list[Herramienta]:
        ...

    @abstractmethod
    def guardar(self, herramienta: Herramienta) -> Herramienta:
        ...
