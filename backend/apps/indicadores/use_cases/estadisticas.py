"""
Casos de uso: reportes estadísticos de la página /reportes.

Todos reciben el mismo filtro (desde, hasta, sucursal) y aplican los
mismos permisos que el cierre diario y la antigüedad:
  - Administrador: una sucursal o todas (sucursal_id None);
  - Supervisor: solo la suya (sin indicarla, se usa la suya);
  - Empleado: no ve los reportes.

Puros: reciben el repositorio de estadísticas (que ya devuelve las sumas
hechas por la base) y la fecha de hoy. Sin datos en el periodo responden
listas vacías, no un error.
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.value_objects import TipoMovimiento as T
from apps.transferencias.domain.value_objects import EstadoTransferencia as E
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.repositories import SucursalRepository

from ..domain.antiguedad import TRAMOS, dias_sin_venta, tramo
from ..domain.entities import DIAS_PARA_ESTANCAMIENTO
from ..domain.estadisticas import (
    AntiguedadPorTramo,
    CantidadEstado,
    EstadisticaABC,
    EstadisticaTransferencias,
    MovimientosMes,
    MovimientosPorMes,
    Periodo,
    ResumenEstadistico,
    StockPorSucursal,
    TopHerramientas,
    TramoValor,
    TransferenciasMes,
    clasificar_por_valor,
    errores_de_periodo,
    meses_del_rango,
    periodo_por_defecto,
)
from ..domain.exceptions import PeriodoInvalidoError, SucursalInexistenteError
from ..domain.repositories import EstadisticasRepository
from .panel_auditoria import construir_panel
from .reporte_antiguedad import sucursal_del_reporte

TOP_HERRAMIENTAS = 10


def periodo_del_reporte(
    sucursales: SucursalRepository,
    actor: Actor,
    desde: Optional[date],
    hasta: Optional[date],
    sucursal_id: Optional[int],
    hoy: date,
) -> Periodo:
    """Permisos, sucursal y fechas del filtro. Sin fechas: los últimos 12
    meses. Lanza ReporteNoPermitidoError, SucursalInexistenteError o
    PeriodoInvalidoError."""
    sucursal_id = sucursal_del_reporte(actor, sucursal_id)
    if sucursal_id is not None and sucursales.obtener_por_id(sucursal_id) is None:
        raise SucursalInexistenteError(sucursal_id)
    hasta = hasta or hoy
    desde = desde or periodo_por_defecto(hasta)[0]
    errores = errores_de_periodo(desde, hasta, hoy)
    if errores:
        raise PeriodoInvalidoError(errores)
    return Periodo(desde=desde, hasta=hasta, sucursal_id=sucursal_id)


def movimientos_por_mes(repo: EstadisticasRepository, periodo: Periodo) -> MovimientosPorMes:
    filas = repo.unidades_por_mes(periodo.desde, periodo.hasta, periodo.sucursal_id)
    if not filas:
        return MovimientosPorMes(periodo, ())
    unidades: dict[date, dict[str, int]] = defaultdict(dict)
    for fila in filas:
        unidades[fila.mes][fila.tipo_movimiento] = fila.unidades
    # Todos los meses del rango, también los que no tuvieron movimientos,
    # para que la línea no salte meses.
    meses = tuple(
        MovimientosMes(
            mes=mes,
            entradas=unidades[mes].get(T.ENTRADA.value, 0),
            salidas=unidades[mes].get(T.SALIDA.value, 0),
            ajustes_positivos=unidades[mes].get(T.AJUSTE_POSITIVO.value, 0),
            ajustes_negativos=unidades[mes].get(T.AJUSTE_NEGATIVO.value, 0),
        )
        for mes in meses_del_rango(periodo.desde, periodo.hasta)
    )
    return MovimientosPorMes(periodo, meses)


def top_herramientas(repo: EstadisticasRepository, periodo: Periodo) -> TopHerramientas:
    ventas = repo.ventas_por_herramienta(periodo.desde, periodo.hasta, periodo.sucursal_id)
    return TopHerramientas(periodo, tuple(ventas[:TOP_HERRAMIENTAS]))


def stock_por_sucursal(repo: EstadisticasRepository, periodo: Periodo) -> StockPorSucursal:
    sucursales = tuple(repo.stock_por_sucursal(periodo.hasta, periodo.sucursal_id))
    return StockPorSucursal(
        periodo=periodo,
        sucursales=sucursales,
        total_unidades=sum(s.unidades for s in sucursales),
        total_valor=sum((s.valor for s in sucursales), Decimal("0")),
    )


def clasificacion_abc(repo: EstadisticasRepository, periodo: Periodo) -> EstadisticaABC:
    ventas = repo.ventas_por_herramienta(periodo.desde, periodo.hasta, periodo.sucursal_id)
    valoradas = sum(1 for v in ventas if v.monto)
    sin_costo = sum(1 for v in ventas if v.monto is None)
    clases, pareto, total = clasificar_por_valor(ventas, sin_ventas=repo.total_herramientas() - valoradas - sin_costo)
    return EstadisticaABC(periodo, clases, pareto, total, herramientas_sin_costo=sin_costo)


def antiguedad_por_tramo(repo: EstadisticasRepository, periodo: Periodo) -> AntiguedadPorTramo:
    """Valor inmovilizado por tramo de días sin venta, al cierre de
    "hasta" (con hasta = hoy coincide con el reporte de antigüedad)."""
    con_stock = [i for i in repo.inventario(periodo.hasta, periodo.sucursal_id) if i.stock > 0]
    if not con_stock:
        return AntiguedadPorTramo(periodo, (), Decimal("0"), 0)
    por_tramo = defaultdict(list)
    for item in con_stock:
        por_tramo[tramo(dias_sin_venta(item.ultima_salida, item.primer_movimiento, periodo.hasta))].append(item)
    tramos = tuple(
        TramoValor(
            tramo=etiqueta,
            herramientas=len(por_tramo[etiqueta]),
            unidades=sum(i.stock for i in por_tramo[etiqueta]),
            valor=sum((i.stock * i.costo_unitario for i in por_tramo[etiqueta] if i.costo_unitario is not None),
                      Decimal("0")),
        )
        for _, _, etiqueta in TRAMOS
    )
    return AntiguedadPorTramo(
        periodo=periodo,
        tramos=tramos,
        valor_total=sum((t.valor for t in tramos), Decimal("0")),
        lineas_sin_costo=sum(1 for i in con_stock if i.costo_unitario is None),
    )


def transferencias(repo: EstadisticasRepository, periodo: Periodo) -> EstadisticaTransferencias:
    filas = repo.transferencias_por_mes(periodo.desde, periodo.hasta, periodo.sucursal_id)
    if not filas:
        return EstadisticaTransferencias(periodo, (), (), 0)
    por_mes: dict[date, dict[str, int]] = defaultdict(dict)
    for fila in filas:
        por_mes[fila.mes][fila.estado] = fila.cantidad
    estados = (E.PENDIENTE.value, E.COMPLETADA.value, E.RECHAZADA.value)
    return EstadisticaTransferencias(
        periodo=periodo,
        por_estado=tuple(CantidadEstado(e, sum(f.cantidad for f in filas if f.estado == e)) for e in estados),
        por_mes=tuple(
            TransferenciasMes(mes, *(por_mes[mes].get(e, 0) for e in estados))
            for mes in meses_del_rango(periodo.desde, periodo.hasta)
        ),
        total=sum(f.cantidad for f in filas),
    )


def resumen(
    repo: EstadisticasRepository,
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    periodo: Periodo,
    hoy: date,
    ahora: datetime,
) -> ResumenEstadistico:
    ventas = repo.ventas_por_herramienta(periodo.desde, periodo.hasta, periodo.sucursal_id)
    stock = repo.stock_por_sucursal(periodo.hasta, periodo.sucursal_id)
    # Estancadas: misma regla que el panel y la antigüedad, en la sucursal
    # del filtro y al cierre de "hasta".
    estancadas = sum(
        1 for i in repo.inventario(periodo.hasta, periodo.sucursal_id)
        if i.stock > 0 and dias_sin_venta(i.ultima_salida, i.primer_movimiento, periodo.hasta) > DIAS_PARA_ESTANCAMIENTO
    )
    # Alertas de reorden: las mismas del panel (hoy, stock de todas las
    # sucursales), para que la cifra coincida con la pantalla de inicio.
    panel = construir_panel(movimientos, herramientas, sucursales, hoy=hoy, ahora=ahora)
    return ResumenEstadistico(
        periodo=periodo,
        total_movimientos=repo.total_movimientos(periodo.desde, periodo.hasta, periodo.sucursal_id),
        unidades_vendidas=sum(v.unidades for v in ventas),
        valor_inventario=sum((s.valor for s in stock), Decimal("0")),
        alertas_reorden=panel.total_alertas_stock,
        herramientas_estancadas=estancadas,
    )
