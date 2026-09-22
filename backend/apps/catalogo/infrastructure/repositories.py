"""Implementación concreta (ORM) del repositorio de catálogo.

Único lugar del catálogo que traduce entre el modelo ORM y la entidad de
dominio. Guarda con .save() y borra con .delete() de cada instancia (no con
querysets masivos) para que se disparen los signals de auditoría (HU13)."""

from dataclasses import asdict
from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from ..domain.entities import Herramienta
from ..domain.exceptions import CodigoDuplicadoError, HerramientaEnUsoError
from ..domain.repositories import HerramientaRepository
from .models import Herramienta as HerramientaModel

# Los que asigna la base; nunca se copian de la entidad al modelo.
_CAMPOS_DEL_SISTEMA = {"id", "creado_en", "actualizado_en"}


def _a_entidad(modelo: HerramientaModel) -> Herramienta:
    return Herramienta(
        id=modelo.id,
        codigo=modelo.codigo,
        nombre=modelo.nombre,
        modelo=modelo.modelo,
        unidades_por_caja=modelo.unidades_por_caja,
        demanda_anual=modelo.demanda_anual,
        costo_pedido=modelo.costo_pedido,
        costo_almacenamiento_unitario=modelo.costo_almacenamiento_unitario,
        tiempo_entrega_dias=modelo.tiempo_entrega_dias,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
    )


class HerramientaRepositoryDjango(HerramientaRepository):
    def obtener_por_id(self, herramienta_id: int) -> Optional[Herramienta]:
        modelo = HerramientaModel.objects.filter(pk=herramienta_id).first()
        return _a_entidad(modelo) if modelo else None

    def obtener_por_codigo(self, codigo: str) -> Optional[Herramienta]:
        modelo = HerramientaModel.objects.filter(codigo=codigo).first()
        return _a_entidad(modelo) if modelo else None

    def listar(self) -> list[Herramienta]:
        return [_a_entidad(m) for m in HerramientaModel.objects.order_by("nombre", "codigo")]

    def guardar(self, herramienta: Herramienta) -> Herramienta:
        valores = {k: v for k, v in asdict(herramienta).items() if k not in _CAMPOS_DEL_SISTEMA}
        if herramienta.id is None:
            modelo = HerramientaModel(**valores)
        else:
            modelo = HerramientaModel.objects.get(pk=herramienta.id)
            for campo, valor in valores.items():
                setattr(modelo, campo, valor)
        try:
            # atomic: si la base rechaza el código (dos altas simultáneas con
            # el mismo código), no deja la transacción del request rota.
            with transaction.atomic():
                modelo.save()
        except IntegrityError as error:
            if "codigo" not in str(error):
                raise
            raise CodigoDuplicadoError(herramienta.codigo) from error
        return _a_entidad(modelo)

    def eliminar(self, herramienta_id: int) -> None:
        try:
            HerramientaModel.objects.get(pk=herramienta_id).delete()
        except ProtectedError as error:
            raise HerramientaEnUsoError(herramienta_id) from error
