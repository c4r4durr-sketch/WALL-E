from django.urls import path

from .views import HistorialView, OpcionesHistorialView

urlpatterns = [
    path("historial/", HistorialView.as_view(), name="historial"),
    path("historial/opciones/", OpcionesHistorialView.as_view(), name="historial-opciones"),
]
