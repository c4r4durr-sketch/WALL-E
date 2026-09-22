from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.usuarios.interfaces.api.permissions import (
    LecturaParaTodosEscrituraAdministradorOSupervisor,
)

from ...domain.exceptions import (
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaEnUsoError,
    HerramientaNoEncontradaError,
)
from ...infrastructure.repositories import HerramientaRepositoryDjango
from ...use_cases import gestionar_herramientas as casos
from .serializers import HerramientaSerializer


class HerramientaViewSet(viewsets.ViewSet):
    """
    CRUD de herramientas (HU6). La vista no tiene lógica de negocio:
    valida la forma del request con el serializer, invoca el use_case con
    el repositorio concreto y traduce las excepciones de dominio a HTTP.

    Permisos: todos los autenticados consultan; solo Administrador y
    Supervisor crean, editan y borran (Empleado -> 403).
    """

    permission_classes = [IsAuthenticated, LecturaParaTodosEscrituraAdministradorOSupervisor]
    serializer_class = HerramientaSerializer  # para Swagger (drf-spectacular)
    lookup_value_regex = r"\d+"  # /herramientas/abc/ -> 404, no un int() fallido

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = HerramientaRepositoryDjango()

    def _responder(self, herramienta, codigo_http=status.HTTP_200_OK):
        return Response(HerramientaSerializer(herramienta).data, status=codigo_http)

    def _ejecutar(self, caso, *args):
        """Corre el use_case y convierte sus errores de negocio en la
        respuesta HTTP que corresponde."""
        try:
            return caso(self.repo, *args)
        except HerramientaNoEncontradaError:
            raise NotFound("No existe una herramienta con ese id.")
        except CodigoDuplicadoError:
            raise ValidationError({"codigo": ["Ya existe una herramienta con ese código."]})
        except DatosHerramientaInvalidosError as error:
            raise ValidationError({campo: [mensaje] for campo, mensaje in error.errores.items()})

    def list(self, request):
        herramientas = self._ejecutar(casos.listar_herramientas)
        return Response(HerramientaSerializer(herramientas, many=True).data)

    def retrieve(self, request, pk=None):
        return self._responder(self._ejecutar(casos.obtener_herramienta, int(pk)))

    def create(self, request):
        serializer = HerramientaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        herramienta = self._ejecutar(casos.registrar_herramienta, serializer.validated_data)
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
        herramienta = self._ejecutar(casos.actualizar_herramienta, int(pk), serializer.validated_data)
        return self._responder(herramienta)

    @extend_schema(responses={204: None, 409: None})
    def destroy(self, request, pk=None):
        try:
            self._ejecutar(casos.eliminar_herramienta, int(pk))
        except HerramientaEnUsoError:
            return Response(
                {"detail": "No se puede eliminar: la herramienta tiene movimientos o transferencias registrados."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
