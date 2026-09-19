# Registro en el admin de Django: útil para inspeccionar datos a mano
# durante el desarrollo. No forma parte de ninguna capa de Clean
# Architecture (es una herramienta operativa de Django), por eso vive
# suelto en la raíz de la app en vez de en infrastructure/.
from django.contrib import admin

from .infrastructure.models import Sucursal, Usuario

admin.site.register(Sucursal)
admin.site.register(Usuario)
