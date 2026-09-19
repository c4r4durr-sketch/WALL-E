"""
DTOs de resultado para los indicadores. No son "entidades" en el sentido
tradicional (no tienen identidad propia ni se persisten): son el resultado
puro de un cálculo, devuelto por los use_cases de esta app.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoEOQ:
    herramienta_id: int
    demanda_anual: int  # D
    costo_pedido: float  # S
    costo_almacenamiento_unitario: float  # H
    eoq: float  # raiz(2*D*S/H)


@dataclass(frozen=True)
class ResultadoROP:
    herramienta_id: int
    demanda_diaria_promedio: float
    lead_time_dias: int
    punto_reorden: float


@dataclass(frozen=True)
class ClasificacionABC:
    herramienta_id: int
    valor_consumo: float
    porcentaje_acumulado: float
    clase: str  # "A" | "B" | "C"
