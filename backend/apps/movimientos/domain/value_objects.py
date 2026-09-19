"""Value objects puros del dominio de movimientos."""

from enum import Enum


class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"


class TipoUnidad(str, Enum):
    """Distingue unidad suelta de caja por mayor. La conversión entre
    ambas usa Herramienta.unidades_por_caja (ver apps/catalogo)."""

    UNIDAD = "UNIDAD"
    CAJA = "CAJA"
