from rest_framework import serializers

from ...infrastructure.models import Herramienta


class HerramientaSerializer(serializers.ModelSerializer):
    # coerce_to_string=False: los costos viajan como número en el JSON (DRF
    # los manda como texto por defecto), así el frontend no tiene que
    # convertirlos antes de mostrarlos o calcular.
    costo_pedido = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        required=False, allow_null=True, coerce_to_string=False,
    )
    costo_almacenamiento_unitario = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        required=False, allow_null=True, coerce_to_string=False,
    )

    class Meta:
        model = Herramienta
        fields = [
            "id",
            "codigo",
            "nombre",
            "modelo",
            "unidades_por_caja",
            "demanda_anual",
            "costo_pedido",
            "costo_almacenamiento_unitario",
            "tiempo_entrega_dias",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]
