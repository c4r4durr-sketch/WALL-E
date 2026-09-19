"""
Caso de uso: clasificación ABC por rotación.

Regla clásica: ordenar las herramientas por valor de consumo (o cantidad
movida) descendente, acumular el porcentaje del total, y asignar:
  A: hasta ~80% acumulado
  B: hasta ~95% acumulado
  C: el resto

Depende de MovimientoRepository (apps.movimientos.domain.repositories) y
HerramientaRepository (apps.catalogo.domain.repositories) para obtener los
datos: son imports domain -> domain entre bounded contexts, sin pasar por
Django, así que siguen siendo válidos en un caso de uso puro.

Sin implementar todavía (solo el esqueleto y la regla documentada).
"""

from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository

from ..domain.entities import ClasificacionABC


def clasificar_abc(
    herramienta_repo: HerramientaRepository,
    movimiento_repo: MovimientoRepository,
) -> list[ClasificacionABC]:
    raise NotImplementedError
