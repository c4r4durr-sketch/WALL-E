"""
Modelos ORM (detalle de infraestructura).

Estos modelos son deliberadamente "anémicos": solo persistencia, sin
métodos de negocio. Las reglas de negocio viven en domain/ y use_cases/;
aquí solo se traduce eso a tablas de PostgreSQL.

app_label se fija explícito a "usuarios" para que quede documentado, aunque
Django ya lo infiere solo a partir de apps.py (AppConfig.name = "apps.usuarios")
aunque el archivo real esté anidado en infrastructure/.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from ..domain.value_objects import Rol


def _campo_heredado(nombre: str, columna: str):
    """
    Copia exacta de un campo de AbstractUser, cambiando solo su columna en la
    base. Así se aplica la convención de nombres sin reescribir a mano (y sin
    desincronizar) validadores, unique, help_text, etc. de Django.
    """
    campo = AbstractUser._meta.get_field(nombre).clone()
    campo.db_column = columna
    return campo


class Sucursal(models.Model):
    """
    Las 2 sucursales de la importadora. La cantidad exacta (2) es una regla
    de negocio del dominio, no una restricción de este modelo: acá solo se
    modela "una sucursal", sin límite fijo en la base de datos.
    """

    id = models.BigAutoField(primary_key=True, db_column="cod_sucursal")
    nombre = models.CharField(max_length=100, db_column="nombre_sucursal")
    direccion = models.CharField(max_length=255, blank=True, db_column="direccion_sucursal")
    activa = models.BooleanField(default=True, db_column="estado_sucursal")

    class Meta:
        app_label = "usuarios"
        db_table = "sucursales"
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    def __str__(self) -> str:
        return self.nombre


class Usuario(AbstractUser):
    """
    Usuario custom (AUTH_USER_MODEL = 'usuarios.Usuario') para poder agregar
    rol y sucursal desde el día uno. Cambiar el modelo de usuario después de
    la primera migración es doloroso en Django, por eso se define custom
    aunque todavía no tenga lógica adicional.
    """

    ROL_CHOICES = [(rol.value, rol.value.title()) for rol in Rol]

    id = models.BigAutoField(primary_key=True, db_column="cod_usuario")
    # Campos de AbstractUser con columna renombrada. is_staff, is_superuser,
    # groups y user_permissions quedan con su nombre de Django.
    username = _campo_heredado("username", "nombre_usuario")
    password = _campo_heredado("password", "contrasena_usuario")
    first_name = _campo_heredado("first_name", "nombres_usuario")
    last_name = _campo_heredado("last_name", "apellidos_usuario")
    email = _campo_heredado("email", "email_usuario")
    is_active = _campo_heredado("is_active", "estado_usuario")
    date_joined = _campo_heredado("date_joined", "fecha_registro_usuario")
    last_login = _campo_heredado("last_login", "fecha_ultimo_acceso_usuario")

    rol = models.CharField(
        max_length=20, choices=ROL_CHOICES, default=Rol.EMPLEADO.value, db_column="rol_usuario"
    )
    # Obligatorio para SUPERVISOR y EMPLEADO. Se deja nullable a nivel de BD
    # porque esa validación condicional es una regla de negocio: vive en
    # domain/reglas.py y la aplica use_cases/gestionar_usuarios.py, no una
    # constraint de base de datos.
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        db_column="cod_sucursal",
    )

    class Meta:
        app_label = "usuarios"
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        return f"{self.username} ({self.rol})"
