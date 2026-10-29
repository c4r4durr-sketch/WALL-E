from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError
from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango, PromocionRepositoryDjango
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.usuarios.domain.entities import Actor
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from ...domain.entities import CierreDiario, PromocionListada, ReporteAntiguedad
from ...domain.exceptions import (
    DatosPromocionInvalidosError,
    PromocionNoAplicableError,
    PromocionNoEncontradaError,
    PromocionNoPermitidaError,
    FechaFuturaError,
    ReporteNoPermitidoError,
    SucursalInexistenteError,
)
from ...use_cases.calcular_eoq import calcular_eoq
from ...use_cases.cierre_diario import construir_cierre
from ...use_cases.calcular_punto_reorden import calcular_punto_reorden
from ...use_cases.clasificar_abc import clasificar_abc
from ...use_cases.panel_auditoria import construir_panel
from ...use_cases.promociones import crear_promocion, estado_promocion, listar_promociones, terminar_promocion
from ...use_cases.reporte_antiguedad import construir_reporte_antiguedad
from ..excel import TIPO_XLSX, excel_abc, excel_antiguedad, excel_cierre_diario, respuesta_excel
from .serializers import (
    CierreDiarioSerializer,
    ClasificacionABCSerializer,
    CrearPromocionSerializer,
    FiltroAntiguedadSerializer,
    FiltroCierreDiarioSerializer,
    FiltroPromocionesSerializer,
    PanelAuditoriaSerializer,
    PromocionSerializer,
    ReporteAntiguedadSerializer,
    ResultadoEOQSerializer,
    ResultadoROPSerializer,
)

# Estas vistas usan APIView (no GenericAPIView) porque no hay un modelo/
# queryset detrás: son puro cálculo. @extend_schema documenta manualmente
# la respuesta para que Swagger la muestre bien, ya que drf-spectacular no
# puede inferirla de un serializer_class como en un ModelViewSet normal.


class EOQPorHerramientaView(APIView):
    """GET /api/indicadores/eoq/<herramienta_id>/
    EOQ (HU17), ajustado a cajas (HU20), calculado con la demanda observada
    de los últimos 12 meses o, sin ventas, con la estimada (HU21). Si faltan
    datos en el catálogo responde 200 con eoq = null y datos_faltantes, para
    que la pantalla diga qué completar."""

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


class PuntoReordenPorHerramientaView(APIView):
    """GET /api/indicadores/rop/<herramienta_id>/
    Punto de reorden (HU18) comparado con el stock total de la herramienta."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ResultadoROPSerializer)
    def get(self, request, herramienta_id: int):
        try:
            resultado = calcular_punto_reorden(
                HerramientaRepositoryDjango(), MovimientoRepositoryDjango(), herramienta_id, ahora=timezone.now()
            )
        except HerramientaNoEncontradaError:
            raise NotFound("No existe esa herramienta.")
        return Response(ResultadoROPSerializer(resultado).data)


def _clasificacion_abc():
    return clasificar_abc(HerramientaRepositoryDjango(), MovimientoRepositoryDjango(), ahora=timezone.now())


class ClasificacionABCView(APIView):
    """GET /api/indicadores/abc/
    Clasificación ABC de todo el catálogo por unidades vendidas en los
    últimos 12 meses, de mayor a menor rotación."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ClasificacionABCSerializer(many=True))
    def get(self, request):
        return Response(ClasificacionABCSerializer(_clasificacion_abc(), many=True).data)


class ClasificacionABCExcelView(APIView):
    """GET /api/indicadores/abc/excel/  (HU25, todos los roles)"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={(200, TIPO_XLSX): OpenApiTypes.BINARY})
    def get(self, request):
        return respuesta_excel(*excel_abc(_clasificacion_abc(), timezone.localdate()))


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
            ahora=timezone.now(),
        )
        return Response(PanelAuditoriaSerializer(panel).data)


def _cierre_diario(request) -> CierreDiario:
    filtro = FiltroCierreDiarioSerializer(data=request.query_params)
    filtro.is_valid(raise_exception=True)
    sucursal_id = filtro.validated_data.get("sucursal", request.user.sucursal_id)
    if sucursal_id is None:
        raise ValidationError({"sucursal": ["Indica la sucursal."]})
    hoy = timezone.localdate()
    try:
        return construir_cierre(
            MovimientoRepositoryDjango(),
            HerramientaRepositoryDjango(),
            SucursalRepositoryDjango(),
            _actor(request),
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


class CierreDiarioView(APIView):
    """GET /api/indicadores/cierre-diario/?sucursal=<id>&fecha=AAAA-MM-DD
    Cierre y resumen diario (HU14): movimientos del día de una sucursal, en
    hora de La Paz, con totales por tipo. Administrador: cualquier sucursal
    (debe indicarla); Supervisor: la suya (por defecto); Empleado: 403."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroCierreDiarioSerializer], responses=CierreDiarioSerializer)
    def get(self, request):
        return Response(CierreDiarioSerializer(_cierre_diario(request)).data)


