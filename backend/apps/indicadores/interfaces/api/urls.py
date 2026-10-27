from django.urls import path

from .views import (
    ActualizarDemandaView,
    CierreDiarioView,
    ClasificacionABCView,
    EOQPorHerramientaView,
    PanelAuditoriaView,
    PuntoReordenPorHerramientaView,
)

urlpatterns = [
    path("eoq/<int:herramienta_id>/", EOQPorHerramientaView.as_view(), name="indicador-eoq"),
    path("eoq/<int:herramienta_id>/actualizar-demanda/", ActualizarDemandaView.as_view(),
         name="indicador-actualizar-demanda"),
    path("rop/<int:herramienta_id>/", PuntoReordenPorHerramientaView.as_view(), name="indicador-rop"),
    path("abc/", ClasificacionABCView.as_view(), name="indicador-abc"),
    path("panel/", PanelAuditoriaView.as_view(), name="panel-auditoria"),
    path("cierre-diario/", CierreDiarioView.as_view(), name="cierre-diario"),
]
