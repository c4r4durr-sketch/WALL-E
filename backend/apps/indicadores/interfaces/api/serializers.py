from rest_framework import serializers

# Serializers "planos" (no ModelSerializer): indicadores no tiene modelos
# propios, así que estos serializan los DTOs de domain/entities.py, no un
# modelo ORM.


class ResultadoEOQSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    demanda_anual = serializers.IntegerField(allow_null=True)
    costo_pedido = serializers.FloatField(allow_null=True)
    costo_almacenamiento_unitario = serializers.FloatField(allow_null=True)
    unidades_por_caja = serializers.IntegerField()
    eoq = serializers.FloatField(allow_null=True)
    eoq_ajustado_cajas = serializers.FloatField(allow_null=True)
    demanda_observada = serializers.IntegerField()
    datos_faltantes = serializers.ListField(child=serializers.CharField())


class ResultadoROPSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    demanda_anual = serializers.IntegerField(allow_null=True)
    demanda_diaria_promedio = serializers.FloatField(allow_null=True)
    lead_time_dias = serializers.IntegerField(allow_null=True)
    punto_reorden = serializers.FloatField(allow_null=True)
    stock_total = serializers.IntegerField()
    requiere_reorden = serializers.BooleanField()
    datos_faltantes = serializers.ListField(child=serializers.CharField())


class ClasificacionABCSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    unidades_vendidas = serializers.IntegerField()
    porcentaje = serializers.FloatField()
    porcentaje_acumulado = serializers.FloatField()
    clase = serializers.CharField()


class AlertaReordenSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    stock_total = serializers.IntegerField()
    punto_reorden = serializers.FloatField()
    pedido_sugerido = serializers.FloatField(allow_null=True)
    unidades_por_caja = serializers.IntegerField()


class HerramientaEstancadaSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    sucursal_id = serializers.IntegerField()
    sucursal_nombre = serializers.CharField()
    stock = serializers.IntegerField()
    dias_sin_venta = serializers.IntegerField()
    nunca_vendida = serializers.BooleanField()


class PanelAuditoriaSerializer(serializers.Serializer):
    total_alertas_stock = serializers.IntegerField()
    total_herramientas_estancadas = serializers.IntegerField()
    total_herramientas = serializers.IntegerField()
    total_sucursales_activas = serializers.IntegerField()
    herramientas_sin_datos_rop = serializers.IntegerField()
    dias_para_estancamiento = serializers.IntegerField()
    alertas = AlertaReordenSerializer(many=True)
    estancadas = HerramientaEstancadaSerializer(many=True)
