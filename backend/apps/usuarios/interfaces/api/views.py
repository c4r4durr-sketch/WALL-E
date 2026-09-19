from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from ...infrastructure.models import Sucursal, Usuario
from .permissions import EsAdministrador
from .serializers import CustomTokenObtainPairSerializer, SucursalSerializer, UsuarioSerializer


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


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuarios, solo para Administrador.

    Nota: por ahora la vista llama directo al ORM vía el serializer
    (patrón estándar de DRF). Cuando exista el use_case de gestión de
    usuarios (ej. crear_empleado, validando sucursal obligatoria), esta
    vista pasará a orquestar ese use_case en vez de usar ModelViewSet
    genérico, para no meter lógica de negocio en la vista.
    """

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, EsAdministrador]
