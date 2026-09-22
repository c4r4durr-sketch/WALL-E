"""
Casos de uso de movimientos (HU9): registrar entrada, registrar salida,
registrar ajuste (corrección) y consultar stock por herramienta y sucursal.

Puros: reciben los repositorios como interfaces (movimientos, catálogo y
sucursales) y un Actor con el usuario que opera; no importan Django.

Reglas:
  - la cantidad se registra en UNIDAD o CAJA; si es CAJA se convierte a
    unidades con el unidades_por_caja de la herramienta (reutiliza
    indicadores/domain/formulas.py, no reimplementa la conversión);
  - una SALIDA o un AJUSTE_NEGATIVO nunca deja el stock de la sucursal
    en negativo;
  - los ajustes son solo para Administrador/Supervisor y llevan motivo;
  - un Empleado solo registra movimientos en su propia sucursal;
  - la sucursal debe existir y estar activa.
"""

from dataclasses import dataclass
from typing import Optional

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.indicadores.domain.formulas import cajas_a_unidades, unidades_a_cajas
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.repositories import SucursalRepository
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import Movimiento
from ..domain.exceptions import (
    AjusteNoPermitidoError,
    HerramientaInexistenteError,
    MotivoObligatorioError,
    StockInsuficienteError,
    SucursalInvalidaError,
    SucursalNoPermitidaError,
)
from ..domain.repositories import MovimientoRepository
from ..domain.stock import resta_stock, stock_desde_totales
from ..domain.value_objects import TipoMovimiento, TipoUnidad


@dataclass(frozen=True)
class StockEnSucursal:
    herramienta_id: int
    sucursal_id: int
    sucursal_nombre: str
    unidades: int
    cajas_completas: int
    unidades_sueltas: int


def _stock_actual(repo: MovimientoRepository, herramienta_id: int, sucursal_id: int) -> int:
    return stock_desde_totales(repo.unidades_por_tipo(herramienta_id, sucursal_id))


def _registrar(
    tipo: TipoMovimiento,
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    herramienta_id: int,
    sucursal_id: int,
    tipo_unidad: TipoUnidad,
    cantidad: int,
    motivo: str = "",
) -> Movimiento:
    if cantidad < 1:
        raise ValueError("La cantidad debe ser al menos 1.")

    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaInexistenteError(herramienta_id)

    sucursal = sucursales.obtener_por_id(sucursal_id)
    if sucursal is None or not sucursal.activa:
        raise SucursalInvalidaError(sucursal_id)

    if Rol(actor.rol) == Rol.EMPLEADO and actor.sucursal_id != sucursal_id:
        raise SucursalNoPermitidaError(sucursal_id)

    tipo_unidad = TipoUnidad(tipo_unidad)
    if tipo_unidad == TipoUnidad.CAJA:
        unidades = cajas_a_unidades(cantidad, herramienta.unidades_por_caja)
    else:
        unidades = cantidad

    if resta_stock(tipo):
        # Salidas y ajustes negativos pasan por el MISMO bloqueo: se toma
        # ANTES de leer el stock, así si otra operación que resta stock de
        # esta herramienta está en curso, esta espera a que termine y ve el
        # stock ya descontado.
        movimientos.bloquear_stock(herramienta_id)
        disponible = _stock_actual(movimientos, herramienta_id, sucursal_id)
        if unidades > disponible:
            raise StockInsuficienteError(disponible=disponible, solicitado=unidades)

    return movimientos.guardar(
        Movimiento(
            id=None,
            herramienta_id=herramienta_id,
            sucursal_id=sucursal_id,
            tipo_movimiento=tipo,
            tipo_unidad=tipo_unidad,
            cantidad=cantidad,
            cantidad_unidades=unidades,
            usuario_id=actor.usuario_id,
            motivo=motivo,
        )
    )


def registrar_entrada(movimientos, herramientas, sucursales, actor, herramienta_id, sucursal_id, tipo_unidad, cantidad):
    return _registrar(TipoMovimiento.ENTRADA, movimientos, herramientas, sucursales,
                      actor, herramienta_id, sucursal_id, tipo_unidad, cantidad)


def registrar_salida(movimientos, herramientas, sucursales, actor, herramienta_id, sucursal_id, tipo_unidad, cantidad):
    return _registrar(TipoMovimiento.SALIDA, movimientos, herramientas, sucursales,
                      actor, herramienta_id, sucursal_id, tipo_unidad, cantidad)


ROLES_QUE_AJUSTAN = frozenset({Rol.ADMINISTRADOR, Rol.SUPERVISOR})


def registrar_ajuste(
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    herramienta_id: int,
    sucursal_id: int,
    positivo: bool,
    tipo_unidad: TipoUnidad,
    cantidad: int,
    motivo: str,
) -> Movimiento:
    """Corrección de stock (los movimientos no se editan: un error se
    arregla con un ajuste nuevo). Solo Administrador/Supervisor, motivo
    obligatorio, y un ajuste negativo tampoco deja el stock en negativo
    (usa el mismo bloqueo y validación que una salida)."""
    if Rol(actor.rol) not in ROLES_QUE_AJUSTAN:
        raise AjusteNoPermitidoError()
    motivo = (motivo or "").strip()
    if not motivo:
        raise MotivoObligatorioError()
    tipo = TipoMovimiento.AJUSTE_POSITIVO if positivo else TipoMovimiento.AJUSTE_NEGATIVO
    return _registrar(tipo, movimientos, herramientas, sucursales, actor,
                      herramienta_id, sucursal_id, tipo_unidad, cantidad, motivo)


def consultar_stock(
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    herramienta_id: int,
    sucursal_id: Optional[int] = None,
) -> list[StockEnSucursal]:
    """Stock de una herramienta en una sucursal, o en todas las sucursales
    activas si no se indica ninguna (HU11: ver el stock en ambas)."""
    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaInexistenteError(herramienta_id)

    if sucursal_id is not None:
        sucursal = sucursales.obtener_por_id(sucursal_id)
        if sucursal is None:
            raise SucursalInvalidaError(sucursal_id)
        objetivo = [sucursal]
    else:
        objetivo = [s for s in sucursales.listar() if s.activa]

    resultado = []
    for sucursal in objetivo:
        unidades = _stock_actual(movimientos, herramienta_id, sucursal.id)
        cajas, sueltas = unidades_a_cajas(unidades, herramienta.unidades_por_caja)
        resultado.append(
            StockEnSucursal(
                herramienta_id=herramienta_id,
                sucursal_id=sucursal.id,
                sucursal_nombre=sucursal.nombre,
                unidades=unidades,
                cajas_completas=cajas,
                unidades_sueltas=sueltas,
            )
        )
    return resultado


def historial(
    movimientos: MovimientoRepository,
    herramienta_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
) -> list[Movimiento]:
    return movimientos.listar(herramienta_id=herramienta_id, sucursal_id=sucursal_id)
