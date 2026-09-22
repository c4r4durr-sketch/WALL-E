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


class Sucursal(models.Model):
    """
    Las 2 sucursales de la importadora. La cantidad exacta (2) es una regla
    de negocio del dominio, no una restricción de este modelo: acá solo se
    modela "una sucursal", sin límite fijo en la base de datos.
    """

    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        app_label = "usuarios"
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

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default=Rol.EMPLEADO.value)
    # Obligatorio para SUPERVISOR y EMPLEADO. Se deja nullable a nivel de BD
    # porque esa validación condicional es una regla de negocio: vive en
    # domain/reglas.py y la aplica UsuarioSerializer.validate, no una
    # constraint de base de datos.
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    class Meta:
        app_label = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        return f"{self.username} ({self.rol})"
