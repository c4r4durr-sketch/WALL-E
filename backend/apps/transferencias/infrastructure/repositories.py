"""Implementación concreta (ORM) del repositorio de transferencias.
Sin implementar todavía: ver justificación en
apps/usuarios/infrastructure/repositories.py."""

from typing import Optional

from ..domain.entities import Transferencia
from ..domain.repositories import TransferenciaRepository
from .models import Transferencia as TransferenciaModel  # noqa: F401


class TransferenciaRepositoryDjango(TransferenciaRepository):
    def obtener_por_id(self, transferencia_id: int) -> Optional[Transferencia]:
        raise NotImplementedError

    def listar(self) -> list[Transferencia]:
        raise NotImplementedError

    def guardar(self, transferencia: Transferencia) -> Transferencia:
        raise NotImplementedError
