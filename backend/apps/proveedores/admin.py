# Registro en el admin de Django para inspeccionar datos a mano (ver
# justificación en apps/usuarios/admin.py).
from django.contrib import admin

from .infrastructure.models import Proveedor

admin.site.register(Proveedor)
