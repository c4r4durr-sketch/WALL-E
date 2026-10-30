"""Implementación concreta (ORM) del repositorio de catálogo.

Único lugar del catálogo que traduce entre el modelo ORM y la entidad de
dominio. Guarda con .save() y borra con .delete() de cada instancia (no con
querysets masivos) para que se disparen los signals de auditoría (HU13)."""

from dataclasses import asdict
from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils.text import slugify

from ..domain.entities import CambioCosto, Herramienta, ImagenProducto, Promocion
from ..domain.exceptions import CodigoDuplicadoError, HerramientaEnUsoError
from ..domain.repositories import HerramientaRepository, HistorialCostoRepository, PromocionRepository
from .models import Herramienta as HerramientaModel
from .models import HistorialCosto as HistorialCostoModel
from .models import Promocion as PromocionModel

# Los que asigna la base, más la foto (cambia solo si guardar() recibe una
# ImagenProducto); nunca se copian de la entidad al modelo.
_CAMPOS_DEL_SISTEMA = {"id", "creado_en", "actualizado_en", "proveedor_nombre", "imagen"}

_EXTENSION_POR_FORMATO = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}


def _borrar_archivo_al_confirmar(storage, ruta: str) -> None:
    """El archivo se borra recién cuando la transacción se confirma: si se
    revierte, la fila sigue apuntando a una foto que todavía existe."""
    if ruta:
        transaction.on_commit(lambda: storage.delete(ruta))


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
        costo_unitario=modelo.costo_unitario,
        proveedor_id=modelo.proveedor_id,
        imagen=modelo.imagen.name or None,
        creado_en=modelo.creado_en,
        actualizado_en=modelo.actualizado_en,
        proveedor_nombre=modelo.proveedor.nombre if modelo.proveedor_id else None,
    )


class HerramientaRepositoryDjango(HerramientaRepository):
    def _consulta(self):
        # select_related: el nombre del proveedor sale en la misma consulta.
        return HerramientaModel.objects.select_related("proveedor")

    def obtener_por_id(self, herramienta_id: int) -> Optional[Herramienta]:
        modelo = self._consulta().filter(pk=herramienta_id).first()
        return _a_entidad(modelo) if modelo else None

    def obtener_por_codigo(self, codigo: str) -> Optional[Herramienta]:
        modelo = self._consulta().filter(codigo=codigo).first()
        return _a_entidad(modelo) if modelo else None

    def listar(self) -> list[Herramienta]:
        return [_a_entidad(m) for m in self._consulta().order_by("nombre", "codigo")]

    def guardar(self, herramienta: Herramienta, imagen: Optional[ImagenProducto] = None) -> Herramienta:
        valores = {k: v for k, v in asdict(herramienta).items() if k not in _CAMPOS_DEL_SISTEMA}
        if herramienta.id is None:
            modelo = HerramientaModel(**valores)
        else:
            modelo = HerramientaModel.objects.get(pk=herramienta.id)
            for campo, valor in valores.items():
                setattr(modelo, campo, valor)
        anterior = modelo.imagen.name
        if imagen is not None:
            # Nombre propio (no el del archivo subido): sin caracteres raros
            # y con la extensión del formato real. Si ya existe, el almacén
            # le agrega un sufijo. save=False: la foto va en el mismo
            # INSERT/UPDATE que el resto (un solo registro de auditoría).
            nombre = f"{slugify(herramienta.codigo) or 'herramienta'}.{_EXTENSION_POR_FORMATO.get(imagen.formato, 'img')}"
            modelo.imagen.save(nombre, imagen.contenido, save=False)
        try:
            # atomic: si la base rechaza el código (dos altas simultáneas con
            # el mismo código), no deja la transacción del request rota.
            with transaction.atomic():
                modelo.save()
        except IntegrityError as error:
            if imagen is not None:
                modelo.imagen.storage.delete(modelo.imagen.name)
            if "codigo" not in str(error):
                raise
            raise CodigoDuplicadoError(herramienta.codigo) from error
        if imagen is not None and anterior:
            _borrar_archivo_al_confirmar(modelo.imagen.storage, anterior)
        return self.obtener_por_id(modelo.id)

    def eliminar(self, herramienta_id: int) -> None:
        modelo = HerramientaModel.objects.get(pk=herramienta_id)
        try:
            modelo.delete()
        except ProtectedError as error:
            raise HerramientaEnUsoError(herramienta_id) from error
        _borrar_archivo_al_confirmar(modelo.imagen.storage, modelo.imagen.name)


