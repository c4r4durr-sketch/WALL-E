"""
Caso de uso: EOQ y ROP por sucursal, y el dashboard "Productos para pedir".

Mismas fórmulas que el EOQ y el ROP generales (domain/formulas.py), con
los datos de UNA sucursal:
  D     = lo vendido en esa sucursal en los últimos 12 meses
          (formulas.demanda_de_sucursal decide qué hacer si no vendió)
  S, H  = costo de pedido y de almacenamiento del catálogo
  L     = tiempo de entrega del catálogo
  stock = el de esa sucursal

Hay que pedir para una sucursal si su stock <= su ROP y tiene demanda
(D > 0). El pedido sugerido es el EOQ de esa sucursal en cajas cerradas.

Una ENTRADA solo sube el stock: puede sacar una herramienta de la lista,
pero no cambia su EOQ (que depende de las ventas).

Puro: recibe los repositorios como interfaces y la hora como parámetro.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from apps.catalogo.domain.entities import Herramienta
from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import TIPOS_QUE_CUENTAN_COMO_DEMANDA, stock_desde_totales
from apps.usuarios.domain.entities import Sucursal
from apps.usuarios.domain.repositories import SucursalRepository

from ..domain import formulas
from ..domain.entities import PERIODO_DEMANDA_DIAS, EOQPorSucursal, ProductosParaPedir, ReposicionSucursal
from ..domain.exceptions import SucursalInexistenteError
from .calcular_eoq import resultado_eoq
from .calcular_punto_reorden import resultado_rop


def _a_float(valor):
    return None if valor is None else float(valor)


def linea_sucursal(
    herramienta: Herramienta,
    sucursal: Sucursal,
    stock: int,
    vendido_sucursal: int,
    vendido_total: int,
    sucursales_activas: int,
) -> ReposicionSucursal:
    """Cálculo puro para una herramienta en una sucursal."""
    demanda, fuente = formulas.demanda_de_sucursal(
        herramienta.demanda_anual, vendido_sucursal, vendido_total, sucursales_activas
    )
    costo_pedido = _a_float(herramienta.costo_pedido)
    costo_almacenamiento = _a_float(herramienta.costo_almacenamiento_unitario)
    entrega = herramienta.tiempo_entrega_dias

    faltantes = []
    if demanda is None:
        faltantes.append("demanda_anual")
    if entrega is None:
        faltantes.append("tiempo_entrega_dias")
    if costo_pedido is None:
        faltantes.append("costo_pedido")
    if costo_almacenamiento is None or costo_almacenamiento <= 0:
        faltantes.append("costo_almacenamiento_unitario")

    d = _a_float(demanda)
    rop = formulas.calcular_rop(d, entrega)
    eoq = formulas.calcular_eoq(d, costo_pedido, costo_almacenamiento)
    return ReposicionSucursal(
        herramienta_id=herramienta.id,
        codigo=herramienta.codigo,
        nombre=herramienta.nombre,
        sucursal_id=sucursal.id,
        sucursal_nombre=sucursal.nombre,
        stock=stock,
        demanda_observada=vendido_sucursal,
        demanda_usada=demanda,
        fuente_demanda=fuente,
        punto_reorden=None if rop is None else round(rop, 2),
        eoq=None if eoq is None else round(eoq, 2),
        eoq_ajustado_cajas=None if eoq is None else formulas.ajustar_a_cajas(eoq, herramienta.unidades_por_caja),
        unidades_por_caja=herramienta.unidades_por_caja,
        # Sin demanda (D = 0) el ROP es 0 y un stock en 0 "lo tocaría": no
        # hay nada que reponer, así que no se pide.
        requiere_reorden=rop is not None and bool(demanda) and stock <= rop,
        datos_faltantes=tuple(faltantes),
    )


class _Datos:
    """Lo que necesitan los dos casos de uso, en dos consultas agregadas."""

    def __init__(self, movimientos: MovimientoRepository, sucursales: SucursalRepository, ahora: datetime):
        self.activas = sorted((s for s in sucursales.listar() if s.activa), key=lambda s: s.id)
        self.stock: dict[tuple[int, int], int] = {
            (f.herramienta_id, f.sucursal_id): stock_desde_totales(f.unidades_por_tipo)
            for f in movimientos.resumen_inventario()
        }
        self.vendido = movimientos.unidades_por_herramienta_y_sucursal(
            TIPOS_QUE_CUENTAN_COMO_DEMANDA, desde=ahora - timedelta(days=PERIODO_DEMANDA_DIAS)
        )
        self.vendido_total: dict[int, int] = defaultdict(int)
        for (herramienta_id, _), unidades in self.vendido.items():
            self.vendido_total[herramienta_id] += unidades

    def lineas(self, herramienta: Herramienta, solo: Optional[list[Sucursal]] = None) -> list[ReposicionSucursal]:
        return [
            linea_sucursal(
                herramienta,
                sucursal,
                self.stock.get((herramienta.id, sucursal.id), 0),
                self.vendido.get((herramienta.id, sucursal.id), 0),
                self.vendido_total[herramienta.id],
                len(self.activas),
            )
            for sucursal in (self.activas if solo is None else solo)
        ]


def eoq_por_sucursal(
    herramientas: HerramientaRepository,
    movimientos: MovimientoRepository,
    sucursales: SucursalRepository,
    herramienta_id: int,
    ahora: datetime,
) -> EOQPorSucursal:
    herramienta = herramientas.obtener_por_id(herramienta_id)
    if herramienta is None:
        raise HerramientaNoEncontradaError(herramienta_id)
    datos = _Datos(movimientos, sucursales, ahora)
    vendido = datos.vendido_total[herramienta_id]
    # El ROP general compara con el stock de TODAS las sucursales, como siempre.
    stock_total = sum(s for (h, _), s in datos.stock.items() if h == herramienta_id)
    return EOQPorSucursal(
        general_eoq=resultado_eoq(herramienta, vendido),
        general_rop=resultado_rop(herramienta, stock_total, vendido),
        sucursales=datos.lineas(herramienta),
    )


def productos_para_pedir(
    herramientas: HerramientaRepository,
    movimientos: MovimientoRepository,
    sucursales: SucursalRepository,
    ahora: datetime,
    sucursal_id: Optional[int] = None,
) -> ProductosParaPedir:
    """Todas las sucursales activas, o solo `sucursal_id` si se indica."""
    datos = _Datos(movimientos, sucursales, ahora)
    solo = None
    if sucursal_id is not None:
        solo = [s for s in datos.activas if s.id == sucursal_id]
        if not solo:
            raise SucursalInexistenteError(sucursal_id)

    lineas: list[ReposicionSucursal] = []
    sin_datos = 0
    for herramienta in herramientas.listar():
        calculadas = datos.lineas(herramienta, solo)
        if any(linea.punto_reorden is None for linea in calculadas):
            sin_datos += 1
        lineas.extend(linea for linea in calculadas if linea.requiere_reorden)

    # Lo más urgente primero: más por debajo de su ROP.
    lineas.sort(key=lambda l: (l.stock - l.punto_reorden, l.codigo, l.sucursal_id))
    return ProductosParaPedir(
        total_lineas=len(lineas),
        total_herramientas=len({l.herramienta_id for l in lineas}),
        herramientas_sin_datos=sin_datos,
        lineas=lineas,
    )
