"""
Casos de uso del directorio de proveedores (HU8): listar y buscar,
obtener, registrar, actualizar (incluye desactivar) y eliminar.

Puros: reciben el repositorio como interfaz y trabajan con la entidad.
Reglas que viven acá:
  - solo el Administrador registra, edita o elimina (todos consultan);
  - nombre (2 a 150 caracteres) y teléfono obligatorios; el teléfono, de
    7 a 15 dígitos con espacios, guiones y + al inicio (apps/comun/reglas.py);
    el correo es opcional pero, si viene, debe tener formato de correo. Al
    editar, el formato del teléfono solo se revisa si cambia;
  - el nombre es único sin distinguir mayúsculas;
  - un proveedor con herramientas asociadas no se elimina: se desactiva
    (el repositorio lo detecta y lanza ProveedorEnUsoError).
"""

import re
from dataclasses import fields, replace
from typing import Any, Optional

from apps.comun.reglas import error_telefono, normalizar_espacios
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

NOMBRE_LARGO_MINIMO = 2
NOMBRE_LARGO_MAXIMO = 150
_EMAIL_VALIDO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _exigir_administrador(actor: Actor) -> None:
    if Rol(actor.rol) != Rol.ADMINISTRADOR:
        raise PermisoDenegadoError()


def _validar(proveedor: Proveedor, anterior: Optional[Proveedor] = None) -> Proveedor:
    """`anterior`: el proveedor antes de editarlo (None en el alta)."""
    proveedor = replace(
        proveedor,
        nombre=normalizar_espacios(proveedor.nombre),
        telefono=proveedor.telefono.strip(),
        email=proveedor.email.strip().lower(),
    )
    errores: dict[str, str] = {}
    # Es el nombre de una empresa, no de una persona: admite números y
    # símbolos ("Ferretería 3H S.R.L.").
    if not proveedor.nombre:
        errores["nombre"] = "El nombre es obligatorio."
    elif not NOMBRE_LARGO_MINIMO <= len(proveedor.nombre) <= NOMBRE_LARGO_MAXIMO:
        errores["nombre"] = f"Debe tener de {NOMBRE_LARGO_MINIMO} a {NOMBRE_LARGO_MAXIMO} caracteres."
    telefono_cambia = anterior is None or anterior.telefono != proveedor.telefono
    mensaje = error_telefono(proveedor.telefono) if telefono_cambia else None
    if mensaje:
        errores["telefono"] = mensaje
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
    actualizado = _validar(actualizado, anterior=actual)
    _verificar_nombre_unico(repo, actualizado)
    return repo.guardar(actualizado)


def eliminar_proveedor(repo: ProveedorRepository, actor: Actor, proveedor_id: int) -> None:
    _exigir_administrador(actor)
    obtener_proveedor(repo, proveedor_id)
    repo.eliminar(proveedor_id)
