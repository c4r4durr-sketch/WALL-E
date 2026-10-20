from rest_framework import serializers


class HerramientaSerializer(serializers.Serializer):
    """
    Serializer "plano" (no ModelSerializer): solo valida la FORMA de los
    datos (tipos, largos, rangos) y serializa la entidad de dominio que
    devuelven los use_cases. Las reglas de negocio (código único, etc.)
    las aplica use_cases/gestionar_herramientas.py, no este serializer:
    un ModelSerializer agregaría su propio validador de unicidad contra
    el ORM y la regla quedaría repetida en dos capas.
    """

    id = serializers.IntegerField(read_only=True)
    codigo = serializers.CharField(max_length=30)
    nombre = serializers.CharField(max_length=150)
    modelo = serializers.CharField(max_length=100, allow_blank=True, required=False, default="")
    unidades_por_caja = serializers.IntegerField(min_value=1, required=False, default=1)
    demanda_anual = serializers.IntegerField(min_value=0, required=False, allow_null=True, default=None)
    # coerce_to_string=False: los costos viajan como número en el JSON (DRF
    # los manda como texto por defecto), así el frontend no tiene que
    # convertirlos antes de mostrarlos o calcular.
    costo_pedido = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        required=False, allow_null=True, default=None, coerce_to_string=False,
    )
    costo_almacenamiento_unitario = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        required=False, allow_null=True, default=None, coerce_to_string=False,
    )
    tiempo_entrega_dias = serializers.IntegerField(min_value=0, required=False, allow_null=True, default=None)
    # HU7. "Mayor que cero" y "solo el Administrador lo cambia" son reglas
    # del caso de uso; acá solo la forma.
    costo_unitario = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        required=False, allow_null=True, default=None, coerce_to_string=False,
    )
    # HU8: id del proveedor (null = sin proveedor); que exista y esté
    # activo lo valida el caso de uso.
    proveedor = serializers.IntegerField(
        source="proveedor_id", min_value=1, required=False, allow_null=True, default=None
    )
    proveedor_nombre = serializers.CharField(read_only=True, allow_null=True)
    creado_en = serializers.DateTimeField(read_only=True)
    actualizado_en = serializers.DateTimeField(read_only=True)


class CambioCostoSerializer(serializers.Serializer):
    """HU7: una fila del historial de costos (solo lectura)."""

    id = serializers.IntegerField()
    costo_anterior = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True, coerce_to_string=False)
    costo_nuevo = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    usuario = serializers.CharField(source="usuario_username")
    fecha = serializers.DateTimeField()
