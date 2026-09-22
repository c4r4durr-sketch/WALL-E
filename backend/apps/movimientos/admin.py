# Admin de SOLO LECTURA para movimientos: son registros auditables e
# inmutables. Crearlos desde acá además se saltaría la validación de stock
# y la conversión caja->unidad de los use_cases; editarlos o borrarlos
# reescribiría el historial de stock. Se registran solo por la API.
from django.contrib import admin

from .infrastructure.models import Movimiento


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ["creado_en", "herramienta", "sucursal", "tipo_movimiento", "cantidad", "tipo_unidad", "cantidad_unidades", "usuario"]
    list_filter = ["tipo_movimiento", "sucursal"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
