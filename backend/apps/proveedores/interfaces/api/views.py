from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.usuarios.domain.entities import Actor

from ...domain.exceptions import (
    DatosProveedorInvalidosError,
    NombreProveedorDuplicadoError,
    PermisoDenegadoError,
    ProveedorEnUsoError,
    ProveedorNoEncontradoError,
)
from ...infrastructure.repositories import ProveedorRepositoryDjango
from ...use_cases import gestionar_proveedores as casos
from .serializers import FiltroProveedoresSerializer, ProveedorSerializer


class ProveedorViewSet(viewsets.ViewSet):
    """
    Directorio de proveedores (HU8). La vista no tiene lógica de negocio:
    valida la forma, invoca el caso de uso y traduce sus errores a HTTP.

    Permisos: todos los autenticados consultan; solo el Administrador
    registra, edita o elimina (regla del caso de uso -> 403).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ProveedorSerializer  # para Swagger (drf-spectacular)
    lookup_value_regex = r"\d+"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = ProveedorRepositoryDjango()

    @staticmethod
    def _actor(request) -> Actor:
        usuario = request.user
        return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)

    def _ejecutar(self, caso, *args, **kwargs):
        try:
            return caso(self.repo, *args, **kwargs)
        except ProveedorNoEncontradoError:
            raise NotFound("No existe un proveedor con ese id.")
        except PermisoDenegadoError:
            raise PermissionDenied("Solo el Administrador puede registrar, editar o eliminar proveedores.")
        except NombreProveedorDuplicadoError:
            raise ValidationError({"nombre": ["Ya existe un proveedor con ese nombre."]})
        except DatosProveedorInvalidosError as error:
            raise ValidationError({campo: [mensaje] for campo, mensaje in error.errores.items()})

    @extend_schema(parameters=[FiltroProveedoresSerializer])
    def list(self, request):
        """?buscar=<texto> filtra por nombre; ?activos=true solo los activos."""
        filtro = FiltroProveedoresSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        proveedores = self._ejecutar(
            casos.listar_proveedores,
            buscar=filtro.validated_data["buscar"],
            solo_activos=filtro.validated_data["activos"],
        )
        return Response(ProveedorSerializer(proveedores, many=True).data)

    def retrieve(self, request, pk=None):
        return Response(ProveedorSerializer(self._ejecutar(casos.obtener_proveedor, int(pk))).data)

    def create(self, request):
        serializer = ProveedorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proveedor = self._ejecutar(casos.registrar_proveedor, self._actor(request), serializer.validated_data)
        return Response(ProveedorSerializer(proveedor).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return self._actualizar(request, pk, parcial=False)

    def partial_update(self, request, pk=None):
        return self._actualizar(request, pk, parcial=True)

    def _actualizar(self, request, pk, parcial: bool):
        serializer = ProveedorSerializer(data=request.data, partial=parcial)
        serializer.is_valid(raise_exception=True)
        proveedor = self._ejecutar(
            casos.actualizar_proveedor, self._actor(request), int(pk), serializer.validated_data
        )
        return Response(ProveedorSerializer(proveedor).data)

    @extend_schema(responses={204: None, 409: None})
    def destroy(self, request, pk=None):
        try:
            self._ejecutar(casos.eliminar_proveedor, self._actor(request), int(pk))
        except ProveedorEnUsoError:
            return Response(
                {"detail": "No se puede eliminar: el proveedor tiene herramientas asociadas. Desactívalo en su lugar."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
