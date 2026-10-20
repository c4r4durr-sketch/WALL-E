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
    detecta y lanza HerramientaEnUsoError);
  - HU7: el costo unitario es mayor que cero; solo el Administrador lo
    carga o lo cambia; una vez cargado no se puede quitar, solo
    reemplazar; y cada cambio queda en el historial de costos con fecha y
    usuario. La vista ejecuta alta y edición dentro de una transacción:
    la herramienta y su fila de historial se guardan juntas o ninguna;
  - HU8: el proveedor asignado debe existir y estar activo (una
    herramienta que ya tenía un proveedor luego desactivado lo conserva).
"""

from dataclasses import fields, replace
from typing import Any, Optional

from apps.proveedores.domain.repositories import ProveedorRepository
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import CambioCosto, Herramienta
from ..domain.exceptions import (
    CambioDeCostoNoPermitidoError,
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaNoEncontradaError,
)
from ..domain.repositories import HerramientaRepository, HistorialCostoRepository

# Campos que el usuario puede cargar/editar (id y fechas los pone el sistema).
CAMPOS_EDITABLES = {
    f.name for f in fields(Herramienta)
    if f.name not in {"id", "creado_en", "actualizado_en", "proveedor_nombre"}
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
    if herramienta.costo_unitario is not None and herramienta.costo_unitario <= 0:
        errores["costo_unitario"] = "El costo unitario debe ser mayor que cero."
    if errores:
        raise DatosHerramientaInvalidosError(errores)
    return herramienta


def _verificar_cambio_de_costo(actor: Actor, anterior: Optional[Herramienta], nueva: Herramienta) -> bool:
    """Devuelve True si el costo unitario cambia (y el actor puede
    cambiarlo); lanza un error si el cambio no está permitido."""
    costo_anterior = anterior.costo_unitario if anterior else None
    if nueva.costo_unitario == costo_anterior:
        return False
    if costo_anterior is not None and nueva.costo_unitario is None:
        raise DatosHerramientaInvalidosError(
            {"costo_unitario": "El costo unitario no se puede quitar; ingresa el valor nuevo."}
        )
    if Rol(actor.rol) != Rol.ADMINISTRADOR:
        raise CambioDeCostoNoPermitidoError()
    return True


def _verificar_proveedor(
    proveedores: ProveedorRepository, anterior: Optional[Herramienta], nueva: Herramienta
) -> None:
    if nueva.proveedor_id is None or (anterior and anterior.proveedor_id == nueva.proveedor_id):
        return
    proveedor = proveedores.obtener_por_id(nueva.proveedor_id)
    if proveedor is None or not proveedor.activo:
        raise DatosHerramientaInvalidosError({"proveedor": "El proveedor no existe o está inactivo."})


def _registrar_cambio_de_costo(
    historial: HistorialCostoRepository, actor: Actor, anterior: Optional[Herramienta], guardada: Herramienta
) -> None:
    historial.registrar(CambioCosto(
        id=None,
        herramienta_id=guardada.id,
        costo_anterior=anterior.costo_unitario if anterior else None,
        costo_nuevo=guardada.costo_unitario,
        usuario_id=actor.usuario_id,
    ))


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


def registrar_herramienta(
    repo: HerramientaRepository,
    datos: dict[str, Any],
    *,
    actor: Actor,
    historial: HistorialCostoRepository,
    proveedores: ProveedorRepository,
) -> Herramienta:
    nueva = Herramienta(
        id=None,
        **{campo: valor for campo, valor in datos.items() if campo in CAMPOS_EDITABLES},
    )
    nueva = _validar(nueva)
    _verificar_codigo_unico(repo, nueva)
    _verificar_proveedor(proveedores, None, nueva)
    cambia_costo = _verificar_cambio_de_costo(actor, None, nueva)
    guardada = repo.guardar(nueva)
    if cambia_costo:
        _registrar_cambio_de_costo(historial, actor, None, guardada)
    return guardada


def actualizar_herramienta(
    repo: HerramientaRepository,
    herramienta_id: int,
    cambios: dict[str, Any],
    *,
    actor: Actor,
    historial: HistorialCostoRepository,
    proveedores: ProveedorRepository,
) -> Herramienta:
    """Aplica solo los campos recibidos (sirve para PUT y PATCH) y valida
    el estado final de la herramienta, no solo lo que cambió."""
    actual = obtener_herramienta(repo, herramienta_id)
    actualizada = replace(
        actual, **{campo: valor for campo, valor in cambios.items() if campo in CAMPOS_EDITABLES}
    )
    actualizada = _validar(actualizada)
    _verificar_codigo_unico(repo, actualizada)
    _verificar_proveedor(proveedores, actual, actualizada)
    cambia_costo = _verificar_cambio_de_costo(actor, actual, actualizada)
    guardada = repo.guardar(actualizada)
    if cambia_costo:
        _registrar_cambio_de_costo(historial, actor, actual, guardada)
    return guardada


def historial_de_costos(
    repo: HerramientaRepository, historial: HistorialCostoRepository, herramienta_id: int
) -> list[CambioCosto]:
    obtener_herramienta(repo, herramienta_id)
    return historial.listar_por_herramienta(herramienta_id)


def eliminar_herramienta(repo: HerramientaRepository, herramienta_id: int) -> None:
    obtener_herramienta(repo, herramienta_id)
    repo.eliminar(herramienta_id)
