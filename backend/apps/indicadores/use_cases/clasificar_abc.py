"""
Caso de uso: clasificación ABC por rotación.

Se ordenan las herramientas por unidades vendidas en los últimos 12 meses
(salidas reales: ajustes y transferencias no son ventas), de mayor a menor,
y se acumula su participación en el total:
  A: las que entran antes de llegar al 80 % acumulado
  B: las que entran antes de llegar al 95 %
  C: el resto, y siempre las que no vendieron nada

Se clasifica por el acumulado ANTERIOR a cada herramienta: así la más
vendida es siempre A aunque ella sola supere el 80 %.

No hay costo unitario en el catálogo, por eso se usa cantidad movida y no
valor en dinero (variante de ABC por rotación).

Depende de MovimientoRepository y HerramientaRepository (imports
domain -> domain entre bounded contexts, sin Django).
"""

from datetime import datetime, timedelta

from apps.catalogo.domain.entities import Herramienta
from apps.catalogo.domain.repositories import HerramientaRepository
from apps.movimientos.domain.repositories import MovimientoRepository
from apps.movimientos.domain.stock import TIPOS_QUE_CUENTAN_COMO_DEMANDA

from ..domain.entities import PERIODO_DEMANDA_DIAS, UMBRAL_A, UMBRAL_B, ClasificacionABC


def clasificar(herramientas: list[Herramienta], vendidas: dict[int, int]) -> list[ClasificacionABC]:
    """Regla ABC pura: recibe el catálogo y las unidades vendidas por
    herramienta; devuelve la clasificación de mayor a menor rotación."""
    total = sum(vendidas.get(h.id, 0) for h in herramientas)
    ordenadas = sorted(herramientas, key=lambda h: (-vendidas.get(h.id, 0), h.codigo))

    resultado = []
    acumulado = 0.0
    for herramienta in ordenadas:
        unidades = vendidas.get(herramienta.id, 0)
        porcentaje = unidades * 100 / total if total else 0.0
        if unidades == 0:
            clase = "C"
        elif acumulado < UMBRAL_A:
            clase = "A"
        elif acumulado < UMBRAL_B:
            clase = "B"
        else:
            clase = "C"
        acumulado += porcentaje
        resultado.append(ClasificacionABC(
            herramienta_id=herramienta.id,
            codigo=herramienta.codigo,
            nombre=herramienta.nombre,
            unidades_vendidas=unidades,
            porcentaje=round(porcentaje, 2),
            porcentaje_acumulado=round(acumulado, 2),
            clase=clase,
        ))
    return resultado


def clasificar_abc(
    herramientas: HerramientaRepository,
    movimientos: MovimientoRepository,
    ahora: datetime,
) -> list[ClasificacionABC]:
    vendidas = movimientos.unidades_por_herramienta(
        TIPOS_QUE_CUENTAN_COMO_DEMANDA, desde=ahora - timedelta(days=PERIODO_DEMANDA_DIAS)
    )
    return clasificar(herramientas.listar(), vendidas)
