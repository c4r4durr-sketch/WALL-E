"""Puerto de repositorio del catálogo. Ver justificación en
apps/usuarios/domain/repositories.py."""

from abc import ABC, abstractmethod
from typing import Optional

from .entities import CambioCosto, Herramienta, ImagenProducto, Promocion


class HerramientaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, herramienta_id: int) -> Optional[Herramienta]:
        ...

    @abstractmethod
    def obtener_por_codigo(self, codigo: str) -> Optional[Herramienta]:
        ...

    @abstractmethod
    def listar(self) -> list[Herramienta]:
        ...

    @abstractmethod
    def guardar(self, herramienta: Herramienta, imagen: Optional[ImagenProducto] = None) -> Herramienta:
        """Crea la herramienta si id es None; si no, la actualiza.
        Lanza CodigoDuplicadoError si la base rechaza el código. Con
        `imagen`, además la guarda como foto; la anterior, si había, se
        borra del almacén cuando la transacción se confirma. Sin `imagen`,
        la foto no cambia."""
        ...

    @abstractmethod
    def eliminar(self, herramienta_id: int) -> None:
        """Lanza HerramientaEnUsoError si tiene movimientos, transferencias
        o historial de costos que la referencian."""
        ...


class HistorialCostoRepository(ABC):
    @abstractmethod
    def registrar(self, cambio: CambioCosto) -> CambioCosto:
        ...

    @abstractmethod
    def listar_por_herramienta(self, herramienta_id: int) -> list[CambioCosto]:
        """Del cambio más reciente al más antiguo."""
        ...


class PromocionRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, promocion_id: int) -> Optional[Promocion]:
        ...

    @abstractmethod
    def listar(self) -> list[Promocion]:
        """De la más reciente a la más antigua."""
        ...

    @abstractmethod
    def de_herramienta_en_sucursal(self, herramienta_id: int, sucursal_id: int) -> list[Promocion]:
        ...

    @abstractmethod
    def guardar(self, promocion: Promocion) -> Promocion:
        """Crea la promoción si id es None; si no, la actualiza."""
        ...
