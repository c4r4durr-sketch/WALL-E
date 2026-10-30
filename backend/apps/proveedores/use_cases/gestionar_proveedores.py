"""
Casos de uso del directorio de proveedores (HU8): listar y buscar,
obtener, registrar, actualizar (incluye desactivar) y eliminar.

Puros: reciben el repositorio como interfaz y trabajan con la entidad.
Reglas que viven acá:
  - solo el Administrador registra, edita o elimina (todos consultan);
  - nombre y teléfono obligatorios; el correo es opcional pero, si viene,
    debe tener formato de correo;
  - el nombre es único sin distinguir mayúsculas;
  - un proveedor con herramientas asociadas no se elimina: se desactiva
    (el repositorio lo detecta y lanza ProveedorEnUsoError).
"""

import re
from dataclasses import fields, replace
from typing import Any

from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import Proveedor
from ..domain.exceptions import (
    DatosProveedorInvalidosError,
    NombreProveedorDuplicadoError,
    PermisoDenegadoError,
    ProveedorNoEncontradoError,
)
from ..domain.repositories import ProveedorRepository

CAMPOS_EDITABLES = {
    f.name for f in fields(Proveedor)
    if f.name not in {"id", "creado_en", "actualizado_en", "cantidad_herramientas"}
}

# Dígitos con separadores habituales (espacios, guiones, paréntesis) y un
# "+" inicial opcional para el código de país: "+591 2 2123456", "77712345".
_TELEFONO_VALIDO = re.compile(r"^\+?[\d\s()-]+$")
TELEFONO_MIN_DIGITOS = 7
TELEFONO_MAX_DIGITOS = 15
_EMAIL_VALIDO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _exigir_administrador(actor: Actor) -> None:
    if Rol(actor.rol) != Rol.ADMINISTRADOR:
        raise PermisoDenegadoError()


def _validar(proveedor: Proveedor) -> Proveedor:
    proveedor = replace(
        proveedor,
        nombre=" ".join(proveedor.nombre.split()),
        telefono=proveedor.telefono.strip(),
        email=proveedor.email.strip().lower(),
    )
    errores: dict[str, str] = {}
    if not proveedor.nombre:
        errores["nombre"] = "El nombre es obligatorio."
    digitos = sum(c.isdigit() for c in proveedor.telefono)
    if not proveedor.telefono:
        errores["telefono"] = "El teléfono es obligatorio."
    elif not _TELEFONO_VALIDO.match(proveedor.telefono) or not (
        TELEFONO_MIN_DIGITOS <= digitos <= TELEFONO_MAX_DIGITOS
    ):
        errores["telefono"] = (
            f"Teléfono no válido: de {TELEFONO_MIN_DIGITOS} a {TELEFONO_MAX_DIGITOS} dígitos "
            "(se permiten espacios, guiones, paréntesis y + al inicio)."
        )
    if proveedor.email and not _EMAIL_VALIDO.match(proveedor.email):
        errores["email"] = "Correo no válido."
    if errores:
        raise DatosProveedorInvalidosError(errores)
    return proveedor


def _verificar_nombre_unico(repo: ProveedorRepository, proveedor: Proveedor) -> None:
    existente = repo.obtener_por_nombre(proveedor.nombre)
    if existente is not None and existente.id != proveedor.id:
        raise NombreProveedorDuplicadoError(proveedor.nombre)


def listar_proveedores(
    repo: ProveedorRepository, buscar: str = "", solo_activos: bool = False
) -> list[Proveedor]:
    return repo.listar(buscar=buscar.strip(), solo_activos=solo_activos)


def obtener_proveedor(repo: ProveedorRepository, proveedor_id: int) -> Proveedor:
    proveedor = repo.obtener_por_id(proveedor_id)
    if proveedor is None:
        raise ProveedorNoEncontradoError(proveedor_id)
    return proveedor


def registrar_proveedor(repo: ProveedorRepository, actor: Actor, datos: dict[str, Any]) -> Proveedor:
    _exigir_administrador(actor)
    nuevo = Proveedor(id=None, **{c: v for c, v in datos.items() if c in CAMPOS_EDITABLES})
    nuevo = _validar(nuevo)
    _verificar_nombre_unico(repo, nuevo)
    return repo.guardar(nuevo)


def actualizar_proveedor(
    repo: ProveedorRepository, actor: Actor, proveedor_id: int, cambios: dict[str, Any]
) -> Proveedor:
    """Aplica solo los campos recibidos (PUT o PATCH) y valida el estado
    final. Desactivar es un cambio más (activo = False)."""
    _exigir_administrador(actor)
    actual = obtener_proveedor(repo, proveedor_id)
    actualizado = replace(actual, **{c: v for c, v in cambios.items() if c in CAMPOS_EDITABLES})
    actualizado = _validar(actualizado)
    _verificar_nombre_unico(repo, actualizado)
    return repo.guardar(actualizado)


def eliminar_proveedor(repo: ProveedorRepository, actor: Actor, proveedor_id: int) -> None:
    _exigir_administrador(actor)
    obtener_proveedor(repo, proveedor_id)
    repo.eliminar(proveedor_id)
