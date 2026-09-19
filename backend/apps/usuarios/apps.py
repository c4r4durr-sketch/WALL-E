from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """
    App de usuarios: autenticación, roles (Administrador/Supervisor/Empleado)
    y sucursales (una sucursal fija por empleado).

    Se agrupa como bounded context propio porque es transversal: catálogo,
    movimientos, transferencias e indicadores dependen de "quién hace la
    acción" y "en qué sucursal", pero ninguno de ellos es dueño de esa
    información.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.usuarios"
    label = "usuarios"
