# Registro en el admin solo de LECTURA: el historial de auditoría (HU13) no
# se puede crear, editar ni borrar a mano, o dejaría de ser confiable.
from django.contrib import admin

from .infrastructure.models import HistorialModificacion


@admin.register(HistorialModificacion)
class HistorialModificacionAdmin(admin.ModelAdmin):
    list_display = ["fecha", "tabla_afectada", "registro_id", "accion", "usuario"]
    list_filter = ["tabla_afectada", "accion"]
    search_fields = ["registro_id", "usuario__username"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
