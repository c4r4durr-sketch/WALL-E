from rest_framework import serializers

from ...infrastructure.models import Herramienta


class HerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Herramienta
        fields = [
            "id",
            "codigo",
            "nombre",
            "modelo",
            "unidades_por_caja",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]
