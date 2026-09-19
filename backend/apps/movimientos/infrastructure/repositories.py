"""Implementación concreta (ORM) del repositorio de movimientos.
Sin implementar todavía: ver justificación en
apps/usuarios/infrastructure/repositories.py."""

from typing import Optional

from ..domain.entities import Movimiento
from ..domain.repositories import MovimientoRepository
from .models import Movimiento as MovimientoModel  # noqa: F401


class MovimientoRepositoryDjango(MovimientoRepository):
    def obtener_por_id(self, movimiento_id: int) -> Optional[Movimiento]:
        raise NotImplementedError

    def listar_por_herramienta_y_sucursal(
        self, herramienta_id: int, sucursal_id: int
    ) -> list[Movimiento]:
        raise NotImplementedError

    def listar(self) -> list[Movimiento]:
        raise NotImplementedError

    def guardar(self, movimiento: Movimiento) -> Movimiento:
        raise NotImplementedError
