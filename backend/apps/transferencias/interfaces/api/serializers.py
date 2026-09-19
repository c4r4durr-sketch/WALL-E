from rest_framework import serializers

from ...infrastructure.models import Transferencia


class TransferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transferencia
        fields = [
            "id",
            "herramienta",
            "sucursal_origen",
            "sucursal_destino",
            "usuario",
            "cantidad",
            "tipo_unidad",
            "estado",
            "creado_en",
        ]
        read_only_fields = ["id", "usuario", "estado", "creado_en"]
