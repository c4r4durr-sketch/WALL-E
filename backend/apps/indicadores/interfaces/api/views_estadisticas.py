from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from ...domain.estadisticas import Periodo
from ...domain.exceptions import PeriodoInvalidoError, ReporteNoPermitidoError, SucursalInexistenteError
from ...infrastructure.estadisticas import EstadisticasRepositoryDjango
from ...use_cases import estadisticas as casos
from ..excel import TIPO_XLSX, excel_estadisticas, respuesta_excel
from .serializers_estadisticas import (
    AntiguedadPorTramoSerializer,
    EstadisticaABCSerializer,
    EstadisticaTransferenciasSerializer,
    FiltroEstadisticasSerializer,
    MovimientosPorMesSerializer,
    ResumenEstadisticoSerializer,
    StockPorSucursalSerializer,
    TopHerramientasSerializer,
)
from .views import Conflicto, REPORTE_VACIO, _actor

# GET /api/indicadores/estadisticas/<reporte>/?desde=&hasta=&sucursal=
# Solo lectura. Administrador: una sucursal o todas; Supervisor: la suya
# (otra -> 403); Empleado: 403. Fechas futuras o "hasta" < "desde" -> 400.


def _periodo(request) -> Periodo:
    filtro = FiltroEstadisticasSerializer(data=request.query_params)
    filtro.is_valid(raise_exception=True)
    try:
        return casos.periodo_del_reporte(
            SucursalRepositoryDjango(),
            _actor(request),
            filtro.validated_data.get("desde"),
            filtro.validated_data.get("hasta"),
            filtro.validated_data.get("sucursal"),
            hoy=timezone.localdate(),
        )
    except ReporteNoPermitidoError:
        raise PermissionDenied("Solo el Administrador o el Supervisor de esa sucursal pueden ver estos reportes.")
    except SucursalInexistenteError:
        raise ValidationError({"sucursal": ["No existe esa sucursal."]})
    except PeriodoInvalidoError as error:
        raise ValidationError({campo: [mensaje] for campo, mensaje in error.errores.items()})


def _resumen(repo, periodo):
    return casos.resumen(
        repo,
        MovimientoRepositoryDjango(),
        HerramientaRepositoryDjango(),
        SucursalRepositoryDjango(),
        periodo,
        hoy=timezone.localdate(),
        ahora=timezone.now(),
    )


class _EstadisticaView(APIView):
    """Base: valida el filtro, llama al caso de uso y serializa."""

    permission_classes = [IsAuthenticated]
    serializer = None

    def calcular(self, repo, periodo):
        raise NotImplementedError

    def get(self, request):
        return Response(self.serializer(self.calcular(EstadisticasRepositoryDjango(), _periodo(request))).data)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=MovimientosPorMesSerializer)
class MovimientosPorMesView(_EstadisticaView):
    """.../movimientos-por-mes/: unidades de entradas, salidas y ajustes por mes."""

    serializer = MovimientosPorMesSerializer

    def calcular(self, repo, periodo):
        return casos.movimientos_por_mes(repo, periodo)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=TopHerramientasSerializer)
class TopHerramientasView(_EstadisticaView):
    """.../top-herramientas/: las 10 más vendidas, unidades y monto (salidas × costo)."""

    serializer = TopHerramientasSerializer

    def calcular(self, repo, periodo):
        return casos.top_herramientas(repo, periodo)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=StockPorSucursalSerializer)
class StockPorSucursalView(_EstadisticaView):
    """.../stock-por-sucursal/: unidades y valor del inventario al cierre de "hasta"."""

    serializer = StockPorSucursalSerializer

    def calcular(self, repo, periodo):
        return casos.stock_por_sucursal(repo, periodo)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=EstadisticaABCSerializer)
class EstadisticaABCView(_EstadisticaView):
    """.../abc/: herramientas y % del valor por clase, y la curva de Pareto."""

    serializer = EstadisticaABCSerializer

    def calcular(self, repo, periodo):
        return casos.clasificacion_abc(repo, periodo)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=AntiguedadPorTramoSerializer)
class AntiguedadPorTramoView(_EstadisticaView):
    """.../antiguedad/: valor inmovilizado por tramo de días sin venta."""

    serializer = AntiguedadPorTramoSerializer

    def calcular(self, repo, periodo):
        return casos.antiguedad_por_tramo(repo, periodo)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=EstadisticaTransferenciasSerializer)
class TransferenciasView(_EstadisticaView):
    """.../transferencias/: solicitadas en el periodo, por estado y por mes."""

    serializer = EstadisticaTransferenciasSerializer

    def calcular(self, repo, periodo):
        return casos.transferencias(repo, periodo)


@extend_schema(parameters=[FiltroEstadisticasSerializer], responses=ResumenEstadisticoSerializer)
class ResumenEstadisticoView(_EstadisticaView):
    """.../resumen/: KPI del periodo."""

    serializer = ResumenEstadisticoSerializer

    def calcular(self, repo, periodo):
        return _resumen(repo, periodo)


class EstadisticasExcelView(APIView):
    """GET /api/indicadores/estadisticas/excel/?desde=&hasta=&sucursal=
    Un libro con una hoja por gráfico (las mismas tablas que la pantalla).
    Mismos permisos; 409 si el periodo no tiene ningún dato."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroEstadisticasSerializer], responses={(200, TIPO_XLSX): OpenApiTypes.BINARY})
    def get(self, request):
        periodo = _periodo(request)
        repo = EstadisticasRepositoryDjango()
        datos = {
            "resumen": _resumen(repo, periodo),
            "movimientos": casos.movimientos_por_mes(repo, periodo),
            "top": casos.top_herramientas(repo, periodo),
            "stock": casos.stock_por_sucursal(repo, periodo),
            "abc": casos.clasificacion_abc(repo, periodo),
            "antiguedad": casos.antiguedad_por_tramo(repo, periodo),
            "transferencias": casos.transferencias(repo, periodo),
        }
        vacio = not any((
            datos["movimientos"].meses, datos["top"].herramientas, datos["stock"].sucursales,
            datos["abc"].pareto, datos["antiguedad"].tramos, datos["transferencias"].por_estado,
        ))
        if vacio:
            raise Conflicto(REPORTE_VACIO)
        sucursal = SucursalRepositoryDjango().obtener_por_id(periodo.sucursal_id) if periodo.sucursal_id else None
        return respuesta_excel(*excel_estadisticas(datos, sucursal.nombre if sucursal else None))
