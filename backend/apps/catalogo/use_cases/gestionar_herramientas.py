"""
Casos de uso del catálogo de herramientas (HU6): listar, obtener,
registrar, actualizar y eliminar.

Puros: reciben el repositorio como parámetro (la interfaz de
domain/repositories.py, nunca el ORM) y trabajan con la entidad de
dominio. Acá viven las reglas de negocio del catálogo, no en la vista ni
en el modelo:
  - código y nombre obligatorios (sin espacios sobrantes);
  - el código de caja es único;
  - una caja trae al menos 1 unidad;
  - los datos de EOQ/ROP son opcionales pero nunca negativos;
  - no se elimina una herramienta con movimientos (el repositorio lo
    detecta y lanza HerramientaEnUsoError).
"""

from dataclasses import fields, replace
from typing import Any

from ..domain.entities import Herramienta
from ..domain.exceptions import (
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaNoEncontradaError,
)
from ..domain.repositories import HerramientaRepository

# Campos que el usuario puede cargar/editar (id y fechas los pone el sistema).
CAMPOS_EDITABLES = {
    f.name for f in fields(Herramienta) if f.name not in {"id", "creado_en", "actualizado_en"}
}
CAMPOS_NO_NEGATIVOS = ["demanda_anual", "costo_pedido", "costo_almacenamiento_unitario", "tiempo_entrega_dias"]


def _validar(herramienta: Herramienta) -> Herramienta:
    """Normaliza textos y verifica las reglas que no dependen de otras
    herramientas. Devuelve la herramienta normalizada."""
    herramienta = replace(
        herramienta,
        codigo=herramienta.codigo.strip(),
        nombre=herramienta.nombre.strip(),
        modelo=(herramienta.modelo or "").strip(),
    )
    errores: dict[str, str] = {}
    if not herramienta.codigo:
        errores["codigo"] = "El código es obligatorio."
    if not herramienta.nombre:
        errores["nombre"] = "El nombre es obligatorio."
    if herramienta.unidades_por_caja < 1:
        errores["unidades_por_caja"] = "Una caja debe traer al menos 1 unidad."
    for campo in CAMPOS_NO_NEGATIVOS:
        valor = getattr(herramienta, campo)
        if valor is not None and valor < 0:
            errores[campo] = "No puede ser negativo."
    if errores:
        raise DatosHerramientaInvalidosError(errores)
    return herramienta


def _verificar_codigo_unico(repo: HerramientaRepository, herramienta: Herramienta) -> None:
    existente = repo.obtener_por_codigo(herramienta.codigo)
    if existente is not None and existente.id != herramienta.id:
        raise CodigoDuplicadoError(herramienta.codigo)


def listar_herramientas(repo: HerramientaRepository) -> list[Herramienta]:
    return repo.listar()


def obtener_herramienta(repo: HerramientaRepository, herramienta_id: int) -> Herramienta:
    herramienta = repo.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaNoEncontradaError(herramienta_id)
    return herramienta


def registrar_herramienta(repo: HerramientaRepository, datos: dict[str, Any]) -> Herramienta:
    nueva = Herramienta(
        id=None,
        **{campo: valor for campo, valor in datos.items() if campo in CAMPOS_EDITABLES},
    )
    nueva = _validar(nueva)
    _verificar_codigo_unico(repo, nueva)
    return repo.guardar(nueva)


def actualizar_herramienta(
    repo: HerramientaRepository, herramienta_id: int, cambios: dict[str, Any]
) -> Herramienta:
    """Aplica solo los campos recibidos (sirve para PUT y PATCH) y valida
    el estado final de la herramienta, no solo lo que cambió."""
    actual = obtener_herramienta(repo, herramienta_id)
    actualizada = replace(
        actual, **{campo: valor for campo, valor in cambios.items() if campo in CAMPOS_EDITABLES}
    )
    actualizada = _validar(actualizada)
    _verificar_codigo_unico(repo, actualizada)
    return repo.guardar(actualizada)


def eliminar_herramienta(repo: HerramientaRepository, herramienta_id: int) -> None:
    obtener_herramienta(repo, herramienta_id)
    repo.eliminar(herramienta_id)
