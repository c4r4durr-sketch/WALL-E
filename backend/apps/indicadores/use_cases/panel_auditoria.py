"""
Caso de uso: panel de auditoría (HU24), el dashboard principal.

Reemplaza a las vistas SQL vw_panel_auditoria, vw_alertas_reorden y
vw_herramientas_estancadas del script descartado. Puro: recibe los
repositorios como interfaces y la fecha de hoy como parámetro (así se
prueba sin reloj ni base de datos).

  - Alerta de reorden (HU18): stock total de la herramienta, sumando todas
    las sucursales, <= ROP. ROP y pedido sugerido (EOQ ajustado a cajas,
    HU19/HU20) salen de domain/formulas.py.
  - Estancada (HU22): stock > 0 en una sucursal y más de
    DIAS_PARA_ESTANCAMIENTO días sin una SALIDA real (los ajustes no son
    ventas). Si nunca se vendió, se cuenta desde su primer movimiento ahí,
    para no marcar como estancado algo que acaba de ingresar.
"""

from collections import defaultdict
from datetime import date

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import stock_desde_totales
from apps.usuarios.domain.repositories import SucursalRepository

from ..domain.entities import (
    DIAS_PARA_ESTANCAMIENTO,
    AlertaReorden,
    HerramientaEstancada,
    PanelAuditoria,
)
from .calcular_eoq import resultado_eoq
from .calcular_punto_reorden import resultado_rop


def construir_panel(
    movimientos: MovimientoRepository,
    herramientas: HerramientaRepository,
    sucursales: SucursalRepository,
    hoy: date,
    dias_para_estancamiento: int = DIAS_PARA_ESTANCAMIENTO,
) -> PanelAuditoria:
    catalogo = {h.id: h for h in herramientas.listar()}
    todas_las_sucursales = {s.id: s for s in sucursales.listar()}
    resumen = [r for r in movimientos.resumen_inventario() if r.herramienta_id in catalogo]

    stock_total: dict[int, int] = defaultdict(int)
    estancadas: list[HerramientaEstancada] = []
    for fila in resumen:
        stock = stock_desde_totales(fila.unidades_por_tipo)
        stock_total[fila.herramienta_id] += stock
        if stock <= 0:
            continue
        referencia = fila.ultima_salida or fila.primer_movimiento
        dias = (hoy - referencia.date()).days
        if dias > dias_para_estancamiento:
            herramienta = catalogo[fila.herramienta_id]
            sucursal = todas_las_sucursales.get(fila.sucursal_id)
            estancadas.append(HerramientaEstancada(
                herramienta_id=herramienta.id,
                codigo=herramienta.codigo,
                nombre=herramienta.nombre,
                sucursal_id=fila.sucursal_id,
                sucursal_nombre=sucursal.nombre if sucursal else f"#{fila.sucursal_id}",
                stock=stock,
                dias_sin_venta=dias,
                nunca_vendida=fila.ultima_salida is None,
            ))

    # Misma regla y mismos cálculos que los endpoints de ROP y EOQ
    # (resultado_rop / resultado_eoq): el panel no tiene fórmulas propias.
    alertas: list[AlertaReorden] = []
    sin_datos_rop = 0
    for herramienta in catalogo.values():
        rop = resultado_rop(herramienta, stock_total[herramienta.id])
        if rop.punto_reorden is None:
            sin_datos_rop += 1
            continue
        if rop.requiere_reorden:
            alertas.append(AlertaReorden(
                herramienta_id=herramienta.id,
                codigo=herramienta.codigo,
                nombre=herramienta.nombre,
                stock_total=rop.stock_total,
                punto_reorden=rop.punto_reorden,
                pedido_sugerido=resultado_eoq(herramienta).eoq_ajustado_cajas,
                unidades_por_caja=herramienta.unidades_por_caja,
            ))

    # Lo más urgente primero: más por debajo del ROP / más días sin venta.
    alertas.sort(key=lambda a: a.stock_total - a.punto_reorden)
    estancadas.sort(key=lambda e: e.dias_sin_venta, reverse=True)

    return PanelAuditoria(
        total_alertas_stock=len(alertas),
        total_herramientas_estancadas=len(estancadas),
        total_herramientas=len(catalogo),
        total_sucursales_activas=sum(1 for s in todas_las_sucursales.values() if s.activa),
        herramientas_sin_datos_rop=sin_datos_rop,
        dias_para_estancamiento=dias_para_estancamiento,
        alertas=alertas,
        estancadas=estancadas,
    )
