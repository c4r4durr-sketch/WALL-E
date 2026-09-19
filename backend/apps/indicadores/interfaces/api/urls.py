from django.urls import path

from .views import ClasificacionABCView, EOQPorHerramientaView, PuntoReordenPorHerramientaView

urlpatterns = [
    path("eoq/<int:herramienta_id>/", EOQPorHerramientaView.as_view(), name="indicador-eoq"),
    path("rop/<int:herramienta_id>/", PuntoReordenPorHerramientaView.as_view(), name="indicador-rop"),
    path("abc/", ClasificacionABCView.as_view(), name="indicador-abc"),
]
