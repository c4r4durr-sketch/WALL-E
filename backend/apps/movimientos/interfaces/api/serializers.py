from rest_framework import serializers

from ...domain.value_objects import TipoMovimiento, TipoUnidad

# Serializers "planos": validan la forma del request y serializan las
# entidades/DTOs de dominio. Las reglas (stock, conversión, sucursal del
# empleado) las aplican los use_cases.


class RegistrarMovimientoSerializer(serializers.Serializer):
    """Operación normal del mostrador: solo ENTRADA o SALIDA. Los ajustes
    van por su propio endpoint (RegistrarAjusteSerializer)."""

    herramienta = serializers.IntegerField(min_value=1)
    sucursal = serializers.IntegerField(min_value=1)
    tipo_movimiento = serializers.ChoiceField(
        choices=[TipoMovimiento.ENTRADA.value, TipoMovimiento.SALIDA.value]
    )
    tipo_unidad = serializers.ChoiceField(choices=[t.value for t in TipoUnidad])
    cantidad = serializers.IntegerField(min_value=1)


class RegistrarAjusteSerializer(serializers.Serializer):
    """Corrección de stock (solo Administrador/Supervisor). `sentido`
    POSITIVO suma unidades, NEGATIVO las resta."""

    herramienta = serializers.IntegerField(min_value=1)
    sucursal = serializers.IntegerField(min_value=1)
    sentido = serializers.ChoiceField(choices=["POSITIVO", "NEGATIVO"])
    tipo_unidad = serializers.ChoiceField(choices=[t.value for t in TipoUnidad])
    cantidad = serializers.IntegerField(min_value=1)
    # allow_blank: el "obligatorio" lo decide el use_case (también rechaza
    # un motivo de puros espacios), con un único mensaje de negocio.
    motivo = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")


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
    motivo = serializers.CharField()
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
