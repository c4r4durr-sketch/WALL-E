from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    """
    App de catálogo: el maestro de herramientas (código, nombre, modelo) y
    su factor de conversión caja->unidad.

    El factor de conversión vive acá (no en movimientos) porque es un
    atributo propio del producto ("esta herramienta viene en cajas de 12"),
    no del movimiento puntual que la usa.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogo"
    label = "catalogo"
