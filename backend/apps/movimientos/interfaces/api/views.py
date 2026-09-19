from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ...infrastructure.models import Movimiento
from .serializers import MovimientoSerializer


class MovimientoViewSet(viewsets.ModelViewSet):
    """
    Esqueleto CRUD directo sobre el ORM (sin reglas de negocio todavía).

    Importante para la sustentación: cuando se implemente, `create()` NO
    va a llamar a `serializer.save()` a secas. Va a invocar el use_case
    registrar_entrada/registrar_salida (con la conversión CAJA->UNIDAD y,
    para salidas, la validación de stock disponible), y recién con el
    resultado de ese use_case arma la respuesta. Así la vista sigue sin
    contener lógica de negocio, solo la orquesta.
    """

    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
