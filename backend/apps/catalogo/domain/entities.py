"""Entidad pura de dominio para el catálogo. Sin dependencias de Django."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
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
    # Datos de entrada para EOQ/ROP (ver indicadores/domain/formulas.py).
    # Opcionales: sin ellos el indicador correspondiente queda en None.
    demanda_anual: Optional[int] = None
    costo_pedido: Optional[Decimal] = None
    costo_almacenamiento_unitario: Optional[Decimal] = None
    tiempo_entrega_dias: Optional[int] = None
    # HU7: costo de compra de una unidad. Opcional (las herramientas ya
    # cargadas no lo tienen); cada cambio queda en el historial de costos.
    costo_unitario: Optional[Decimal] = None
    # Los asigna la base al guardar; None en una herramienta nueva.
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None


@dataclass(frozen=True)
class CambioCosto:
    """HU7: un cambio del costo unitario de una herramienta. Inmutable: es
    el historial, no se edita ni se borra. costo_anterior es None cuando
    es la primera vez que se carga el costo."""

    id: Optional[int]
    herramienta_id: int
    costo_anterior: Optional[Decimal]
    costo_nuevo: Decimal
    usuario_id: int
    # Solo lectura, para mostrar; lo completa el repositorio.
    usuario_username: str = ""
    fecha: Optional[datetime] = None
