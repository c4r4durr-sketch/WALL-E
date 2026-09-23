from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango
from apps.movimientos.domain.exceptions import (
    HerramientaInexistenteError,
    StockInsuficienteError,
    SucursalInvalidaError,
    SucursalNoPermitidaError,
)
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.usuarios.domain.entities import Actor
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from ...domain.exceptions import (
    MismaSucursalError,
    MotivoRechazoObligatorioError,
    ResolucionNoPermitidaError,
    TransferenciaNoEncontradaError,
    TransferenciaYaResueltaError,
)
from ...infrastructure.repositories import TransferenciaRepositoryDjango
from ...use_cases import gestionar_transferencias as casos
from .serializers import (
    FiltroTransferenciasSerializer,
    RechazarTransferenciaSerializer,
    SolicitarTransferenciaSerializer,
    TransferenciaSerializer,
)

_ESTADO_LEGIBLE = {"COMPLETADA": "completada", "RECHAZADA": "rechazada"}


class TransferenciaViewSet(viewsets.ViewSet):
    """
    Transferencias entre sucursales (HU12). La vista no tiene lógica de
    negocio: valida la forma del request, invoca el use_case y traduce las
    excepciones de dominio a HTTP.

      GET  /api/transferencias/[?estado=PENDIENTE]  listado
      POST /api/transferencias/                     solicitar (queda PENDIENTE)
      POST /api/transferencias/{id}/completar/      Admin/Supervisor: mueve el stock
      POST /api/transferencias/{id}/rechazar/       Admin/Supervisor, con motivo

    No hay editar ni borrar (PUT/PATCH/DELETE -> 405): una transferencia
    queda siempre en el historial.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TransferenciaSerializer  # para Swagger (drf-spectacular)
    lookup_value_regex = r"\d+"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transferencias = TransferenciaRepositoryDjango()
        self.movimientos = MovimientoRepositoryDjango()
        self.herramientas = HerramientaRepositoryDjango()
        self.sucursales = SucursalRepositoryDjango()

    @staticmethod
    def _actor(request) -> Actor:
        usuario = request.user
        return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)

    @staticmethod
    def _respuesta(transferencia, codigo=status.HTTP_200_OK):
        return Response(TransferenciaSerializer(transferencia).data, status=codigo)

    @extend_schema(parameters=[FiltroTransferenciasSerializer])
    def list(self, request):
        filtro = FiltroTransferenciasSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        transferencias = casos.listar_transferencias(self.transferencias, filtro.validated_data.get("estado"))
        return Response(TransferenciaSerializer(transferencias, many=True).data)

    def retrieve(self, request, pk=None):
        try:
            return self._respuesta(casos.obtener_transferencia(self.transferencias, int(pk)))
        except TransferenciaNoEncontradaError:
            raise NotFound("No existe esa transferencia.")

    @extend_schema(request=SolicitarTransferenciaSerializer, responses={201: TransferenciaSerializer})
    def create(self, request):
        entrada = SolicitarTransferenciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            transferencia = casos.solicitar_transferencia(
                self.transferencias, self.movimientos, self.herramientas, self.sucursales,
                self._actor(request), datos["herramienta"], datos["sucursal_origen"],
                datos["sucursal_destino"], datos["tipo_unidad"], datos["cantidad"],
            )
        except MismaSucursalError:
            raise ValidationError({"sucursal_destino": ["El destino debe ser una sucursal distinta del origen."]})
        except HerramientaInexistenteError:
            raise ValidationError({"herramienta": ["No existe esa herramienta."]})
        except SucursalInvalidaError:
            raise ValidationError({"sucursal_origen": ["Alguna de las sucursales no existe o está inactiva."]})
        except SucursalNoPermitidaError:
            raise PermissionDenied("Solo puedes solicitar transferencias desde tu sucursal.")
        except StockInsuficienteError as error:
            raise ValidationError({"cantidad": [
                f"Stock insuficiente en origen: hay {error.disponible} unidades disponibles "
                f"y la transferencia pide {error.solicitado}."
            ]})
        return self._respuesta(transferencia, status.HTTP_201_CREATED)

    def _resolver(self, request, pk, ejecutar):
        """Completar y rechazar comparten permisos, bloqueo y errores."""
        try:
            with transaction.atomic():
                transferencia = ejecutar()
        except ResolucionNoPermitidaError:
            raise PermissionDenied("Solo un Administrador o Supervisor puede completar o rechazar transferencias.")
        except TransferenciaNoEncontradaError:
            raise NotFound("No existe esa transferencia.")
        except TransferenciaYaResueltaError as error:
            return Response(
                {"detail": f"La transferencia ya fue {_ESTADO_LEGIBLE.get(error.estado, error.estado.lower())}."},
                status=status.HTTP_409_CONFLICT,
            )
        except StockInsuficienteError as error:
            # El stock cambió desde la solicitud (hubo ventas): no se mueve nada.
            return Response(
                {"detail": f"Ya no hay stock suficiente en origen: hay {error.disponible} unidades "
                           f"y la transferencia pide {error.solicitado}. Se puede rechazar o esperar reposición."},
                status=status.HTTP_409_CONFLICT,
            )
        except SucursalInvalidaError:
            return Response(
                {"detail": "Alguna de las sucursales fue desactivada; no se puede completar."},
                status=status.HTTP_409_CONFLICT,
            )
        except MotivoRechazoObligatorioError:
            raise ValidationError({"motivo": ["Indica el motivo del rechazo."]})
        return self._respuesta(transferencia)

    @extend_schema(request=None, responses=TransferenciaSerializer)
    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        return self._resolver(request, pk, lambda: casos.completar_transferencia(
            self.transferencias, self.movimientos, self.herramientas, self.sucursales,
            self._actor(request), int(pk), ahora=timezone.now(),
        ))

    @extend_schema(request=RechazarTransferenciaSerializer, responses=TransferenciaSerializer)
    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        entrada = RechazarTransferenciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return self._resolver(request, pk, lambda: casos.rechazar_transferencia(
            self.transferencias, self._actor(request), int(pk),
            entrada.validated_data["motivo"], ahora=timezone.now(),
        ))
