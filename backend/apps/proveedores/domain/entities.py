"""Entidad pura de dominio para proveedores. Sin dependencias de Django."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Proveedor:
    id: Optional[int]
    nombre: str
    telefono: str
    email: str = ""
    # Un proveedor con herramientas asociadas no se elimina: se desactiva.
    # Uno inactivo no se puede asignar a herramientas nuevas.
    activo: bool = True
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    # Solo lectura, para mostrar; lo completa el repositorio.
    cantidad_herramientas: int = 0
