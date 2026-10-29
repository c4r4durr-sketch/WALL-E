"""Entidad pura de dominio para el catálogo. Sin dependencias de Django."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional


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
    # HU8: a qué proveedor se le compra (opcional). Solo se puede asignar
    # un proveedor activo.
    proveedor_id: Optional[int] = None
    # Foto del producto: ruta del archivo en el almacén de imágenes (None en
    # las herramientas cargadas antes de que la foto fuera obligatoria).
    # No se edita como un dato más: se cambia subiendo una ImagenProducto.
    imagen: Optional[str] = None
    # Los asigna la base al guardar; None en una herramienta nueva.
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    # Solo lectura, para mostrar; lo completa el repositorio.
    proveedor_nombre: Optional[str] = None


# Formatos de la foto (como los nombra Pillow -> como se le muestran al
# usuario) y tamaño máximo.
FORMATOS_DE_IMAGEN = {"JPEG": "JPG", "PNG": "PNG", "WEBP": "WebP"}
TAMANO_MAXIMO_IMAGEN = 5 * 1024 * 1024


@dataclass(frozen=True)
class ImagenProducto:
    """Una foto recién subida, todavía sin guardar. `formato` es el que
    detectó la capa de interfaz al leer el archivo (no la extensión del
    nombre); `contenido` es el archivo en sí y solo lo entiende la
    infraestructura que lo guarda."""

    nombre: str
    formato: str
    tamano_bytes: int
    contenido: Any = None


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


@dataclass(frozen=True)
class Promocion:
    """HU23: etiqueta de promoción para sacar el stock estancado de una
    herramienta en una sucursal, con un descuento opcional. Empieza el día
    que se crea y dura hasta fecha_fin (inclusive). No se edita ni se
    borra: se quita antes (activa=False) y todo queda en el historial de
    modificaciones."""

    id: Optional[int]
    herramienta_id: int
    sucursal_id: int
    descuento_porcentaje: Optional[int]  # None: etiqueta sin descuento
    fecha_inicio: date
    fecha_fin: date
    usuario_id: int
    motivo: str = ""
    activa: bool = True
    creado_en: Optional[datetime] = None
    # Solo lectura, para mostrar; los completa el repositorio.
    herramienta_codigo: str = ""
    herramienta_nombre: str = ""
    sucursal_nombre: str = ""
    usuario_username: str = ""

    def vigente(self, hoy: date) -> bool:
        return self.activa and self.fecha_inicio <= hoy <= self.fecha_fin
