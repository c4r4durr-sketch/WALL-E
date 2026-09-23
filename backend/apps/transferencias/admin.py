# Admin de SOLO LECTURA para transferencias: crearlas o cambiarles el
# estado desde acá se saltaría la validación de stock y no generaría los
# movimientos. Se gestionan solo por la API (use_cases).
from django.contrib import admin

from .infrastructure.models import Transferencia


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ["creado_en", "herramienta", "sucursal_origen", "sucursal_destino",
                    "cantidad", "tipo_unidad", "estado", "usuario", "resuelto_por"]
    list_filter = ["estado"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
