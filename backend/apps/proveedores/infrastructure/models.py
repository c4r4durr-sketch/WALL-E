from django.db import models


class Proveedor(models.Model):
    """HU8: directorio de proveedores. Las reglas (nombre único sin
    mayúsculas, teléfono válido, no eliminar con herramientas asociadas)
    las aplica use_cases/gestionar_proveedores.py; acá solo persistencia."""

    id = models.BigAutoField(primary_key=True, db_column="cod_proveedor")
    nombre = models.CharField(max_length=150, unique=True, db_column="nombre_proveedor")
    telefono = models.CharField(max_length=30, db_column="telefono_proveedor")
    email = models.EmailField(blank=True, db_column="email_proveedor")
    activo = models.BooleanField(default=True, db_column="estado_proveedor")
    creado_en = models.DateTimeField(auto_now_add=True, db_column="fecha_registro_proveedor")
    actualizado_en = models.DateTimeField(auto_now=True, db_column="fecha_actualizacion_proveedor")

    class Meta:
        app_label = "proveedores"
        db_table = "proveedores"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self) -> str:
        return self.nombre
