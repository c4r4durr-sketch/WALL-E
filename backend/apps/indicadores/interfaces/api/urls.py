from django.urls import path

from .views import (
    CierreDiarioExcelView,
    CierreDiarioView,
    ClasificacionABCExcelView,
    ClasificacionABCView,
    EOQPorHerramientaView,
    EOQPorSucursalView,
    PanelAuditoriaView,
    ProductosParaPedirView,
    PromocionesView,
    PuntoReordenPorHerramientaView,
    ReporteAntiguedadExcelView,
    ReporteAntiguedadView,
    TerminarPromocionView,
)
from .views_estadisticas import (
    AntiguedadPorTramoView,
    EstadisticaABCView,
    EstadisticasExcelView,
    MovimientosPorMesView,
    ResumenEstadisticoView,
    StockPorSucursalView,
    TopHerramientasView,
    TransferenciasView,
)

urlpatterns = [
    path("eoq/<int:herramienta_id>/", EOQPorHerramientaView.as_view(), name="indicador-eoq"),
    path("eoq/<int:herramienta_id>/sucursales/", EOQPorSucursalView.as_view(), name="indicador-eoq-sucursales"),
    path("rop/<int:herramienta_id>/", PuntoReordenPorHerramientaView.as_view(), name="indicador-rop"),
    path("abc/", ClasificacionABCView.as_view(), name="indicador-abc"),
    path("abc/excel/", ClasificacionABCExcelView.as_view(), name="indicador-abc-excel"),
    path("panel/", PanelAuditoriaView.as_view(), name="panel-auditoria"),
    path("productos-para-pedir/", ProductosParaPedirView.as_view(), name="productos-para-pedir"),
    path("antiguedad/", ReporteAntiguedadView.as_view(), name="reporte-antiguedad"),
    path("antiguedad/excel/", ReporteAntiguedadExcelView.as_view(), name="reporte-antiguedad-excel"),
    path("promociones/", PromocionesView.as_view(), name="promociones"),
    path("promociones/<int:promocion_id>/terminar/", TerminarPromocionView.as_view(), name="terminar-promocion"),
    path("cierre-diario/", CierreDiarioView.as_view(), name="cierre-diario"),
    path("cierre-diario/excel/", CierreDiarioExcelView.as_view(), name="cierre-diario-excel"),
    # Reportes estadísticos (página /reportes)
    path("estadisticas/resumen/", ResumenEstadisticoView.as_view(), name="estadisticas-resumen"),
    path("estadisticas/movimientos-por-mes/", MovimientosPorMesView.as_view(), name="estadisticas-movimientos"),
    path("estadisticas/top-herramientas/", TopHerramientasView.as_view(), name="estadisticas-top"),
    path("estadisticas/stock-por-sucursal/", StockPorSucursalView.as_view(), name="estadisticas-stock"),
    path("estadisticas/abc/", EstadisticaABCView.as_view(), name="estadisticas-abc"),
    path("estadisticas/antiguedad/", AntiguedadPorTramoView.as_view(), name="estadisticas-antiguedad"),
    path("estadisticas/transferencias/", TransferenciasView.as_view(), name="estadisticas-transferencias"),
    path("estadisticas/excel/", EstadisticasExcelView.as_view(), name="estadisticas-excel"),
]
