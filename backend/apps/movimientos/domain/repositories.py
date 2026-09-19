"""Puerto de repositorio de movimientos. Ver justificación en
apps/usuarios/domain/repositories.py.

Se expone `listar_por_herramienta_y_sucursal` (además del CRUD básico)
porque tanto "calcular stock" como "clasificación ABC por rotación"
(apps/indicadores) necesitan iterar el historial de movimientos de un
producto, no solo leerlos uno por uno."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Movimiento


class MovimientoRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, movimiento_id: int) -> Optional[Movimiento]:
        ...

    @abstractmethod
    def listar_por_herramienta_y_sucursal(
        self, herramienta_id: int, sucursal_id: int
    ) -> list[Movimiento]:
        ...

    @abstractmethod
    def listar(self) -> list[Movimiento]:
        ...

    @abstractmethod
    def guardar(self, movimiento: Movimiento) -> Movimiento:
        ...
