from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from ..domain.value_objects import AccionAuditoria


class HistorialModificacion(models.Model):
    """
    HU13: una fila por cada INSERT/UPDATE/DELETE de un modelo auditado.

    registro_id es texto (y no una FK) porque apunta a filas de tablas
    distintas y debe sobrevivir aunque el registro original se borre.
    usuario_username guarda una copia del nombre por la misma razón: si el
    usuario autor se elimina, la FK queda en NULL pero el historial sigue
    diciendo quién fue.
    """

    id = models.BigAutoField(primary_key=True, db_column="cod_historial")
    tabla_afectada = models.CharField(max_length=100, db_column="tabla_historial")
    registro_id = models.CharField(max_length=64, db_column="registro_historial")
    accion = models.CharField(
        max_length=10,
        choices=[(a.value, a.value.title()) for a in AccionAuditoria],
        db_column="accion_historial",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        db_column="cod_usuario",
    )
    usuario_username = models.CharField(max_length=150, blank=True, db_column="nombre_usuario_historial")
    datos_anteriores = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder, db_column="datos_anteriores_historial"
    )
    datos_nuevos = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder, db_column="datos_nuevos_historial"
    )
    fecha = models.DateTimeField(auto_now_add=True, db_column="fecha_historial")

    class Meta:
        app_label = "auditoria"
        db_table = "historial_modificaciones"
        verbose_name = "Historial de modificación"
        verbose_name_plural = "Historial de modificaciones"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["tabla_afectada", "registro_id"], name="historial_tabla_registro_idx")
        ]

    def __str__(self) -> str:
        return f"{self.accion} {self.tabla_afectada}#{self.registro_id}"
