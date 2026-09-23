"""
DTOs de resultado para los indicadores. No son "entidades" en el sentido
tradicional (no tienen identidad propia ni se persisten): son el resultado
puro de un cálculo, devuelto por los use_cases de esta app.
"""

from dataclasses import dataclass
from typing import Optional


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


# --- Panel de auditoría (HU24) ---
# Equivalente de la vista SQL vw_panel_auditoria del script descartado,
# armado en Python a partir de catálogo + movimientos.

# Umbral de estancamiento: el default del diseño original
# (herramientas.dias_para_estancamiento = 40).
DIAS_PARA_ESTANCAMIENTO = 40


@dataclass(frozen=True)
class AlertaReorden:
    """HU18: el stock total (todas las sucursales) ya tocó el punto de
    reorden. pedido_sugerido (HU19/HU20) es el EOQ redondeado a cajas
    cerradas; None si faltan costos para calcularlo."""

    herramienta_id: int
    codigo: str
    nombre: str
    stock_total: int
    punto_reorden: float
    pedido_sugerido: Optional[float]
    unidades_por_caja: int


@dataclass(frozen=True)
class HerramientaEstancada:
    """HU22: tiene stock en una sucursal pero no se vende hace más de
    DIAS_PARA_ESTANCAMIENTO días. Si nunca se vendió, los días se cuentan
    desde su primer movimiento en esa sucursal."""

    herramienta_id: int
    codigo: str
    nombre: str
    sucursal_id: int
    sucursal_nombre: str
    stock: int
    dias_sin_venta: int
    nunca_vendida: bool


@dataclass(frozen=True)
class PanelAuditoria:
    total_alertas_stock: int
    total_herramientas_estancadas: int
    total_herramientas: int
    total_sucursales_activas: int
    # Sin demanda anual o tiempo de entrega no se puede calcular el ROP:
    # se informa para que se completen en el catálogo.
    herramientas_sin_datos_rop: int
    dias_para_estancamiento: int
    alertas: list[AlertaReorden]
    estancadas: list[HerramientaEstancada]
