"""Entidad pura de dominio para el catálogo. Sin dependencias de Django."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Herramienta:
    id: Optional[int]
    codigo: str
    nombre: str
    modelo: str
    # Cuántas unidades sueltas trae una caja por mayor de esta herramienta.
    # Lo usa movimientos/use_cases para convertir CAJA <-> UNIDAD; se
    # modela acá porque es un dato propio del producto, no del movimiento.
    unidades_por_caja: int
