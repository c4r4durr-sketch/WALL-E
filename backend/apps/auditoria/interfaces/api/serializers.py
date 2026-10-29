from rest_framework import serializers

from ...domain.value_objects import AccionAuditoria, OrigenHistorial

# Serializers "planos": validan la forma de los filtros y serializan las
# entidades del dominio de auditoría (solo lectura).


class FiltroHistorialSerializer(serializers.Serializer):
    desde = serializers.DateField(required=False)
    hasta = serializers.DateField(required=False)
    usuario = serializers.IntegerField(min_value=1, required=False)
    tabla = serializers.CharField(max_length=100, required=False)
    accion = serializers.ChoiceField(choices=[a.value for a in AccionAuditoria], required=False)
    origen = serializers.ChoiceField(choices=[o.value for o in OrigenHistorial], required=False)
    pagina = serializers.IntegerField(min_value=1, required=False, default=1)
    tamano = serializers.IntegerField(min_value=1, max_value=100, required=False, default=25)


class RegistroHistorialSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fecha = serializers.DateTimeField()
    tabla = serializers.CharField()
    tabla_nombre = serializers.CharField()
    registro_id = serializers.CharField()
    accion = serializers.CharField(source="accion.value")
    usuario_id = serializers.IntegerField(allow_null=True)
    usuario = serializers.CharField(source="usuario_username")
    datos_anteriores = serializers.JSONField(allow_null=True)
    datos_nuevos = serializers.JSONField(allow_null=True)
    campos_cambiados = serializers.ListField(child=serializers.CharField())


class PaginaHistorialSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    pagina = serializers.IntegerField()
    paginas = serializers.IntegerField()
    tamano = serializers.IntegerField()
    resultados = RegistroHistorialSerializer(many=True)


class OpcionFiltroSerializer(serializers.Serializer):
    valor = serializers.CharField()
    texto = serializers.CharField()


class OpcionesHistorialSerializer(serializers.Serializer):
    tablas = OpcionFiltroSerializer(many=True)
    usuarios = OpcionFiltroSerializer(many=True)
    acciones = OpcionFiltroSerializer(many=True)
    origenes = OpcionFiltroSerializer(many=True)
