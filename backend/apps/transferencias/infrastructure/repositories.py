"""Implementación concreta (ORM) del repositorio de transferencias.

Único lugar de transferencias que traduce entre el modelo ORM y la entidad
de dominio. Guarda con .save() para que se disparen los signals de
auditoría (HU13)."""

from typing import Optional

from apps.movimientos.domain.value_objects import TipoUnidad

from ..domain.entities import Transferencia
from ..domain.repositories import TransferenciaRepository
from ..domain.value_objects import EstadoTransferencia
from .models import Transferencia as TransferenciaModel

# Lo que el use case puede cambiar al resolver una transferencia; el resto
# (herramienta, sucursales, cantidades, solicitante) es fijo desde la solicitud.
_CAMPOS_DE_RESOLUCION = [
    "estado", "resuelto_por_id", "resuelto_en", "motivo_rechazo",
    "movimiento_salida_id", "movimiento_entrada_id",
]


def _a_entidad(m: TransferenciaModel) -> Transferencia:
    return Transferencia(
        id=m.id,
        herramienta_id=m.herramienta_id,
        sucursal_origen_id=m.sucursal_origen_id,
        sucursal_destino_id=m.sucursal_destino_id,
        cantidad=m.cantidad,
        tipo_unidad=TipoUnidad(m.tipo_unidad),
        cantidad_unidades=m.cantidad_unidades,
        estado=EstadoTransferencia(m.estado),
        usuario_id=m.usuario_id,
        creado_en=m.creado_en,
        resuelto_por_id=m.resuelto_por_id,
        resuelto_en=m.resuelto_en,
        motivo_rechazo=m.motivo_rechazo,
        movimiento_salida_id=m.movimiento_salida_id,
        movimiento_entrada_id=m.movimiento_entrada_id,
        usuario_username=m.usuario.username,
        resuelto_por_username=m.resuelto_por.username if m.resuelto_por_id else None,
    )


def _consulta():
    return TransferenciaModel.objects.select_related("usuario", "resuelto_por")


class TransferenciaRepositoryDjango(TransferenciaRepository):
    def obtener_por_id(self, transferencia_id: int) -> Optional[Transferencia]:
        modelo = _consulta().filter(pk=transferencia_id).first()
        return _a_entidad(modelo) if modelo else None

    def obtener_para_resolver(self, transferencia_id: int) -> Optional[Transferencia]:
        # SELECT ... FOR UPDATE sobre la fila de la transferencia, SIN
        # select_related: si otra operación la estaba resolviendo, PostgreSQL
        # devuelve la fila ya actualizada pero las tablas unidas por JOIN
        # quedarían desactualizadas (resuelto_por_id con valor y resuelto_por
        # vacío). Los usuarios se leen después, ya con la fila vigente.
        # Requiere una transacción abierta: la abre la vista.
        modelo = TransferenciaModel.objects.select_for_update().filter(pk=transferencia_id).first()
        return _a_entidad(modelo) if modelo else None

    def listar(self, estado: Optional[EstadoTransferencia] = None) -> list[Transferencia]:
        consulta = _consulta().order_by("-creado_en", "-id")
        if estado is not None:
            consulta = consulta.filter(estado=EstadoTransferencia(estado).value)
        return [_a_entidad(m) for m in consulta]

    def guardar(self, transferencia: Transferencia) -> Transferencia:
        if transferencia.id is None:
            modelo = TransferenciaModel(
                herramienta_id=transferencia.herramienta_id,
                sucursal_origen_id=transferencia.sucursal_origen_id,
                sucursal_destino_id=transferencia.sucursal_destino_id,
                usuario_id=transferencia.usuario_id,
                cantidad=transferencia.cantidad,
                tipo_unidad=transferencia.tipo_unidad.value,
                cantidad_unidades=transferencia.cantidad_unidades,
                estado=transferencia.estado.value,
            )
            modelo.save()
        else:
            modelo = TransferenciaModel.objects.get(pk=transferencia.id)
            modelo.estado = transferencia.estado.value
            modelo.resuelto_por_id = transferencia.resuelto_por_id
            modelo.resuelto_en = transferencia.resuelto_en
            modelo.motivo_rechazo = transferencia.motivo_rechazo
            modelo.movimiento_salida_id = transferencia.movimiento_salida_id
            modelo.movimiento_entrada_id = transferencia.movimiento_entrada_id
            modelo.save(update_fields=_CAMPOS_DE_RESOLUCION)
        return self.obtener_por_id(modelo.id)
