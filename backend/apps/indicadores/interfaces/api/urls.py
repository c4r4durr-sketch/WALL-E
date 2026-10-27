from django.urls import path

from .views import (
    ActualizarDemandaView,
    CierreDiarioExcelView,
    CierreDiarioView,
    ClasificacionABCExcelView,
    ClasificacionABCView,
    EOQPorHerramientaView,
    PanelAuditoriaView,
    PromocionesView,
    PuntoReordenPorHerramientaView,
    ReporteAntiguedadExcelView,
    ReporteAntiguedadView,
    TerminarPromocionView,
)

urlpatterns = [
    path("eoq/<int:herramienta_id>/", EOQPorHerramientaView.as_view(), name="indicador-eoq"),
    path("eoq/<int:herramienta_id>/actualizar-demanda/", ActualizarDemandaView.as_view(),
         name="indicador-actualizar-demanda"),
    path("rop/<int:herramienta_id>/", PuntoReordenPorHerramientaView.as_view(), name="indicador-rop"),
    path("abc/", ClasificacionABCView.as_view(), name="indicador-abc"),
    path("abc/excel/", ClasificacionABCExcelView.as_view(), name="indicador-abc-excel"),
    path("panel/", PanelAuditoriaView.as_view(), name="panel-auditoria"),
    path("antiguedad/", ReporteAntiguedadView.as_view(), name="reporte-antiguedad"),
    path("antiguedad/excel/", ReporteAntiguedadExcelView.as_view(), name="reporte-antiguedad-excel"),
    path("promociones/", PromocionesView.as_view(), name="promociones"),
    path("promociones/<int:promocion_id>/terminar/", TerminarPromocionView.as_view(), name="terminar-promocion"),
    path("cierre-diario/", CierreDiarioView.as_view(), name="cierre-diario"),
    path("cierre-diario/excel/", CierreDiarioExcelView.as_view(), name="cierre-diario-excel"),
]
