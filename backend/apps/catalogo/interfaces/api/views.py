from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ...infrastructure.models import Herramienta
from .serializers import HerramientaSerializer


class HerramientaViewSet(viewsets.ModelViewSet):
    """
    CRUD estándar de DRF por ahora (ModelViewSet directo sobre el ORM).

    Cuando el catálogo tenga reglas propias (ej. validar código único con
    mensaje de negocio, o impedir borrar una herramienta con movimientos),
    esas reglas van en use_cases/ y esta vista pasa a invocarlas, en vez de
    seguir usando el queryset directo.
    """

    queryset = Herramienta.objects.all()
    serializer_class = HerramientaSerializer
    permission_classes = [IsAuthenticated]
