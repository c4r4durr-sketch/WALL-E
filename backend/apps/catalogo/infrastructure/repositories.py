"""Implementación concreta (ORM) del repositorio de catálogo.
Sin implementar todavía: ver justificación en
apps/usuarios/infrastructure/repositories.py."""

from typing import Optional

from ..domain.entities import Herramienta
from ..domain.repositories import HerramientaRepository
from .models import Herramienta as HerramientaModel  # noqa: F401


class HerramientaRepositoryDjango(HerramientaRepository):
    def obtener_por_id(self, herramienta_id: int) -> Optional[Herramienta]:
        raise NotImplementedError

    def obtener_por_codigo(self, codigo: str) -> Optional[Herramienta]:
        raise NotImplementedError

    def listar(self) -> list[Herramienta]:
        raise NotImplementedError

    def guardar(self, herramienta: Herramienta) -> Herramienta:
        raise NotImplementedError
