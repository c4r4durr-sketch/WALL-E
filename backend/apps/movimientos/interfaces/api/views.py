from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango
from apps.usuarios.domain.entities import Actor
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from ...domain.exceptions import (
    AjusteNoPermitidoError,
    HerramientaInexistenteError,
    MotivoObligatorioError,
    StockInsuficienteError,
    SucursalInvalidaError,
    SucursalNoPermitidaError,
)
from ...domain.value_objects import TipoMovimiento
from ...infrastructure.repositories import MovimientoRepositoryDjango
from ...use_cases import registrar_movimiento as casos
from .serializers import (
    FiltroMovimientosSerializer,
    FiltroStockSerializer,
    MovimientoSerializer,
    RegistrarAjusteSerializer,
    RegistrarMovimientoSerializer,
    StockEnSucursalSerializer,
)


class MovimientoViewSet(viewsets.ViewSet):
    """
    Movimientos de inventario (HU9): registrar entradas/salidas, historial y
    stock. La vista no tiene lógica de negocio: valida la forma del request,
    invoca el use_case y traduce las excepciones de dominio a HTTP.

    Permisos: todo usuario autenticado (incluido el Empleado, es su trabajo
    diario en el mostrador) consulta y registra entradas/salidas; los
    ajustes (POST ajustes/) solo Administrador/Supervisor. NO hay editar ni borrar
    para nadie (PUT/PATCH/DELETE -> 405): un movimiento es un registro
    auditable; un error se corrige con un movimiento nuevo.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MovimientoSerializer  # para Swagger (drf-spectacular)
    lookup_value_regex = r"\d+"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.movimientos = MovimientoRepositoryDjango()
        self.herramientas = HerramientaRepositoryDjango()
        self.sucursales = SucursalRepositoryDjango()

    @extend_schema(parameters=[FiltroMovimientosSerializer])
    def list(self, request):
        """Historial, del más reciente al más antiguo. Filtros opcionales:
        ?herramienta=<id>&sucursal=<id>."""
        filtro = FiltroMovimientosSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        movimientos = casos.historial(
            self.movimientos,
            herramienta_id=filtro.validated_data.get("herramienta"),
            sucursal_id=filtro.validated_data.get("sucursal"),
        )
        return Response(MovimientoSerializer(movimientos, many=True).data)

    def retrieve(self, request, pk=None):
        movimiento = self.movimientos.obtener_por_id(int(pk))
        if movimiento is None:
            raise NotFound("No existe ese movimiento.")
        return Response(MovimientoSerializer(movimiento).data)

    @staticmethod
    def _actor(request) -> Actor:
        usuario = request.user
        return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)

    def _registrar(self, registrar, operacion: str, *args):
        """Corre un use_case de registro dentro de una transacción y traduce
        sus errores de negocio a HTTP. `operacion` ("la salida", "el
        ajuste") solo personaliza el mensaje de stock insuficiente."""
        try:
            # atomic: el bloqueo de stock (salidas y ajustes negativos) dura
            # hasta que el movimiento queda guardado
            # (ver MovimientoRepository.bloquear_stock).
            with transaction.atomic():
                movimiento = registrar(self.movimientos, self.herramientas, self.sucursales, *args)
        except HerramientaInexistenteError:
            raise ValidationError({"herramienta": ["No existe esa herramienta."]})
        except SucursalInvalidaError:
            raise ValidationError({"sucursal": ["La sucursal no existe o está inactiva."]})
        except SucursalNoPermitidaError:
            raise PermissionDenied("Solo puedes registrar movimientos en tu sucursal.")
        except AjusteNoPermitidoError:
            raise PermissionDenied("Solo un Administrador o Supervisor puede registrar ajustes de stock.")
        except MotivoObligatorioError:
            raise ValidationError({"motivo": ["Indica el motivo del ajuste."]})
        except StockInsuficienteError as error:
            raise ValidationError({
                "cantidad": [
                    f"Stock insuficiente: hay {error.disponible} unidades disponibles en esta "
                    f"sucursal y {operacion} pide {error.solicitado}."
                ]
            })
        return Response(MovimientoSerializer(movimiento).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=RegistrarMovimientoSerializer, responses={201: MovimientoSerializer})
    def create(self, request):
        entrada = RegistrarMovimientoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        es_salida = datos["tipo_movimiento"] == TipoMovimiento.SALIDA.value
        return self._registrar(
            casos.registrar_salida if es_salida else casos.registrar_entrada,
            "la salida",
            self._actor(request), datos["herramienta"], datos["sucursal"],
            datos["tipo_unidad"], datos["cantidad"],
        )

    @extend_schema(request=RegistrarAjusteSerializer, responses={201: MovimientoSerializer})
    @action(detail=False, methods=["post"])
    def ajustes(self, request):
        """POST /api/movimientos/ajustes/ — corrección de stock con motivo
        obligatorio. Solo Administrador/Supervisor (Empleado -> 403)."""
        entrada = RegistrarAjusteSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        return self._registrar(
            casos.registrar_ajuste,
            "el ajuste",
            self._actor(request), datos["herramienta"], datos["sucursal"],
            datos["sentido"] == "POSITIVO", datos["tipo_unidad"], datos["cantidad"], datos["motivo"],
        )

    @extend_schema(parameters=[FiltroStockSerializer], responses=StockEnSucursalSerializer(many=True))
    @action(detail=False, methods=["get"])
    def stock(self, request):
        """GET /api/movimientos/stock/?herramienta=<id>[&sucursal=<id>]
        Stock en unidades (y en cajas completas + sueltas) por sucursal."""
        filtro = FiltroStockSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        try:
            stock = casos.consultar_stock(
                self.movimientos, self.herramientas, self.sucursales,
                herramienta_id=filtro.validated_data["herramienta"],
                sucursal_id=filtro.validated_data.get("sucursal"),
            )
        except HerramientaInexistenteError:
            raise NotFound("No existe esa herramienta.")
        except SucursalInvalidaError:
            raise NotFound("No existe esa sucursal.")
        return Response(StockEnSucursalSerializer(stock, many=True).data)
