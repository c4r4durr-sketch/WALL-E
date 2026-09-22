"""Implementación concreta (ORM) del repositorio de movimientos.

Único lugar de movimientos que traduce entre el modelo ORM y la entidad de
dominio. Guarda con .save() para que se disparen los signals de auditoría
(HU13)."""

from typing import Optional

from django.db.models import Sum

from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel

from ..domain.entities import Movimiento
from ..domain.repositories import MovimientoRepository
from ..domain.value_objects import TipoMovimiento, TipoUnidad
from .models import Movimiento as MovimientoModel


def _a_entidad(modelo: MovimientoModel) -> Movimiento:
    return Movimiento(
        id=modelo.id,
        herramienta_id=modelo.herramienta_id,
        sucursal_id=modelo.sucursal_id,
        tipo_movimiento=TipoMovimiento(modelo.tipo_movimiento),
        tipo_unidad=TipoUnidad(modelo.tipo_unidad),
        cantidad=modelo.cantidad,
        cantidad_unidades=modelo.cantidad_unidades,
        usuario_id=modelo.usuario_id,
        creado_en=modelo.creado_en,
        usuario_username=modelo.usuario.username,
    )


class MovimientoRepositoryDjango(MovimientoRepository):
    def obtener_por_id(self, movimiento_id: int) -> Optional[Movimiento]:
        modelo = MovimientoModel.objects.select_related("usuario").filter(pk=movimiento_id).first()
        return _a_entidad(modelo) if modelo else None

    def listar(
        self, herramienta_id: Optional[int] = None, sucursal_id: Optional[int] = None
    ) -> list[Movimiento]:
        consulta = MovimientoModel.objects.select_related("usuario").order_by("-creado_en", "-id")
        if herramienta_id is not None:
            consulta = consulta.filter(herramienta_id=herramienta_id)
        if sucursal_id is not None:
            consulta = consulta.filter(sucursal_id=sucursal_id)
        return [_a_entidad(m) for m in consulta]

    def unidades_por_tipo(self, herramienta_id: int, sucursal_id: int) -> dict[TipoMovimiento, int]:
        filas = (
            MovimientoModel.objects.filter(herramienta_id=herramienta_id, sucursal_id=sucursal_id)
            .values("tipo_movimiento")
            .annotate(total=Sum("cantidad_unidades"))
        )
        return {TipoMovimiento(f["tipo_movimiento"]): f["total"] for f in filas}

    def bloquear_stock(self, herramienta_id: int) -> None:
        # SELECT ... FOR UPDATE sobre la fila de la herramienta: toda salida
        # de esa herramienta pasa por acá, así que quedan en fila una tras
        # otra. Requiere una transacción abierta (la abre la vista).
        list(HerramientaModel.objects.select_for_update().filter(pk=herramienta_id).values_list("pk"))

    def guardar(self, movimiento: Movimiento) -> Movimiento:
        if movimiento.id is not None:
            raise ValueError("Los movimientos son inmutables: solo se pueden crear.")
        modelo = MovimientoModel(
            herramienta_id=movimiento.herramienta_id,
            sucursal_id=movimiento.sucursal_id,
            usuario_id=movimiento.usuario_id,
            tipo_movimiento=movimiento.tipo_movimiento.value,
            tipo_unidad=movimiento.tipo_unidad.value,
            cantidad=movimiento.cantidad,
            cantidad_unidades=movimiento.cantidad_unidades,
        )
        modelo.save()
        return self.obtener_por_id(modelo.id)
