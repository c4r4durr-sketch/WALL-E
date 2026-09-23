from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from ...use_cases.calcular_eoq import calcular_eoq
from ...use_cases.calcular_punto_reorden import calcular_punto_reorden
from ...use_cases.clasificar_abc import clasificar_abc
from ...use_cases.panel_auditoria import construir_panel
from .serializers import (
    ClasificacionABCSerializer,
    PanelAuditoriaSerializer,
    ResultadoEOQSerializer,
    ResultadoROPSerializer,
)

# Estas vistas usan APIView (no GenericAPIView) porque no hay un modelo/
# queryset detrás: son puro cálculo. @extend_schema documenta manualmente
# la respuesta para que Swagger la muestre bien, ya que drf-spectacular no
# puede inferirla de un serializer_class como en un ModelViewSet normal.


class EOQPorHerramientaView(APIView):
    """GET /api/indicadores/eoq/<herramienta_id>/
    EOQ (HU17), ajustado a cajas (HU20), y demanda observada de los últimos
    12 meses (HU21). Si faltan datos en el catálogo responde 200 con
    eoq = null y datos_faltantes, para que la pantalla diga qué completar."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ResultadoEOQSerializer)
    def get(self, request, herramienta_id: int):
        try:
            resultado = calcular_eoq(
                HerramientaRepositoryDjango(), MovimientoRepositoryDjango(), herramienta_id, ahora=timezone.now()
            )
        except HerramientaNoEncontradaError:
            raise NotFound("No existe esa herramienta.")
        return Response(ResultadoEOQSerializer(resultado).data)


class PuntoReordenPorHerramientaView(APIView):
    """GET /api/indicadores/rop/<herramienta_id>/
    Punto de reorden (HU18) comparado con el stock total de la herramienta."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ResultadoROPSerializer)
    def get(self, request, herramienta_id: int):
        try:
            resultado = calcular_punto_reorden(
                HerramientaRepositoryDjango(), MovimientoRepositoryDjango(), herramienta_id
            )
        except HerramientaNoEncontradaError:
            raise NotFound("No existe esa herramienta.")
        return Response(ResultadoROPSerializer(resultado).data)


class ClasificacionABCView(APIView):
    """GET /api/indicadores/abc/
    Clasificación ABC de todo el catálogo por unidades vendidas en los
    últimos 12 meses, de mayor a menor rotación."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ClasificacionABCSerializer(many=True))
    def get(self, request):
        resultado = clasificar_abc(
            HerramientaRepositoryDjango(), MovimientoRepositoryDjango(), ahora=timezone.now()
        )
        return Response(ClasificacionABCSerializer(resultado, many=True).data)


class PanelAuditoriaView(APIView):
    """GET /api/indicadores/panel/
    Panel principal (HU24): alertas de reorden, herramientas estancadas y
    totales. Lo ven todos los roles (es la pantalla de inicio)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=PanelAuditoriaSerializer)
    def get(self, request):
        panel = construir_panel(
            MovimientoRepositoryDjango(),
            HerramientaRepositoryDjango(),
            SucursalRepositoryDjango(),
            hoy=timezone.localdate(),
        )
        return Response(PanelAuditoriaSerializer(panel).data)
