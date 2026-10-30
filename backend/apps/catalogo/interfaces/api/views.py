from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.proveedores.infrastructure.repositories import ProveedorRepositoryDjango
from apps.usuarios.domain.entities import Actor
from apps.usuarios.interfaces.api.permissions import (
    LecturaParaTodosEscrituraAdministradorOSupervisor,
)

from ...domain.exceptions import (
    CambioDeCostoNoPermitidoError,
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaEnUsoError,
    HerramientaNoEncontradaError,
)
from ...infrastructure.repositories import HerramientaRepositoryDjango, HistorialCostoRepositoryDjango
from ...use_cases import gestionar_herramientas as casos
from .serializers import CambioCostoSerializer, HerramientaAltaSerializer, HerramientaSerializer


class HerramientaViewSet(viewsets.ViewSet):
    """
    CRUD de herramientas (HU6). La vista no tiene lógica de negocio:
    valida la forma del request con el serializer, invoca el use_case con
    el repositorio concreto y traduce las excepciones de dominio a HTTP.

    Permisos: todos los autenticados consultan; solo Administrador y
    Supervisor crean, editan y borran (Empleado -> 403). El costo unitario
    (HU7) solo lo cambia el Administrador (regla del caso de uso -> 403).
    """

    permission_classes = [IsAuthenticated, LecturaParaTodosEscrituraAdministradorOSupervisor]
    serializer_class = HerramientaSerializer  # para Swagger (drf-spectacular)
    lookup_value_regex = r"\d+"  # /herramientas/abc/ -> 404, no un int() fallido

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = HerramientaRepositoryDjango()
        self.historial = HistorialCostoRepositoryDjango()
        self.proveedores = ProveedorRepositoryDjango()

    @staticmethod
    def _actor(request) -> Actor:
        usuario = request.user
        return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)

    def _responder(self, herramienta, codigo_http=status.HTTP_200_OK):
        # request en el contexto: la foto se devuelve como URL absoluta.
        return Response(HerramientaSerializer(herramienta, context={"request": self.request}).data, status=codigo_http)

    def _ejecutar(self, caso, *args, **kwargs):
        """Corre el use_case y convierte sus errores de negocio en la
        respuesta HTTP que corresponde."""
        try:
            return caso(self.repo, *args, **kwargs)
        except HerramientaNoEncontradaError:
            raise NotFound("No existe una herramienta con ese id.")
        except CodigoDuplicadoError:
            raise ValidationError({"codigo": ["Ya existe una herramienta con ese código."]})
        except DatosHerramientaInvalidosError as error:
            raise ValidationError({campo: [mensaje] for campo, mensaje in error.errores.items()})
        except CambioDeCostoNoPermitidoError:
            raise PermissionDenied("Solo el Administrador puede cambiar el costo unitario.")

    def list(self, request):
        herramientas = self._ejecutar(casos.listar_herramientas)
        return Response(HerramientaSerializer(herramientas, many=True, context={"request": request}).data)

    def retrieve(self, request, pk=None):
        return self._responder(self._ejecutar(casos.obtener_herramienta, int(pk)))

    @extend_schema(request=HerramientaAltaSerializer)
    def create(self, request):
        # Acepta JSON o multipart; la foto es obligatoria (HerramientaAltaSerializer).
        serializer = HerramientaAltaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)
        imagen = datos.pop("imagen")
        # La herramienta, su foto y su fila de historial de costos, juntas o ninguna.
        with transaction.atomic():
            herramienta = self._ejecutar(
                casos.registrar_herramienta, datos,
                actor=self._actor(request), historial=self.historial, proveedores=self.proveedores,
                imagen=imagen,
            )
        return self._responder(herramienta, status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return self._actualizar(request, pk, parcial=False)

    def partial_update(self, request, pk=None):
        return self._actualizar(request, pk, parcial=True)

    def _actualizar(self, request, pk, parcial: bool):
        serializer = HerramientaSerializer(data=request.data, partial=parcial)
        serializer.is_valid(raise_exception=True)
        # En un PATCH solo se aplican los campos que llegaron de verdad:
        # validated_data de un serializer parcial no incluye los defaults.
        # La foto solo cambia si llegó un archivo nuevo.
        datos = dict(serializer.validated_data)
        imagen = datos.pop("imagen", None)
        with transaction.atomic():
            herramienta = self._ejecutar(
                casos.actualizar_herramienta, int(pk), datos,
                actor=self._actor(request), historial=self.historial, proveedores=self.proveedores,
                imagen=imagen,
            )
        return self._responder(herramienta)

    @extend_schema(responses=CambioCostoSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="historial-costos")
    def historial_costos(self, request, pk=None):
        """HU7: cambios del costo unitario, del más reciente al más antiguo."""
        cambios = self._ejecutar(casos.historial_de_costos, self.historial, int(pk))
        return Response(CambioCostoSerializer(cambios, many=True).data)

    @extend_schema(responses={204: None, 409: None})
    def destroy(self, request, pk=None):
        try:
            self._ejecutar(casos.eliminar_herramienta, int(pk))
        except HerramientaEnUsoError:
            return Response(
                {"detail": "No se puede eliminar: la herramienta tiene movimientos, transferencias o historial de costos."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
