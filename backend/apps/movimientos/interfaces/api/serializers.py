from rest_framework import serializers

from ...domain.value_objects import TipoMovimiento, TipoUnidad

# Serializers "planos": validan la forma del request y serializan las
# entidades/DTOs de dominio. Las reglas (stock, conversión, sucursal del
# empleado) las aplican los use_cases.


class RegistrarMovimientoSerializer(serializers.Serializer):
    herramienta = serializers.IntegerField(min_value=1)
    sucursal = serializers.IntegerField(min_value=1)
    tipo_movimiento = serializers.ChoiceField(choices=[t.value for t in TipoMovimiento])
    tipo_unidad = serializers.ChoiceField(choices=[t.value for t in TipoUnidad])
    cantidad = serializers.IntegerField(min_value=1)


class MovimientoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    herramienta = serializers.IntegerField(source="herramienta_id")
    sucursal = serializers.IntegerField(source="sucursal_id")
    usuario = serializers.IntegerField(source="usuario_id")
    usuario_username = serializers.CharField()
    tipo_movimiento = serializers.CharField(source="tipo_movimiento.value")
    tipo_unidad = serializers.CharField(source="tipo_unidad.value")
    cantidad = serializers.IntegerField()
    cantidad_unidades = serializers.IntegerField()
    creado_en = serializers.DateTimeField()


class FiltroMovimientosSerializer(serializers.Serializer):
    herramienta = serializers.IntegerField(min_value=1, required=False)
    sucursal = serializers.IntegerField(min_value=1, required=False)


class FiltroStockSerializer(serializers.Serializer):
    herramienta = serializers.IntegerField(min_value=1)
    sucursal = serializers.IntegerField(min_value=1, required=False)


class StockEnSucursalSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    sucursal_id = serializers.IntegerField()
    sucursal_nombre = serializers.CharField()
    unidades = serializers.IntegerField()
    cajas_completas = serializers.IntegerField()
    unidades_sueltas = serializers.IntegerField()
