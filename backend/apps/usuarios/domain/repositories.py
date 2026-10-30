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
        """Búsqueda sin distinguir mayúsculas: "Ana" y "ana" son la misma
        cuenta a efectos de unicidad."""
        ...

    @abstractmethod
    def listar(self) -> list[Usuario]:
        ...

    @abstractmethod
    def crear(self, usuario: Usuario, password: str) -> Usuario:
        """Guarda la cuenta nueva con la contraseña cifrada."""
        ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario:
        """Guarda los datos de la cuenta; no toca la contraseña."""
        ...

    @abstractmethod
    def establecer_password(self, usuario_id: int, password: str) -> None:
        """Reemplaza la contraseña (cifrada); la anterior deja de servir."""
        ...

    @abstractmethod
    def contar_administradores_activos(self, excluir_id: Optional[int] = None) -> int:
        ...


class ValidadorPassword(ABC):
    """Puerto para la política de contraseñas. La implementación concreta
    usa los AUTH_PASSWORD_VALIDATORS de Django (infraestructura)."""

    @abstractmethod
    def errores(self, password: str, usuario: Usuario) -> list[str]:
        """Mensajes en español de lo que no cumple; lista vacía si es válida."""
        ...


class SucursalRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, sucursal_id: int) -> Optional[Sucursal]:
        ...

    @abstractmethod
    def listar(self) -> list[Sucursal]:
        ...
