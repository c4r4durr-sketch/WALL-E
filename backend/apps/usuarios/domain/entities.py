"""
Entidades puras del dominio de usuarios.

Son dataclasses simples, sin herencia de Django (ni Model ni AbstractUser).
Los use_cases trabajan con estos objetos, no con el modelo ORM directo, para
poder probarse sin base de datos y sin levantar Django. La conversión
ORM <-> entidad de dominio la hacen los repositorios concretos en
infrastructure/repositories.py.
"""

from dataclasses import dataclass
from typing import Optional

from .value_objects import Rol


@dataclass(frozen=True)
class Sucursal:
    id: Optional[int]
    nombre: str
    direccion: str
    activa: bool = True


@dataclass(frozen=True)
class Usuario:
    id: Optional[int]
    username: str
    # El modelo ORM (AbstractUser) separa first_name/last_name; se unen acá
    # en un solo campo porque al dominio no le interesa esa distinción.
    # UsuarioRepositoryDjango es quien hace esa conversión en ambos sentidos.
    nombre_completo: str
    rol: Rol
    # Solo puede ser None para Administrador: Supervisor y Empleado
    # siempre tienen sucursal (ver domain/reglas.py::requiere_sucursal).
    sucursal_id: Optional[int]
    activo: bool = True


@dataclass(frozen=True)
class Actor:
    """Quién ejecuta un caso de uso. Los use_cases de otros módulos lo
    reciben (armado por la vista a partir del usuario autenticado) para
    aplicar reglas que dependen del rol o la sucursal, sin importar Django."""

    usuario_id: int
    rol: Rol
    sucursal_id: Optional[int]
