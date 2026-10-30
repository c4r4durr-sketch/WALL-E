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
    """Cuenta del sistema. La contraseña no forma parte de la entidad: el
    dominio nunca la lee; solo la valida (ValidadorPassword) y la entrega
    al repositorio para que la guarde cifrada."""

    id: Optional[int]
    username: str
    nombres: str
    apellidos: str
    rol: Rol
    # Solo puede ser None para Administrador: Supervisor y Empleado
    # siempre tienen sucursal (ver domain/reglas.py::requiere_sucursal).
    sucursal_id: Optional[int]
    email: str = ""
    activo: bool = True
    # Solo lectura, para mostrar en listas; lo completa el repositorio.
    sucursal_nombre: Optional[str] = None


@dataclass(frozen=True)
class Actor:
    """Quién ejecuta un caso de uso. Los use_cases de otros módulos lo
    reciben (armado por la vista a partir del usuario autenticado) para
    aplicar reglas que dependen del rol o la sucursal, sin importar Django."""

    usuario_id: int
    rol: Rol
    sucursal_id: Optional[int]
