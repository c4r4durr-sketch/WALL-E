"""Value objects puros del dominio de movimientos."""

from enum import Enum


class TipoMovimiento(str, Enum):
    # Operaciones normales del mostrador (HU9).
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    # Correcciones de stock: solo Administrador/Supervisor, siempre con
    # motivo. Como los movimientos son inmutables, un error se corrige con
    # un ajuste nuevo; NO cuentan como demanda para EOQ/ABC (ver
    # domain/stock.py::cuenta_como_demanda).
    AJUSTE_POSITIVO = "AJUSTE_POSITIVO"
    AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO"

    @property
    def es_ajuste(self) -> bool:
        return self in (TipoMovimiento.AJUSTE_POSITIVO, TipoMovimiento.AJUSTE_NEGATIVO)


class TipoUnidad(str, Enum):
    """Distingue unidad suelta de caja por mayor. La conversión entre
    ambas usa Herramienta.unidades_por_caja (ver apps/catalogo)."""

    UNIDAD = "UNIDAD"
    CAJA = "CAJA"
