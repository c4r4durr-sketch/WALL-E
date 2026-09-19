from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ...infrastructure.models import Transferencia
from .serializers import TransferenciaSerializer


class TransferenciaViewSet(viewsets.ModelViewSet):
    """
    Esqueleto CRUD directo sobre el ORM (sin la validación de stock
    todavía). Igual que en movimientos: cuando exista el use_case
    crear_transferencia, `create()` lo va a invocar en vez de guardar
    directo, para que la validación de stock en origen viva en una sola
    parte del sistema.
    """

    queryset = Transferencia.objects.all()
    serializer_class = TransferenciaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
