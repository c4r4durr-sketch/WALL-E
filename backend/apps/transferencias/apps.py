from django.apps import AppConfig


class TransferenciasConfig(AppConfig):
    """
    App de transferencias entre las 2 sucursales. Es su propio bounded
    context (y no parte de movimientos) porque conceptualmente una
    transferencia es UNA operación con dos efectos (salida en origen,
    entrada en destino) más una validación propia (stock en origen), no un
    movimiento simple más.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.transferencias"
    label = "transferencias"
