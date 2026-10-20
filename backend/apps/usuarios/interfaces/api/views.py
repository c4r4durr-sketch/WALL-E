from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from ...domain.entities import Actor
from ...domain.exceptions import (
    DatosUsuarioInvalidosError,
    OperacionNoPermitidaError,
    PermisoDenegadoError,
    UsernameDuplicadoError,
    UsuarioNoEncontradoError,
)
from ...infrastructure.models import Sucursal
from ...infrastructure.repositories import (
    SucursalRepositoryDjango,
    UsuarioRepositoryDjango,
    ValidadorPasswordDjango,
)
from ...use_cases import gestionar_usuarios as casos
from .permissions import EsAdministrador
from .serializers import (
    CustomTokenObtainPairSerializer,
    RestablecerPasswordSerializer,
    SucursalSerializer,
    UsuarioSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Login JWT. Reemplaza la vista default de SimpleJWT solo para usar
    CustomTokenObtainPairSerializer (agrega rol/sucursal al token)."""

    serializer_class = CustomTokenObtainPairSerializer


class SucursalViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura: el frontend la usa para poblar el <select> de sucursal
    al crear un usuario (HU5). Crear/editar sucursales no es parte del
    alcance actual."""

    queryset = Sucursal.objects.filter(activa=True)
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticated]


class UsuarioViewSet(viewsets.ViewSet):
    """
    Cuentas de usuario (HU3/HU4/HU5), solo Administrador. La vista no tiene
    lógica de negocio: valida la forma con el serializer, llama al use case
    con los repositorios concretos y traduce sus excepciones a HTTP.

    No hay DELETE (405): una cuenta queda referenciada por movimientos,
    transferencias y el historial; se desactiva con is_active = false.
    """

    permission_classes = [IsAuthenticated, EsAdministrador]
    serializer_class = UsuarioSerializer  # para Swagger (drf-spectacular)
    lookup_value_regex = r"\d+"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.usuarios = UsuarioRepositoryDjango()
        self.sucursales = SucursalRepositoryDjango()
        self.validador = ValidadorPasswordDjango()

    @staticmethod
    def _actor(request) -> Actor:
        usuario = request.user
        return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)

    @staticmethod
    def _ejecutar(caso, *args):
        """Corre el use case y convierte sus errores de negocio en HTTP."""
        try:
            return caso(*args)
        except UsuarioNoEncontradoError:
            raise NotFound("No existe un usuario con ese id.")
        except PermisoDenegadoError as error:
            raise PermissionDenied(str(error))
        except UsernameDuplicadoError:
            raise ValidationError({"username": ["Ya existe una cuenta con ese nombre de usuario."]})
        except DatosUsuarioInvalidosError as error:
            raise ValidationError(error.errores)
        except OperacionNoPermitidaError as error:
            raise Conflicto(str(error))

    def list(self, request):
        usuarios = self._ejecutar(casos.listar_usuarios, self._actor(request), self.usuarios)
        return Response(UsuarioSerializer(usuarios, many=True).data)

    def retrieve(self, request, pk=None):
        usuario = self._ejecutar(casos.obtener_usuario, self._actor(request), self.usuarios, int(pk))
        return Response(UsuarioSerializer(usuario).data)

    def create(self, request):
        serializer = UsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)
        password = datos.pop("password", None)
        usuario = self._ejecutar(
            casos.crear_usuario, self._actor(request), self.usuarios, self.sucursales,
            self.validador, datos, password,
        )
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return self._actualizar(request, pk, parcial=False)

    def partial_update(self, request, pk=None):
        return self._actualizar(request, pk, parcial=True)

    def _actualizar(self, request, pk, parcial: bool):
        serializer = UsuarioSerializer(data=request.data, partial=parcial)
        serializer.is_valid(raise_exception=True)
        cambios = dict(serializer.validated_data)
        password = cambios.pop("password", None)
        # Datos y contraseña se guardan juntos o ninguno.
        with transaction.atomic():
            usuario = self._ejecutar(
                casos.actualizar_usuario, self._actor(request), self.usuarios, self.sucursales,
                self.validador, int(pk), cambios, password,
            )
        return Response(UsuarioSerializer(usuario).data)

    @extend_schema(request=RestablecerPasswordSerializer, responses={204: None})
    @action(detail=True, methods=["post"], url_path="restablecer-password")
    def restablecer_password(self, request, pk=None):
        """HU3: el Administrador asigna una contraseña nueva a la cuenta."""
        serializer = RestablecerPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._ejecutar(
            casos.restablecer_password, self._actor(request), self.usuarios, self.validador,
            int(pk), serializer.validated_data["password"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class Conflicto(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "La operación no está permitida en el estado actual."
    default_code = "conflicto"
