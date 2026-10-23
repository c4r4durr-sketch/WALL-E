from typing import Optional

from django.core.files.storage import default_storage
from rest_framework import serializers
from rest_framework.fields import SkipField

from ...domain.entities import ImagenProducto


class ArchivoDeImagenOpcional(serializers.ImageField):
    """ImageField que ignora (SkipField) lo que no es un archivo: así un
    PUT que reenvía los datos tal como los devolvió la API no falla por la
    URL de la foto."""

    def validate_empty_values(self, data):
        if data is None or isinstance(data, str):
            raise SkipField()
        return super().validate_empty_values(data)


def _a_imagen_producto(archivo) -> ImagenProducto:
    # ImageField ya abrió el archivo con Pillow (archivo.image): el formato
    # sale del contenido real, no de la extensión. Las reglas (formatos
    # permitidos, tamaño) las aplica el caso de uso.
    return ImagenProducto(
        nombre=archivo.name, formato=archivo.image.format, tamano_bytes=archivo.size, contenido=archivo
    )


def _url_absoluta(request, ruta: Optional[str]) -> Optional[str]:
    if not ruta:
        return None
    url = default_storage.url(ruta)
    return request.build_absolute_uri(url) if request is not None else url


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
    # Foto: se recibe como archivo (multipart) y se devuelve como URL
    # absoluta (ver to_representation). En la edición es opcional y un
    # texto o null (la URL que devolvió la API, o un campo vacío del
    # formulario) significan "no cambiar la foto".
    imagen = ArchivoDeImagenOpcional(write_only=True, required=False)

    def validate_imagen(self, archivo) -> ImagenProducto:
        return _a_imagen_producto(archivo)

    def to_representation(self, herramienta):
        datos = super().to_representation(herramienta)
        datos["imagen"] = _url_absoluta(self.context.get("request"), herramienta.imagen)
        return datos


class HerramientaAltaSerializer(HerramientaSerializer):
    """Alta: igual que la edición, pero la foto es obligatoria."""

    imagen = serializers.ImageField(
        write_only=True,
        error_messages={
            "required": "La foto del producto es obligatoria.",
            "invalid": "La foto del producto es obligatoria.",
        },
    )


class CambioCostoSerializer(serializers.Serializer):
    """HU7: una fila del historial de costos (solo lectura)."""

    id = serializers.IntegerField()
    costo_anterior = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True, coerce_to_string=False)
    costo_nuevo = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    usuario = serializers.CharField(source="usuario_username")
    fecha = serializers.DateTimeField()
