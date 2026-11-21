"""Puerto del repositorio de estadísticas (página /reportes). Ver la
justificación de los puertos en apps/usuarios/domain/repositories.py.

Cada método es una consulta agregada: la base suma y cuenta, el caso de uso
solo arma la respuesta. Las fechas son días de La Paz (TIME_ZONE) y van
incluidas; sucursal_id None = todas las sucursales."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from .estadisticas import (
    InventarioHerramienta,
    StockSucursal,
    TransferenciasDelMes,
    UnidadesDelMes,
    VentaHerramienta,
)


class EstadisticasRepository(ABC):
    @abstractmethod
    def unidades_por_mes(self, desde: date, hasta: date, sucursal_id: Optional[int]) -> list[UnidadesDelMes]:
        """Unidades por mes y tipo de movimiento (solo pares con datos)."""
        ...

    @abstractmethod
    def total_movimientos(self, desde: date, hasta: date, sucursal_id: Optional[int]) -> int:
        """Cantidad de movimientos registrados (de cualquier tipo)."""
        ...

    @abstractmethod
    def ventas_por_herramienta(self, desde: date, hasta: date, sucursal_id: Optional[int]) -> list[VentaHerramienta]:
        """Salidas reales por herramienta, de la más vendida (en unidades)
        a la menos; solo las que vendieron algo."""
        ...

    @abstractmethod
    def total_herramientas(self) -> int:
        ...

    @abstractmethod
    def stock_por_sucursal(self, hasta: date, sucursal_id: Optional[int]) -> list[StockSucursal]:
        """Stock y valor de cada sucursal con movimientos hasta ese día."""
        ...

    @abstractmethod
    def inventario(self, hasta: date, sucursal_id: Optional[int]) -> list[InventarioHerramienta]:
        """Stock de cada par herramienta/sucursal al cierre de ese día."""
        ...

    @abstractmethod
    def transferencias_por_mes(
        self, desde: date, hasta: date, sucursal_id: Optional[int]
    ) -> list[TransferenciasDelMes]:
        """Transferencias solicitadas por mes y estado actual. Con
        sucursal, las que salen de ella o llegan a ella."""
        ...
