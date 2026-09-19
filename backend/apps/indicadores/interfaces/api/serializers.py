from rest_framework import serializers

# Serializers "planos" (no ModelSerializer): indicadores no tiene modelos
# propios, así que estos serializan los DTOs de domain/entities.py, no un
# modelo ORM.


class ResultadoEOQSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    demanda_anual = serializers.IntegerField()
    costo_pedido = serializers.FloatField()
    costo_almacenamiento_unitario = serializers.FloatField()
    eoq = serializers.FloatField()


class ResultadoROPSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    demanda_diaria_promedio = serializers.FloatField()
    lead_time_dias = serializers.IntegerField()
    punto_reorden = serializers.FloatField()


class ClasificacionABCSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    valor_consumo = serializers.FloatField()
    porcentaje_acumulado = serializers.FloatField()
    clase = serializers.CharField()
