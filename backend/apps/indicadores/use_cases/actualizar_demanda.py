"""
Caso de uso: actualizar la demanda anual estimada con la observada (HU21).

La demanda observada son las salidas reales (ventas) de los últimos
PERIODO_DEMANDA_DIAS, la misma que muestra el EOQ; ajustes y
transferencias no cuentan. Al aceptarla, pasa a ser la demanda anual del
catálogo y el EOQ y el ROP se recalculan con ella (los dos la leen de ahí).

Reglas:
  - solo el Administrador y el Supervisor (los que editan el catálogo);
  - sin ventas en el período no se actualiza: D = 0 dejaría el EOQ en 0;
  - se toma el total de los 12 meses tal cual, sin anualizar: si la
    herramienta tiene menos historia, la pantalla muestra las dos cifras
    y es el usuario quien decide si la acepta.

El cambio queda en el historial de modificaciones (HU13) porque el
repositorio guarda la herramienta con .save().

Puro: recibe repositorios como interfaces y la hora actual como parámetro.
"""

from dataclasses import replace
from datetime import datetime, timedelta

from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import TIPOS_QUE_CUENTAN_COMO_DEMANDA
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import PERIODO_DEMANDA_DIAS, ResultadoEOQ
from ..domain.exceptions import ActualizacionNoPermitidaError, SinVentasObservadasError
from .calcular_eoq import resultado_eoq

ROLES_QUE_ACTUALIZAN = {Rol.ADMINISTRADOR, Rol.SUPERVISOR}


def actualizar_demanda_anual(
    herramientas: HerramientaRepository,
    movimientos: MovimientoRepository,
    actor: Actor,
    herramienta_id: int,
    ahora: datetime,
) -> ResultadoEOQ:
    if Rol(actor.rol) not in ROLES_QUE_ACTUALIZAN:
        raise ActualizacionNoPermitidaError()
    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaNoEncontradaError(herramienta_id)

    vendidas = movimientos.unidades_por_herramienta(
        TIPOS_QUE_CUENTAN_COMO_DEMANDA, desde=ahora - timedelta(days=PERIODO_DEMANDA_DIAS)
    )
    observada = vendidas.get(herramienta_id, 0)
    if observada <= 0:
        raise SinVentasObservadasError(herramienta_id)

    if herramienta.demanda_anual != observada:
        herramienta = herramientas.guardar(replace(herramienta, demanda_anual=observada))
    return resultado_eoq(herramienta, observada)
