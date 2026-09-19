"""
Implementaciones concretas de los repositorios de domain/repositories.py,
usando el ORM de Django. Son el único lugar del proyecto que debería
mezclar "modelo ORM" con "entidad de dominio" (hacen la conversión entre
ambos mundos).

Se dejan los métodos declarados pero sin implementar (NotImplementedError):
la tarea actual es dejar el esqueleto listo, no la lógica de negocio. Jostin
completa el cuerpo de cada método cuando se implementen los use_cases que
los necesiten.
"""

from typing import Optional

from ..domain.entities import Sucursal, Usuario
from ..domain.repositories import SucursalRepository, UsuarioRepository
from .models import Sucursal as SucursalModel  # noqa: F401 (se usa al implementar los métodos)
from .models import Usuario as UsuarioModel  # noqa: F401 (se usa al implementar los métodos)


class UsuarioRepositoryDjango(UsuarioRepository):
    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        raise NotImplementedError

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        raise NotImplementedError

    def listar(self) -> list[Usuario]:
        raise NotImplementedError

    def guardar(self, usuario: Usuario) -> Usuario:
        raise NotImplementedError


class SucursalRepositoryDjango(SucursalRepository):
    def obtener_por_id(self, sucursal_id: int) -> Optional[Sucursal]:
        raise NotImplementedError

    def listar(self) -> list[Sucursal]:
        raise NotImplementedError