class CierreDiarioExcelView(APIView):
    """GET /api/indicadores/cierre-diario/excel/?sucursal=&fecha=
    HU25: el mismo cierre, como .xlsx. Mismos permisos."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroCierreDiarioSerializer], responses={(200, TIPO_XLSX): OpenApiTypes.BINARY})
    def get(self, request):
        return respuesta_excel(*excel_cierre_diario(_cierre_diario(request)))


def _reporte_antiguedad(request) -> ReporteAntiguedad:
    filtro = FiltroAntiguedadSerializer(data=request.query_params)
    filtro.is_valid(raise_exception=True)
    try:
        return construir_reporte_antiguedad(
            MovimientoRepositoryDjango(),
            HerramientaRepositoryDjango(),
            SucursalRepositoryDjango(),
            _actor(request),
            filtro.validated_data.get("sucursal"),
            hoy=timezone.localdate(),
            dias_minimos=filtro.validated_data["dias_minimos"],
        )
    except ReporteNoPermitidoError:
        raise PermissionDenied("Solo el Administrador o el Supervisor de esa sucursal pueden ver este reporte.")
    except SucursalInexistenteError:
        raise ValidationError({"sucursal": ["No existe esa sucursal."]})


class ReporteAntiguedadView(APIView):
    """GET /api/indicadores/antiguedad/?sucursal=<id>&dias_minimos=<n>
    Reporte de antigüedad del stock (HU22): días sin venta por herramienta
    y sucursal, tramos y valor inmovilizado. Administrador: una sucursal o
    todas (sin `sucursal`); Supervisor: la suya; Empleado: 403."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroAntiguedadSerializer], responses=ReporteAntiguedadSerializer)
    def get(self, request):
        return Response(ReporteAntiguedadSerializer(_reporte_antiguedad(request)).data)


class ReporteAntiguedadExcelView(APIView):
    """GET /api/indicadores/antiguedad/excel/?sucursal=&dias_minimos=
    HU25: el mismo reporte, como .xlsx. Mismos permisos."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroAntiguedadSerializer], responses={(200, TIPO_XLSX): OpenApiTypes.BINARY})
    def get(self, request):
        reporte = _reporte_antiguedad(request)
        sucursal = SucursalRepositoryDjango().obtener_por_id(reporte.sucursal_id) if reporte.sucursal_id else None
        return respuesta_excel(*excel_antiguedad(reporte, sucursal.nombre if sucursal else None))


SOLO_ADMIN_PROMOCIONES = "Solo el Administrador puede crear o terminar promociones."


class PromocionesView(APIView):
    """GET  /api/indicadores/promociones/?vigentes=true  (todos los roles)
    POST /api/indicadores/promociones/  (solo Administrador)
    HU23: descuento sobre una herramienta estancada en una sucursal. 409 si
    no está estancada ahí o ya tiene una promoción vigente."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroPromocionesSerializer], responses=PromocionSerializer(many=True))
    def get(self, request):
        filtro = FiltroPromocionesSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        listadas = listar_promociones(
            PromocionRepositoryDjango(), hoy=timezone.localdate(), solo_vigentes=filtro.validated_data["vigentes"]
        )
        return Response(PromocionSerializer(listadas, many=True).data)

    @extend_schema(request=CrearPromocionSerializer, responses={201: PromocionSerializer})
    def post(self, request):
        datos = CrearPromocionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        hoy = timezone.localdate()
        try:
            promocion = crear_promocion(
                PromocionRepositoryDjango(),
                MovimientoRepositoryDjango(),
                HerramientaRepositoryDjango(),
                SucursalRepositoryDjango(),
                _actor(request),
                datos.validated_data,
                hoy=hoy,
            )
        except PromocionNoPermitidaError:
            raise PermissionDenied(SOLO_ADMIN_PROMOCIONES)
        except DatosPromocionInvalidosError as error:
            raise ValidationError({campo: [mensaje] for campo, mensaje in error.errores.items()})
        except PromocionNoAplicableError as error:
            raise Conflicto(str(error))
        listada = PromocionListada(promocion, estado_promocion(promocion, hoy))
        return Response(PromocionSerializer(listada).data, status=201)


class TerminarPromocionView(APIView):
    """POST /api/indicadores/promociones/<id>/terminar/
    HU23: corta una promoción vigente antes de su fecha de fin. Solo el
    Administrador; 409 si ya no estaba vigente."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=PromocionSerializer)
    def post(self, request, promocion_id: int):
        hoy = timezone.localdate()
        try:
            promocion = terminar_promocion(PromocionRepositoryDjango(), _actor(request), promocion_id, hoy=hoy)
        except PromocionNoPermitidaError:
            raise PermissionDenied(SOLO_ADMIN_PROMOCIONES)
        except PromocionNoEncontradaError:
            raise NotFound("No existe esa promoción.")
        except PromocionNoAplicableError as error:
            raise Conflicto(str(error))
        return Response(PromocionSerializer(PromocionListada(promocion, estado_promocion(promocion, hoy))).data)
