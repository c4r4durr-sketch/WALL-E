from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.domain.entities import Actor

from ...domain.entities import FiltroHistorial
from ...domain.exceptions import ConsultaNoPermitidaError, FiltroInvalidoError
from ...domain.value_objects import AccionAuditoria
from ...infrastructure.repositories import HistorialRepositoryDjango
from ...use_cases import consultar_historial as casos
from .serializers import FiltroHistorialSerializer, OpcionesHistorialSerializer, PaginaHistorialSerializer

MENSAJE_SIN_ACCESO = "Solo el Administrador y el Supervisor pueden consultar el historial de modificaciones."


def _actor(request) -> Actor:
    usuario = request.user
    return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)


class HistorialView(APIView):
    """GET /api/auditoria/historial/?desde=&hasta=&usuario=&tabla=&accion=&pagina=&tamano=
    Historial de modificaciones (HU13), del más reciente al más antiguo,
    paginado. Solo lectura. Administrador y Supervisor; Empleado 403."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FiltroHistorialSerializer], responses=PaginaHistorialSerializer)
    def get(self, request):
        entrada = FiltroHistorialSerializer(data=request.query_params)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        filtro = FiltroHistorial(
            desde=datos.get("desde"),
            hasta=datos.get("hasta"),
            usuario_id=datos.get("usuario"),
            tabla=datos.get("tabla"),
            accion=AccionAuditoria(datos["accion"]) if datos.get("accion") else None,
        )
        try:
            pagina = casos.consultar_historial(
                HistorialRepositoryDjango(), _actor(request), filtro, datos["pagina"], datos["tamano"]
            )
        except ConsultaNoPermitidaError:
            raise PermissionDenied(MENSAJE_SIN_ACCESO)
        except FiltroInvalidoError as error:
            raise ValidationError({campo: [mensaje] for campo, mensaje in error.errores.items()})
        return Response(PaginaHistorialSerializer(pagina).data)


class OpcionesHistorialView(APIView):
    """GET /api/auditoria/historial/opciones/
    Tablas, autores y acciones que aparecen en el historial (para los
    filtros de la pantalla)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpcionesHistorialSerializer)
    def get(self, request):
        try:
            opciones = casos.opciones_de_filtro(HistorialRepositoryDjango(), _actor(request))
        except ConsultaNoPermitidaError:
            raise PermissionDenied(MENSAJE_SIN_ACCESO)
        return Response(OpcionesHistorialSerializer(opciones).data)
