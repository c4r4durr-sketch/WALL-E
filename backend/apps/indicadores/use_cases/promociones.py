"""
Casos de uso de promociones (HU23): poner la etiqueta de promoción a una
herramienta estancada en una sucursal, quitarla antes y listarlas.

Reglas (backlog: «Como supervisor, quiero marcar las herramientas
estancadas con una etiqueta de promoción»):
  - el Supervisor pone y quita la etiqueta en SU sucursal; el
    Administrador, en cualquiera; el Empleado no. Todos los roles las ven,
    porque el mostrador tiene que saber qué aplicar;
  - solo sobre una herramienta ESTANCADA en esa sucursal: con stock y más
    de DIAS_PARA_ESTANCAMIENTO días sin venta, la misma regla del reporte
    de antigüedad (HU22) y del panel (HU24);
  - el descuento es opcional (la etiqueta sola ya sirve); si se indica, es
    un entero de 1 a 90 %. Empieza hoy y termina en fecha_fin (hoy o
    después);
  - una sola promoción vigente por herramienta y sucursal;
  - no se editan ni se borran: se terminan (activa = False). Todo queda en
    el historial de modificaciones (HU13).

Puros: reciben repositorios como interfaces, el actor y la fecha de hoy.
"""

from dataclasses import replace
from datetime import date
from typing import Any

from apps.catalogo.domain.entities import Promocion
from apps.catalogo.domain.repositories import HerramientaRepository, PromocionRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.repositories import SucursalRepository
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import DIAS_PARA_ESTANCAMIENTO, PromocionListada
from ..domain.exceptions import (
    DatosPromocionInvalidosError,
    PromocionNoAplicableError,
    PromocionNoEncontradaError,
    PromocionNoPermitidaError,
)
from .reporte_antiguedad import lineas_de_antiguedad

DESCUENTO_MINIMO = 1
DESCUENTO_MAXIMO = 90


def estado_promocion(promocion: Promocion, hoy: date) -> str:
    if not promocion.activa:
        return "TERMINADA"
    return "VIGENTE" if promocion.vigente(hoy) else "VENCIDA"


ROLES_QUE_PROMOCIONAN = frozenset({Rol.ADMINISTRADOR, Rol.SUPERVISOR})


def _verificar_rol(actor: Actor) -> None:
    if Rol(actor.rol) not in ROLES_QUE_PROMOCIONAN:
        raise PromocionNoPermitidaError()


def _verificar_sucursal(actor: Actor, sucursal_id: int) -> None:
    """El Supervisor solo gestiona las promociones de su sucursal."""
    if Rol(actor.rol) == Rol.SUPERVISOR and actor.sucursal_id != sucursal_id:
        raise PromocionNoPermitidaError()


def puede_gestionar(actor: Actor, sucursal_id: int) -> bool:
    try:
        _verificar_rol(actor)
        _verificar_sucursal(actor, sucursal_id)
    except PromocionNoPermitidaError:
        return False
    return True


def _validar(datos: dict[str, Any], hoy: date) -> None:
    errores: dict[str, str] = {}
    descuento = datos.get("descuento_porcentaje")
    if descuento is not None and not DESCUENTO_MINIMO <= descuento <= DESCUENTO_MAXIMO:
        errores["descuento_porcentaje"] = f"El descuento debe estar entre {DESCUENTO_MINIMO} y {DESCUENTO_MAXIMO} %."
    fecha_fin = datos.get("fecha_fin")
    if fecha_fin is None or fecha_fin < hoy:
        errores["fecha_fin"] = "La promoción debe terminar hoy o después."
    if errores:
        raise DatosPromocionInvalidosError(errores)


def crear_promocion(
    promociones: PromocionRepository,
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    datos: dict[str, Any],
    hoy: date,
) -> Promocion:
    """`datos`: herramienta_id, sucursal_id, fecha_fin, y opcionales
    descuento_porcentaje y motivo."""
    _verificar_rol(actor)
    _verificar_sucursal(actor, datos["sucursal_id"])
    _validar(datos, hoy)
    herramienta_id, sucursal_id = datos["herramienta_id"], datos["sucursal_id"]
    if herramientas.obtener_por_id(herramienta_id) is None:
        raise DatosPromocionInvalidosError({"herramienta_id": "No existe esa herramienta."})
    if sucursales.obtener_por_id(sucursal_id) is None:
        raise DatosPromocionInvalidosError({"sucursal_id": "No existe esa sucursal."})

    estancada = any(
        l.herramienta_id == herramienta_id and l.estancada
        for l in lineas_de_antiguedad(movimientos, herramientas, sucursales, hoy, sucursal_id)
    )
    if not estancada:
        raise PromocionNoAplicableError(
            f"Solo se promocionan herramientas con stock y más de {DIAS_PARA_ESTANCAMIENTO} días sin venta en esa sucursal."
        )
    if any(p.vigente(hoy) for p in promociones.de_herramienta_en_sucursal(herramienta_id, sucursal_id)):
        raise PromocionNoAplicableError("Esta herramienta ya tiene una promoción vigente en esa sucursal.")

    return promociones.guardar(Promocion(
        id=None,
        herramienta_id=herramienta_id,
        sucursal_id=sucursal_id,
        descuento_porcentaje=datos.get("descuento_porcentaje"),
        fecha_inicio=hoy,
        fecha_fin=datos["fecha_fin"],
        usuario_id=actor.usuario_id,
        motivo=(datos.get("motivo") or "").strip(),
    ))


def terminar_promocion(promociones: PromocionRepository, actor: Actor, promocion_id: int, hoy: date) -> Promocion:
    _verificar_rol(actor)
    promocion = promociones.obtener_por_id(promocion_id)
    if promocion is None:
        raise PromocionNoEncontradaError(promocion_id)
    _verificar_sucursal(actor, promocion.sucursal_id)
    if not promocion.vigente(hoy):
        raise PromocionNoAplicableError("La promoción ya no está vigente.")
    return promociones.guardar(replace(promocion, activa=False))


def listar_promociones(promociones: PromocionRepository, hoy: date, solo_vigentes: bool = False) -> list[PromocionListada]:
    listadas = [PromocionListada(p, estado_promocion(p, hoy)) for p in promociones.listar()]
    return [l for l in listadas if l.estado == "VIGENTE"] if solo_vigentes else listadas
