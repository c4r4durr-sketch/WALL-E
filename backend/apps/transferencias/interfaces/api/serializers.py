from rest_framework import serializers

from apps.movimientos.domain.value_objects import TipoUnidad

from ...domain.value_objects import EstadoTransferencia

# Serializers "planos": validan la forma del request y serializan la
# entidad de dominio. Las reglas (stock, sucursales, quién resuelve) las
# aplican los use_cases.


class SolicitarTransferenciaSerializer(serializers.Serializer):
    herramienta = serializers.IntegerField(min_value=1)
    sucursal_origen = serializers.IntegerField(min_value=1)
    sucursal_destino = serializers.IntegerField(min_value=1)
    tipo_unidad = serializers.ChoiceField(choices=[t.value for t in TipoUnidad])
    cantidad = serializers.IntegerField(min_value=1)


class RechazarTransferenciaSerializer(serializers.Serializer):
    # allow_blank: el "obligatorio" lo decide el use_case (también rechaza
    # un motivo de puros espacios), con un único mensaje de negocio.
    motivo = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")


class FiltroTransferenciasSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=[e.value for e in EstadoTransferencia], required=False)


class TransferenciaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    herramienta = serializers.IntegerField(source="herramienta_id")
    sucursal_origen = serializers.IntegerField(source="sucursal_origen_id")
    sucursal_destino = serializers.IntegerField(source="sucursal_destino_id")
    usuario = serializers.IntegerField(source="usuario_id")
    usuario_username = serializers.CharField()
    cantidad = serializers.IntegerField()
    tipo_unidad = serializers.CharField(source="tipo_unidad.value")
    cantidad_unidades = serializers.IntegerField()
    estado = serializers.CharField(source="estado.value")
    creado_en = serializers.DateTimeField()
    resuelto_por = serializers.IntegerField(source="resuelto_por_id", allow_null=True)
    resuelto_por_username = serializers.CharField(allow_null=True)
    resuelto_en = serializers.DateTimeField(allow_null=True)
    motivo_rechazo = serializers.CharField()
    movimiento_salida = serializers.IntegerField(source="movimiento_salida_id", allow_null=True)
    movimiento_entrada = serializers.IntegerField(source="movimiento_entrada_id", allow_null=True)
