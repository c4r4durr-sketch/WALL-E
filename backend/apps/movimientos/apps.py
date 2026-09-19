from django.apps import AppConfig


class MovimientosConfig(AppConfig):
    """
    App de movimientos: entradas y salidas de inventario, diferenciando
    UNIDAD suelta de CAJA por mayor. El stock por sucursal NO se guarda
    como campo aparte: se deriva sumando/restando movimientos (evita que
    "stock guardado" y "stock real" se desincronicen). Ese cálculo vive
    como use_case puro, no en el modelo.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.movimientos"
    label = "movimientos"
