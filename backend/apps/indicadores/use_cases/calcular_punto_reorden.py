"""
Caso de uso: Punto de Reorden (ROP).

Fórmula base: ROP = demanda_diaria_promedio * lead_time_dias
(un stock de seguridad adicional se puede sumar más adelante si el equipo
lo define; por ahora se documenta solo la fórmula base pedida).

Caso de uso puro: no importa Django. Sin implementar todavía.
"""

from ..domain.entities import ResultadoROP


def calcular_punto_reorden(
    herramienta_id: int,
    demanda_diaria_promedio: float,
    lead_time_dias: int,
) -> ResultadoROP:
    raise NotImplementedError
