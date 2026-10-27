"""
Caso de uso: reporte de antigüedad del stock (HU22).

Por cada herramienta con stock en una sucursal: cuántos días lleva sin
una venta real, en qué tramo cae y cuánto dinero tiene inmovilizado
(stock x costo unitario). Las de más de DIAS_PARA_ESTANCAMIENTO días son
las estancadas, las mismas que muestra el panel (HU24): las dos usan
domain/antiguedad.py.

Permisos (como el cierre diario, tabla 11 del informe):
  - Administrador: una sucursal o todas (sucursal_id None);
  - Supervisor: solo la suya (sin indicarla, se usa la suya);
  - Empleado: no ve el reporte.

Puro: recibe repositorios como interfaces, el actor y la fecha de hoy.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import stock_desde_totales
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.repositories import SucursalRepository
from apps.usuarios.domain.value_objects import Rol

from ..domain.antiguedad import TRAMOS, dias_sin_venta, tramo
from ..domain.entities import (
    DIAS_PARA_ESTANCAMIENTO,
    LineaAntiguedad,
    ReporteAntiguedad,
    TotalTramo,
)
from ..domain.exceptions import ReporteNoPermitidoError, SucursalInexistenteError


def sucursal_del_reporte(actor: Actor, sucursal_id: Optional[int]) -> Optional[int]:
    """Qué sucursal puede ver el actor: la pedida, o la suya si no pidió
    ninguna. Lanza ReporteNoPermitidoError si no le corresponde."""
    rol = Rol(actor.rol)
    if rol == Rol.ADMINISTRADOR:
        return sucursal_id
    if rol == Rol.SUPERVISOR and sucursal_id in (None, actor.sucursal_id):
        return actor.sucursal_id
    raise ReporteNoPermitidoError()


def lineas_de_antiguedad(
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    hoy: date,
    sucursal_id: Optional[int] = None,
    dias_para_estancamiento: int = DIAS_PARA_ESTANCAMIENTO,
) -> list[LineaAntiguedad]:
    """Todas las líneas con stock > 0, de la que lleva más días sin venta
    a la que menos. La reutiliza la promoción (HU23) para saber si una
    herramienta está estancada en una sucursal."""
    catalogo = {h.id: h for h in herramientas.listar()}
    nombres = {s.id: s.nombre for s in sucursales.listar()}
    lineas = []
    for fila in movimientos.resumen_inventario():
        herramienta = catalogo.get(fila.herramienta_id)
        if herramienta is None or (sucursal_id is not None and fila.sucursal_id != sucursal_id):
            continue
        stock = stock_desde_totales(fila.unidades_por_tipo)
        if stock <= 0:
            continue
        dias = dias_sin_venta(fila.ultima_salida, fila.primer_movimiento, hoy)
        costo = herramienta.costo_unitario
        lineas.append(LineaAntiguedad(
            herramienta_id=herramienta.id,
            codigo=herramienta.codigo,
            nombre=herramienta.nombre,
            sucursal_id=fila.sucursal_id,
            sucursal_nombre=nombres.get(fila.sucursal_id, f"#{fila.sucursal_id}"),
            stock=stock,
            ultima_venta=fila.ultima_salida,
            dias_sin_venta=dias,
            nunca_vendida=fila.ultima_salida is None,
            tramo=tramo(dias),
            estancada=dias > dias_para_estancamiento,
            costo_unitario=costo,
            valor_inmovilizado=None if costo is None else costo * stock,
        ))
    lineas.sort(key=lambda l: (-l.dias_sin_venta, l.codigo, l.sucursal_nombre))
    return lineas


def construir_reporte_antiguedad(
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    actor: Actor,
    sucursal_id: Optional[int],
    hoy: date,
    dias_minimos: int = 0,
) -> ReporteAntiguedad:
    sucursal_id = sucursal_del_reporte(actor, sucursal_id)
    if sucursal_id is not None and sucursales.obtener_por_id(sucursal_id) is None:
        raise SucursalInexistenteError(sucursal_id)

    lineas = [
        l for l in lineas_de_antiguedad(movimientos, herramientas, sucursales, hoy, sucursal_id)
        if l.dias_sin_venta >= dias_minimos
    ]
    estancadas = [l for l in lineas if l.estancada]
    return ReporteAntiguedad(
        fecha=hoy,
        sucursal_id=sucursal_id,
        dias_minimos=dias_minimos,
        dias_para_estancamiento=DIAS_PARA_ESTANCAMIENTO,
        lineas=tuple(lineas),
        tramos=tuple(
            TotalTramo(
                tramo=etiqueta,
                lineas=sum(1 for l in lineas if l.tramo == etiqueta),
                unidades=sum(l.stock for l in lineas if l.tramo == etiqueta),
            )
            for _, _, etiqueta in TRAMOS
        ),
        total_unidades=sum(l.stock for l in lineas),
        total_estancadas=len(estancadas),
        valor_inmovilizado_estancado=sum(
            (l.valor_inmovilizado for l in estancadas if l.valor_inmovilizado is not None), Decimal("0")
        ),
        lineas_sin_costo=sum(1 for l in lineas if l.costo_unitario is None),
    )
