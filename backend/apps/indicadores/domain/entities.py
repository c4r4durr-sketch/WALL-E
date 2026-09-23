"""
DTOs de resultado para los indicadores. No son "entidades" en el sentido
tradicional (no tienen identidad propia ni se persisten): son el resultado
puro de un cálculo, devuelto por los use_cases de esta app.
"""

from dataclasses import dataclass
from typing import Optional


# Período con el que se mide la demanda REAL (ventas registradas): los
# últimos 12 meses. Lo usan la demanda observada de EOQ y la clasificación ABC.
PERIODO_DEMANDA_DIAS = 365

# Clasificación ABC por rotación: A hasta ~80 % acumulado, B hasta ~95 %,
# C el resto.
UMBRAL_A = 80.0
UMBRAL_B = 95.0


@dataclass(frozen=True)
class ResultadoEOQ:
    """HU17/HU20/HU21. eoq es None si falta algún dato de entrada
    (datos_faltantes dice cuáles, para completarlos en el catálogo)."""

    herramienta_id: int
    codigo: str
    nombre: str
    demanda_anual: Optional[int]  # D (estimada, del catálogo)
    costo_pedido: Optional[float]  # S
    costo_almacenamiento_unitario: Optional[float]  # H
    unidades_por_caja: int
    eoq: Optional[float]  # raiz(2*D*S/H), en unidades
    eoq_ajustado_cajas: Optional[float]  # HU20: redondeado a cajas cerradas
    # HU21: ventas reales de los últimos PERIODO_DEMANDA_DIAS, para comparar
    # con la demanda estimada y decidir si hay que actualizarla.
    demanda_observada: int
    datos_faltantes: tuple[str, ...]


@dataclass(frozen=True)
class ResultadoROP:
    """HU18: punto de reorden = (D / 365) * tiempo de entrega, comparado con
    el stock total de la herramienta (todas las sucursales)."""

    herramienta_id: int
    codigo: str
    nombre: str
    demanda_anual: Optional[int]
    demanda_diaria_promedio: Optional[float]
    lead_time_dias: Optional[int]
    punto_reorden: Optional[float]
    stock_total: int
    requiere_reorden: bool  # stock_total <= punto_reorden
    datos_faltantes: tuple[str, ...]


@dataclass(frozen=True)
class ClasificacionABC:
    """Clasificación por rotación: unidades vendidas (salidas reales) en
    los últimos PERIODO_DEMANDA_DIAS. No hay costo unitario en el catálogo,
    así que se clasifica por cantidad movida y no por valor en dinero."""

    herramienta_id: int
    codigo: str
    nombre: str
    unidades_vendidas: int
    porcentaje: float  # participación en el total vendido
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
