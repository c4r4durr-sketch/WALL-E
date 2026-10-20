"""Puerto de repositorio de proveedores. Ver justificación en
apps/usuarios/domain/repositories.py."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Proveedor


class ProveedorRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, proveedor_id: int) -> Optional[Proveedor]:
        ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Optional[Proveedor]:
        """Búsqueda exacta sin distinguir mayúsculas (para la unicidad)."""
        ...

    @abstractmethod
    def listar(self, buscar: str = "", solo_activos: bool = False) -> list[Proveedor]:
        """Ordenados por nombre. `buscar` filtra por nombre (contiene, sin
        distinguir mayúsculas)."""
        ...

    @abstractmethod
    def guardar(self, proveedor: Proveedor) -> Proveedor:
        """Crea el proveedor si id es None; si no, lo actualiza. Lanza
        NombreProveedorDuplicadoError si la base rechaza el nombre."""
        ...

    @abstractmethod
    def eliminar(self, proveedor_id: int) -> None:
        """Lanza ProveedorEnUsoError si tiene herramientas asociadas."""
        ...
