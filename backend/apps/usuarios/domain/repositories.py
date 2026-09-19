"""
Puertos (interfaces) de repositorio para el dominio de usuarios.

Son ABCs sin ninguna dependencia de Django. use_cases depende de estas
interfaces, no de una implementación concreta (Inversión de Dependencias):
así los casos de uso se pueden probar con un fake/mock que las implemente,
sin necesitar una base de datos real.

La implementación concreta (con el ORM de Django) vive en
infrastructure/repositories.py y se inyecta en cada use case desde
interfaces/api/views.py.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Sucursal, Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        ...

    @abstractmethod
    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        ...

    @abstractmethod
    def listar(self) -> list[Usuario]:
        ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario:
        ...


class SucursalRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, sucursal_id: int) -> Optional[Sucursal]:
        ...

    @abstractmethod
    def listar(self) -> list[Sucursal]:
        ...
