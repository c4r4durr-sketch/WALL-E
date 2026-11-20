"""
Campos de DRF más estrictos que los de serie, compartidos por los
serializers de todos los módulos.

- EnteroEstricto: IntegerField de DRF acepta 5.0, "5.0" o 1e1 y los
  convierte a entero. Acá solo se aceptan enteros de verdad (o su texto,
  porque multipart manda todo como texto): "5" sí; "5.0", "5.5", "1e3",
  true, no.
- Monto: DecimalField de DRF acepta notación científica ("1e3"). Acá no.
  Los montos son mayores que 0 con hasta 2 decimales.
"""

import re
from decimal import Decimal

from rest_framework import serializers

_ENTERO = re.compile(r"-?\d+")


class EnteroEstricto(serializers.IntegerField):
    default_error_messages = {
        "invalid": "Debe ser un número entero, sin decimales.",
        "min_value": "Debe ser mayor o igual que {min_value}.",
        "max_value": "Debe ser menor o igual que {max_value}.",
    }

    def to_internal_value(self, data):
        if isinstance(data, bool):
            self.fail("invalid")
        if isinstance(data, int):
            return data
        if isinstance(data, str) and _ENTERO.fullmatch(data.strip()):
            return int(data.strip())
        self.fail("invalid")


class Monto(serializers.DecimalField):
    """Número mayor que 0 con hasta 2 decimales. Con 2 decimales, "mayor
    que 0" es lo mismo que "al menos 0.01"."""

    default_error_messages = {
        "invalid": "Debe ser un número (con punto para los decimales).",
        "min_value": "Debe ser mayor que 0.",
        "max_decimal_places": "Hasta 2 decimales.",
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 12)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("min_value", Decimal("0.01"))
        kwargs.setdefault("coerce_to_string", False)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, bool) or (isinstance(data, str) and re.search(r"[eE]", data)):
            self.fail("invalid")
        return super().to_internal_value(data)
