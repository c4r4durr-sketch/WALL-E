"""
Entidades puras del dominio de auditoría (HU13). Sin dependencias de
Django: el historial se lee a través de domain/repositories.py.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

from .value_objects import AccionAuditoria


@dataclass(frozen=True)
class RegistroHistorial:
    """Un alta, edición o baja de un registro auditado, con su autor.
    `tabla` es la etiqueta del modelo (catalogo.Herramienta); `tabla_nombre`
    su nombre legible (Herramientas). Las claves de los datos son nombres
    de campo de Python, no nombres físicos de columna."""

    id: int
    fecha: datetime
    tabla: str
    tabla_nombre: str
    registro_id: str
    accion: AccionAuditoria
    usuario_id: Optional[int]
    usuario_username: str
    datos_anteriores: Optional[dict[str, Any]]
    datos_nuevos: Optional[dict[str, Any]]
    # Lo completa el caso de uso: en una edición, qué campos cambiaron.
    campos_cambiados: tuple[str, ...] = ()


@dataclass(frozen=True)
class FiltroHistorial:
    """Todos opcionales. `desde`/`hasta` son días calendario de la zona
    horaria del negocio, ambos incluidos."""

    desde: Optional[date] = None
    hasta: Optional[date] = None
    usuario_id: Optional[int] = None
    tabla: Optional[str] = None
    accion: Optional[AccionAuditoria] = None


@dataclass(frozen=True)
class PaginaHistorial:
    total: int
    pagina: int
    tamano: int
    resultados: tuple[RegistroHistorial, ...] = field(default_factory=tuple)

    @property
    def paginas(self) -> int:
        return max(1, -(-self.total // self.tamano))


@dataclass(frozen=True)
class OpcionFiltro:
    valor: str
    texto: str
