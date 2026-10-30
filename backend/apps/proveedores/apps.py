from django.apps import AppConfig


class ProveedoresConfig(AppConfig):
    """
    App de proveedores (HU8): directorio de contactos de los proveedores de
    la importadora. Cada herramienta del catálogo puede indicar a qué
    proveedor se le compra; el tiempo de entrega (HU16) sigue siendo un
    dato de la herramienta.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.proveedores"
    label = "proveedores"
