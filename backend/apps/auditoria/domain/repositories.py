"""Puerto de repositorio del historial de modificaciones (solo lectura:
el historial lo escriben los signals de infraestructura, nunca un caso de
uso). Ver justificación en apps/usuarios/domain/repositories.py."""

from abc import ABC, abstractmethod

from .entities import FiltroHistorial, OpcionFiltro, RegistroHistorial


class HistorialRepository(ABC):
    @abstractmethod
    def buscar(self, filtro: FiltroHistorial, desde: int, limite: int) -> tuple[int, list[RegistroHistorial]]:
        """(total que cumple el filtro, registros [desde, desde+limite)),
        del más reciente al más antiguo."""
        ...

    @abstractmethod
    def tablas(self) -> list[OpcionFiltro]:
        """Tablas que aparecen en el historial (valor = etiqueta del modelo)."""
        ...

    @abstractmethod
    def autores(self) -> list[OpcionFiltro]:
        """Usuarios que aparecen como autores (valor = id del usuario)."""
        ...
