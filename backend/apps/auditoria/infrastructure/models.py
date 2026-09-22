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

    tabla_afectada = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=64)
    accion = models.CharField(
        max_length=10, choices=[(a.value, a.value.title()) for a in AccionAuditoria]
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    usuario_username = models.CharField(max_length=150, blank=True)
    datos_anteriores = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    datos_nuevos = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "auditoria"
        verbose_name = "Historial de modificación"
        verbose_name_plural = "Historial de modificaciones"
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["tabla_afectada", "registro_id"])]

    def __str__(self) -> str:
        return f"{self.accion} {self.tabla_afectada}#{self.registro_id}"
