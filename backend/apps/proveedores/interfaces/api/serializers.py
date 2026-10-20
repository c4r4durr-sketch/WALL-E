from rest_framework import serializers


class ProveedorSerializer(serializers.Serializer):
    """Serializer "plano": solo valida la FORMA de los datos y serializa
    la entidad de dominio. Las reglas (nombre único, teléfono válido,
    no eliminar con herramientas) las aplica el caso de uso."""

    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(max_length=150)
    telefono = serializers.CharField(max_length=30)
    email = serializers.CharField(max_length=254, required=False, allow_blank=True, default="")
    activo = serializers.BooleanField(required=False, default=True)
    cantidad_herramientas = serializers.IntegerField(read_only=True)
    creado_en = serializers.DateTimeField(read_only=True)
    actualizado_en = serializers.DateTimeField(read_only=True)


class FiltroProveedoresSerializer(serializers.Serializer):
    buscar = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    activos = serializers.BooleanField(required=False, default=False)