def _cambio_a_entidad(modelo: HistorialCostoModel) -> CambioCosto:
    return CambioCosto(
        id=modelo.id,
        herramienta_id=modelo.herramienta_id,
        costo_anterior=modelo.costo_anterior,
        costo_nuevo=modelo.costo_nuevo,
        usuario_id=modelo.usuario_id,
        usuario_username=modelo.usuario.username,
        fecha=modelo.fecha,
    )


class HistorialCostoRepositoryDjango(HistorialCostoRepository):
    def registrar(self, cambio: CambioCosto) -> CambioCosto:
        modelo = HistorialCostoModel(
            herramienta_id=cambio.herramienta_id,
            costo_anterior=cambio.costo_anterior,
            costo_nuevo=cambio.costo_nuevo,
            usuario_id=cambio.usuario_id,
        )
        modelo.save()
        return _cambio_a_entidad(HistorialCostoModel.objects.select_related("usuario").get(pk=modelo.pk))

    def listar_por_herramienta(self, herramienta_id: int) -> list[CambioCosto]:
        # select_related: el username sale en la misma consulta.
        filas = (
            HistorialCostoModel.objects.select_related("usuario")
            .filter(herramienta_id=herramienta_id)
            .order_by("-fecha", "-id")
        )
        return [_cambio_a_entidad(m) for m in filas]


def _promocion_a_entidad(modelo: PromocionModel) -> Promocion:
    return Promocion(
        id=modelo.id,
        herramienta_id=modelo.herramienta_id,
        sucursal_id=modelo.sucursal_id,
        descuento_porcentaje=modelo.descuento_porcentaje,
        fecha_inicio=modelo.fecha_inicio,
        fecha_fin=modelo.fecha_fin,
        usuario_id=modelo.usuario_id,
        motivo=modelo.motivo,
        activa=modelo.activa,
        creado_en=modelo.creado_en,
        herramienta_codigo=modelo.herramienta.codigo,
        herramienta_nombre=modelo.herramienta.nombre,
        sucursal_nombre=modelo.sucursal.nombre,
        usuario_username=modelo.usuario.username,
    )


class PromocionRepositoryDjango(PromocionRepository):
    def _consulta(self):
        # select_related: los nombres para mostrar salen en la misma consulta.
        return PromocionModel.objects.select_related("herramienta", "sucursal", "usuario").order_by("-creado_en", "-id")

    def obtener_por_id(self, promocion_id: int) -> Optional[Promocion]:
        modelo = self._consulta().filter(pk=promocion_id).first()
        return _promocion_a_entidad(modelo) if modelo else None

    def listar(self) -> list[Promocion]:
        return [_promocion_a_entidad(m) for m in self._consulta()]

    def de_herramienta_en_sucursal(self, herramienta_id: int, sucursal_id: int) -> list[Promocion]:
        filas = self._consulta().filter(herramienta_id=herramienta_id, sucursal_id=sucursal_id)
        return [_promocion_a_entidad(m) for m in filas]

    def guardar(self, promocion: Promocion) -> Promocion:
        # .save() por instancia: así la auditoría (signals) registra el cambio.
        modelo = PromocionModel.objects.get(pk=promocion.id) if promocion.id else PromocionModel()
        modelo.herramienta_id = promocion.herramienta_id
        modelo.sucursal_id = promocion.sucursal_id
        modelo.descuento_porcentaje = promocion.descuento_porcentaje
        modelo.fecha_inicio = promocion.fecha_inicio
        modelo.fecha_fin = promocion.fecha_fin
        modelo.motivo = promocion.motivo
        modelo.activa = promocion.activa
        modelo.usuario_id = promocion.usuario_id
        modelo.save()
        return self.obtener_por_id(modelo.pk)
