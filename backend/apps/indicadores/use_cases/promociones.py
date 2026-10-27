"""
Casos de uso de promociones (HU23): poner en promoción una herramienta
estancada en una sucursal, terminarla antes y listarlas.

Reglas:
  - solo el Administrador crea o termina promociones (es una decisión de
    precio); todos los roles las ven, porque el mostrador tiene que saber
    qué aplicar;
  - solo sobre una herramienta ESTANCADA en esa sucursal: con stock y más
    de DIAS_PARA_ESTANCAMIENTO días sin venta, la misma regla del reporte
    de antigüedad (HU22) y del panel (HU24);
  - descuento entero de 1 a 90 %; empieza hoy y termina en fecha_fin
    (hoy o después);
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


def _verificar_administrador(actor: Actor) -> None:
    if Rol(actor.rol) != Rol.ADMINISTRADOR:
        raise PromocionNoPermitidaError()


def _validar(datos: dict[str, Any], hoy: date) -> None:
    errores: dict[str, str] = {}
    descuento = datos.get("descuento_porcentaje")
    if descuento is None or not DESCUENTO_MINIMO <= descuento <= DESCUENTO_MAXIMO:
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
    """`datos`: herramienta_id, sucursal_id, descuento_porcentaje,
    fecha_fin y motivo (opcional)."""
    _verificar_administrador(actor)
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
        descuento_porcentaje=datos["descuento_porcentaje"],
        fecha_inicio=hoy,
        fecha_fin=datos["fecha_fin"],
        usuario_id=actor.usuario_id,
        motivo=(datos.get("motivo") or "").strip(),
    ))


def terminar_promocion(promociones: PromocionRepository, actor: Actor, promocion_id: int, hoy: date) -> Promocion:
    _verificar_administrador(actor)
    promocion = promociones.obtener_por_id(promocion_id)
    if promocion is None:
        raise PromocionNoEncontradaError(promocion_id)
    if not promocion.vigente(hoy):
        raise PromocionNoAplicableError("La promoción ya no está vigente.")
    return promociones.guardar(replace(promocion, activa=False))


def listar_promociones(promociones: PromocionRepository, hoy: date, solo_vigentes: bool = False) -> list[PromocionListada]:
    listadas = [PromocionListada(p, estado_promocion(p, hoy)) for p in promociones.listar()]
    return [l for l in listadas if l.estado == "VIGENTE"] if solo_vigentes else listadas
