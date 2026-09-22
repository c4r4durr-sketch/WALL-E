from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    """
    App de auditoría (HU13): historial oculto de quién creó, editó o borró
    un registro y cuándo.

    Reemplaza al trigger SQL fn_registrar_historial del script descartado.
    En vez de un trigger de base de datos, se usan signals de Django
    (post_save / post_delete): así el historial queda en una tabla
    gestionada por el ORM y migraciones como el resto del esquema, y el
    autor del cambio se toma del usuario autenticado del request.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auditoria"
    label = "auditoria"

    def ready(self):
        # Importar el módulo conecta los receivers de los signals.
        from .infrastructure import signals  # noqa: F401
