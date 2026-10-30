"""
Caso de uso: cierre y resumen diario por sucursal (HU14), para cuadrar la
caja al final del día. Reemplaza a la vista SQL vw_cierre_diario del
script descartado, que solo sumaba salidas: acá se listan todos los
movimientos del día (entradas, salidas, transferencias y ajustes) con
totales por tipo, y las salidas se destacan aparte.

Puro: recibe los repositorios como interfaces, el actor y la fecha de hoy
como parámetros (así se prueba sin reloj ni base de datos). Qué es "el
día" lo resuelve el repositorio en la zona horaria del negocio.

Permisos (tabla 11 del informe: Administrador y Supervisor):
  - Administrador: cualquier sucursal;
  - Supervisor: solo su sucursal;
  - Empleado: no ve el cierre.
"""

from datetime import date

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.value_objects import TipoMovimiento
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.repositories import SucursalRepository
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import CierreDiario, LineaCierre, TotalPorTipo
from ..domain.exceptions import FechaFuturaError, ReporteNoPermitidoError, SucursalInexistenteError


def _verificar_acceso(actor: Actor, sucursal_id: int) -> None:
    rol = Rol(actor.rol)
    if rol == Rol.ADMINISTRADOR:
        return
    if rol == Rol.SUPERVISOR and actor.sucursal_id == sucursal_id:
        return
    raise ReporteNoPermitidoError()


def construir_cierre(
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    sucursal_id: int,
    fecha: date,
    hoy: date,
) -> CierreDiario:
    _verificar_acceso(actor, sucursal_id)
    if fecha > hoy:
        raise FechaFuturaError(fecha)
    sucursal = sucursales.obtener_por_id(sucursal_id)
    if sucursal is None:
        raise SucursalInexistenteError(sucursal_id)

    del_dia = movimientos.listar_del_dia(sucursal_id, fecha)
    # Una sola consulta al catálogo para los nombres (no una por línea).
    catalogo = {h.id: h for h in herramientas.listar()} if del_dia else {}

    lineas = []
    for m in del_dia:
        herramienta = catalogo.get(m.herramienta_id)
        lineas.append(LineaCierre(
            movimiento_id=m.id,
            fecha_hora=m.creado_en,
            herramienta_id=m.herramienta_id,
            codigo=herramienta.codigo if herramienta else f"#{m.herramienta_id}",
            nombre=herramienta.nombre if herramienta else "",
            tipo_movimiento=m.tipo_movimiento.value,
            tipo_unidad=m.tipo_unidad.value,
            cantidad=m.cantidad,
            cantidad_unidades=m.cantidad_unidades,
            usuario=m.usuario_username or "",
            motivo=m.motivo,
        ))

    totales = tuple(
        TotalPorTipo(
            tipo_movimiento=tipo.value,
            movimientos=sum(1 for m in del_dia if m.tipo_movimiento == tipo),
            unidades=sum(m.cantidad_unidades for m in del_dia if m.tipo_movimiento == tipo),
        )
        for tipo in TipoMovimiento
    )
    salidas = [m for m in del_dia if m.tipo_movimiento == TipoMovimiento.SALIDA]
    return CierreDiario(
        fecha=fecha,
        sucursal_id=sucursal.id,
        sucursal_nombre=sucursal.nombre,
        lineas=tuple(lineas),
        totales=totales,
        total_salidas_unidades=sum(m.cantidad_unidades for m in salidas),
        cantidad_salidas=len(salidas),
    )
