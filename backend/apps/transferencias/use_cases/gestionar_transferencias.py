"""
Casos de uso de transferencias entre sucursales (HU12): solicitar,
completar, rechazar, listar y obtener.

Puros: reciben los repositorios como interfaces y un Actor; no importan
Django. La validación de stock, el bloqueo y el registro de movimientos NO
se reimplementan acá: se reutilizan los use cases de movimientos.

Flujo:
  1. SOLICITAR (cualquier rol; un Empleado solo desde su sucursal): queda
     PENDIENTE. Se valida que haya stock en origen en ese momento, pero el
     stock todavía no se mueve.
  2. COMPLETAR (Administrador/Supervisor): se registran en una sola
     operación la salida en origen y la entrada en destino. El stock se
     vuelve a validar con bloqueo: si ya no alcanza (hubo ventas desde la
     solicitud), no se mueve nada.
  3. RECHAZAR (Administrador/Supervisor): con motivo obligatorio; el stock
     no se toca.
"""

from dataclasses import replace
from datetime import datetime
from typing import Optional

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.indicadores.domain.formulas import cajas_a_unidades
from apps.movimientos.domain.exceptions import (
    HerramientaInexistenteError,
    StockInsuficienteError,
    SucursalInvalidaError,
    SucursalNoPermitidaError,
)
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.value_objects import TipoUnidad
from apps.movimientos.use_cases.registrar_movimiento import (
    registrar_movimientos_de_transferencia,
    stock_disponible,
)
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.repositories import SucursalRepository
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import Transferencia
from ..domain.exceptions import (
    MismaSucursalError,
    MotivoRechazoObligatorioError,
    ResolucionNoPermitidaError,
    TransferenciaNoEncontradaError,
    TransferenciaYaResueltaError,
)
from ..domain.repositories import TransferenciaRepository
from ..domain.value_objects import EstadoTransferencia

ROLES_QUE_RESUELVEN = frozenset({Rol.ADMINISTRADOR, Rol.SUPERVISOR})


def solicitar_transferencia(
    transferencias: TransferenciaRepository,
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    herramienta_id: int,
    sucursal_origen_id: int,
    sucursal_destino_id: int,
    tipo_unidad: TipoUnidad,
    cantidad: int,
) -> Transferencia:
    if cantidad < 1:
        raise ValueError("La cantidad debe ser al menos 1.")
    if sucursal_origen_id == sucursal_destino_id:
        raise MismaSucursalError()

    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaInexistenteError(herramienta_id)
    for sucursal_id in (sucursal_origen_id, sucursal_destino_id):
        sucursal = sucursales.obtener_por_id(sucursal_id)
        if sucursal is None or not sucursal.activa:
            raise SucursalInvalidaError(sucursal_id)

    # Un Empleado solo puede pedir que salga mercadería de SU sucursal.
    if Rol(actor.rol) == Rol.EMPLEADO and actor.sucursal_id != sucursal_origen_id:
        raise SucursalNoPermitidaError(sucursal_origen_id)

    tipo_unidad = TipoUnidad(tipo_unidad)
    unidades = (
        cajas_a_unidades(cantidad, herramienta.unidades_por_caja)
        if tipo_unidad == TipoUnidad.CAJA
        else cantidad
    )
    # Validación temprana (sin bloqueo): avisar ya si no alcanza. La
    # definitiva, con bloqueo, se hace al completar.
    disponible = stock_disponible(movimientos, herramienta_id, sucursal_origen_id)
    if unidades > disponible:
        raise StockInsuficienteError(disponible=disponible, solicitado=unidades)

    return transferencias.guardar(Transferencia(
        id=None,
        herramienta_id=herramienta_id,
        sucursal_origen_id=sucursal_origen_id,
        sucursal_destino_id=sucursal_destino_id,
        cantidad=cantidad,
        tipo_unidad=tipo_unidad,
        cantidad_unidades=unidades,
        estado=EstadoTransferencia.PENDIENTE,
        usuario_id=actor.usuario_id,
    ))


def _pendiente_para_resolver(
    transferencias: TransferenciaRepository, actor: Actor, transferencia_id: int
) -> Transferencia:
    if Rol(actor.rol) not in ROLES_QUE_RESUELVEN:
        raise ResolucionNoPermitidaError()
    transferencia = transferencias.obtener_para_resolver(transferencia_id)
    if transferencia is None:
        raise TransferenciaNoEncontradaError(transferencia_id)
    if transferencia.estado != EstadoTransferencia.PENDIENTE:
        raise TransferenciaYaResueltaError(transferencia.estado.value)
    return transferencia


def completar_transferencia(
    transferencias: TransferenciaRepository,
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    transferencia_id: int,
    ahora: datetime,
) -> Transferencia:
    """Quien llama debe envolverlo en UNA transacción: bloquear la
    transferencia, mover el stock y marcarla COMPLETADA van juntos."""
    transferencia = _pendiente_para_resolver(transferencias, actor, transferencia_id)
    salida, entrada = registrar_movimientos_de_transferencia(
        movimientos, herramientas, sucursales, actor,
        transferencia.herramienta_id,
        transferencia.sucursal_origen_id,
        transferencia.sucursal_destino_id,
        transferencia.tipo_unidad,
        transferencia.cantidad,
        transferencia.cantidad_unidades,
        referencia=f"Transferencia #{transferencia.id}",
    )
    return transferencias.guardar(replace(
        transferencia,
        estado=EstadoTransferencia.COMPLETADA,
        resuelto_por_id=actor.usuario_id,
        resuelto_en=ahora,
        movimiento_salida_id=salida.id,
        movimiento_entrada_id=entrada.id,
    ))


def rechazar_transferencia(
    transferencias: TransferenciaRepository,
    actor: Actor,
    transferencia_id: int,
    motivo: str,
    ahora: datetime,
) -> Transferencia:
    motivo = (motivo or "").strip()
    if not motivo:
        raise MotivoRechazoObligatorioError()
    transferencia = _pendiente_para_resolver(transferencias, actor, transferencia_id)
    return transferencias.guardar(replace(
        transferencia,
        estado=EstadoTransferencia.RECHAZADA,
        resuelto_por_id=actor.usuario_id,
        resuelto_en=ahora,
        motivo_rechazo=motivo,
    ))


def listar_transferencias(
    transferencias: TransferenciaRepository, estado: Optional[EstadoTransferencia] = None
) -> list[Transferencia]:
    return transferencias.listar(estado)


def obtener_transferencia(transferencias: TransferenciaRepository, transferencia_id: int) -> Transferencia:
    transferencia = transferencias.obtener_por_id(transferencia_id)
    if transferencia is None:
        raise TransferenciaNoEncontradaError(transferencia_id)
    return transferencia
