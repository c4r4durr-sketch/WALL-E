"""
Reglas puras de antigüedad del stock (HU22): cuántos días lleva una
herramienta sin venderse en una sucursal y en qué tramo cae. Las usan el
panel (estancadas) y el reporte de antigüedad, para que los dos cuenten
igual.
"""

from datetime import date, datetime
from typing import Optional

# Tramos del reporte: (desde, hasta, etiqueta); hasta None = sin tope. El
# corte de 40 días coincide con DIAS_PARA_ESTANCAMIENTO: los dos últimos
# tramos son las estancadas.
TRAMOS = (
    (0, 30, "0–30 días"),
    (31, 40, "31–40 días"),
    (41, 90, "41–90 días"),
    (91, None, "Más de 90 días"),
)


def dias_sin_venta(ultima_salida: Optional[datetime], primer_movimiento: datetime, hoy: date) -> int:
    """Días desde la última SALIDA real; si nunca se vendió, desde su
    primer movimiento en la sucursal (algo que acaba de ingresar no está
    estancado)."""
    referencia = ultima_salida or primer_movimiento
    return (hoy - referencia.date()).days


def tramo(dias: int) -> str:
    for desde, hasta, etiqueta in TRAMOS:
        if dias >= desde and (hasta is None or dias <= hasta):
            return etiqueta
    return TRAMOS[0][2]  # días negativos (fecha en el futuro): el más reciente
