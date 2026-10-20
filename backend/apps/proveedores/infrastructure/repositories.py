"""Implementación concreta (ORM) del repositorio de proveedores.

Único lugar de proveedores que traduce entre el modelo ORM y la entidad de
dominio. Guarda con .save() y borra con .delete() de cada instancia para
que se disparen los signals de auditoría (HU13)."""

from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import Count, ProtectedError

from ..domain.entities import Proveedor
from ..domain.exceptions import NombreProveedorDuplicadoError, ProveedorEnUsoError
from ..domain.repositories import ProveedorRepository
from .models import Proveedor as ProveedorModel


def _a_entidad(modelo: ProveedorModel) -> Proveedor:
    return Proveedor(
        id=modelo.id,
        nombre=modelo.nombre,
        telefono=modelo.telefono,
        email=modelo.email,
        activo=modelo.activo,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
        cantidad_herramientas=getattr(modelo, "cantidad_herramientas", 0),
    )


class ProveedorRepositoryDjango(ProveedorRepository):
    def _consulta(self):
        # La cantidad de herramientas sale en la misma consulta (COUNT con
        # GROUP BY), sin una consulta extra por proveedor al listar.
        return ProveedorModel.objects.annotate(cantidad_herramientas=Count("herramientas"))

    def obtener_por_id(self, proveedor_id: int) -> Optional[Proveedor]:
        modelo = self._consulta().filter(pk=proveedor_id).first()
        return _a_entidad(modelo) if modelo else None

    def obtener_por_nombre(self, nombre: str) -> Optional[Proveedor]:
        modelo = ProveedorModel.objects.filter(nombre__iexact=nombre).first()
        return _a_entidad(modelo) if modelo else None

    def listar(self, buscar: str = "", solo_activos: bool = False) -> list[Proveedor]:
        consulta = self._consulta().order_by("nombre")
        if buscar:
            consulta = consulta.filter(nombre__icontains=buscar)
        if solo_activos:
            consulta = consulta.filter(activo=True)
        return [_a_entidad(m) for m in consulta]

    def guardar(self, proveedor: Proveedor) -> Proveedor:
        if proveedor.id is None:
            modelo = ProveedorModel()
        else:
            modelo = ProveedorModel.objects.get(pk=proveedor.id)
        modelo.nombre = proveedor.nombre
        modelo.telefono = proveedor.telefono
        modelo.email = proveedor.email
        modelo.activo = proveedor.activo
        try:
            # atomic: si la base rechaza el nombre (dos altas simultáneas),
            # no deja rota la transacción del request.
            with transaction.atomic():
                modelo.save()
        except IntegrityError as error:
            if "nombre" not in str(error):
                raise
            raise NombreProveedorDuplicadoError(proveedor.nombre) from error
        return self.obtener_por_id(modelo.id)

    def eliminar(self, proveedor_id: int) -> None:
        try:
            ProveedorModel.objects.get(pk=proveedor_id).delete()
        except ProtectedError as error:
            raise ProveedorEnUsoError(proveedor_id) from error
