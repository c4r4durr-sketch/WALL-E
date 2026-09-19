from rest_framework import serializers

from ...infrastructure.models import Movimiento


class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = [
            "id",
            "herramienta",
            "sucursal",
            "usuario",
            "tipo_movimiento",
            "tipo_unidad",
            "cantidad",
            "creado_en",
        ]
        read_only_fields = ["id", "usuario", "creado_en"]
