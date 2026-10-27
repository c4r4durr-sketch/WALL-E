from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.usuarios.domain.entities import Actor
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from ...domain.exceptions import (
    ActualizacionNoPermitidaError,
    FechaFuturaError,
    ReporteNoPermitidoError,
    SinVentasObservadasError,
    SucursalInexistenteError,
)
from ...use_cases.actualizar_demanda import actualizar_demanda_anual
from ...use_cases.calcular_eoq import calcular_eoq
from ...use_cases.cierre_diario import construir_cierre
from ...use_cases.calcular_punto_reorden import calcular_punto_reorden
from ...use_cases.clasificar_abc import clasificar_abc
from ...use_cases.panel_auditoria import construir_panel
from .serializers import (
    CierreDiarioSerializer,
    ClasificacionABCSerializer,
    FiltroCierreDiarioSerializer,
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


class Conflicto(APIException):
    status_code = 409
    default_detail = "La operación no se puede realizar en el estado actual."


def _actor(request) -> Actor:
    usuario = request.user
    return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)


class ActualizarDemandaView(APIView):
    """POST /api/indicadores/eoq/<herramienta_id>/actualizar-demanda/
    HU21: reemplaza la demanda anual estimada del catálogo por la observada
    (ventas de los últimos 12 meses) y devuelve el EOQ recalculado.
    Administrador y Supervisor; Empleado 403; sin ventas en el período 409."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=ResultadoEOQSerializer)
    def post(self, request, herramienta_id: int):
        try:
            resultado = actualizar_demanda_anual(
                HerramientaRepositoryDjango(), MovimientoRepositoryDjango(), _actor(request),
                herramienta_id, ahora=timezone.now(),
            )
        except ActualizacionNoPermitidaError:
            raise PermissionDenied("Solo el Administrador o el Supervisor pueden actualizar la demanda anual.")
        except HerramientaNoEncontradaError:
            raise NotFound("No existe esa herramienta.")
        except SinVentasObservadasError:
            raise Conflicto("No hay ventas en los últimos 12 meses: la demanda anual no se actualiza.")
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


class CierreDiarioView(APIView):
    """GET /api/indicadores/cierre-diario/?sucursal=<id>&fecha=AAAA-MM-DD
    Cierre y resumen diario (HU14): movimientos del día de una sucursal, en
    hora de La Paz, con totales por tipo. Administrador: cualquier sucursal
    (debe indicarla); Supervisor: la suya (por defecto); Empleado: 403."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroCierreDiarioSerializer], responses=CierreDiarioSerializer)
    def get(self, request):
        filtro = FiltroCierreDiarioSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        usuario = request.user
        actor = _actor(request)
        sucursal_id = filtro.validated_data.get("sucursal", usuario.sucursal_id)
        if sucursal_id is None:
            raise ValidationError({"sucursal": ["Indica la sucursal."]})
        hoy = timezone.localdate()
        try:
            cierre = construir_cierre(
                MovimientoRepositoryDjango(),
                HerramientaRepositoryDjango(),
                SucursalRepositoryDjango(),
                actor,
                sucursal_id,
                fecha=filtro.validated_data.get("fecha", hoy),
                hoy=hoy,
            )
        except ReporteNoPermitidoError:
            raise PermissionDenied("Solo el Administrador o el Supervisor de esa sucursal pueden ver su cierre diario.")
        except FechaFuturaError:
            raise ValidationError({"fecha": ["La fecha no puede ser posterior a hoy."]})
        except SucursalInexistenteError:
            raise ValidationError({"sucursal": ["No existe esa sucursal."]})
        return Response(CierreDiarioSerializer(cierre).data)
