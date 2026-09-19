from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ClasificacionABCSerializer, ResultadoEOQSerializer, ResultadoROPSerializer

# Estas vistas usan APIView (no GenericAPIView) porque no hay un modelo/
# queryset detrás: son puro cálculo. @extend_schema documenta manualmente
# la respuesta para que Swagger la muestre bien, ya que drf-spectacular no
# puede inferirla de un serializer_class como en un ModelViewSet normal.


class EOQPorHerramientaView(APIView):
    """GET /api/indicadores/eoq/<herramienta_id>/
    Va a invocar use_cases.calcular_eoq. Placeholder: responde 501 hasta
    que ese use_case y el armado de D/S/H estén implementados."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ResultadoEOQSerializer)
    def get(self, request, herramienta_id: int):
        return Response(
            {"detail": "Pendiente de implementar."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class PuntoReordenPorHerramientaView(APIView):
    """GET /api/indicadores/rop/<herramienta_id>/
    Va a invocar use_cases.calcular_punto_reorden. Placeholder."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ResultadoROPSerializer)
    def get(self, request, herramienta_id: int):
        return Response(
            {"detail": "Pendiente de implementar."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class ClasificacionABCView(APIView):
    """GET /api/indicadores/abc/
    Va a invocar use_cases.clasificar_abc sobre todas las herramientas.
    Placeholder."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ClasificacionABCSerializer(many=True))
    def get(self, request):
        return Response(
            {"detail": "Pendiente de implementar."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
