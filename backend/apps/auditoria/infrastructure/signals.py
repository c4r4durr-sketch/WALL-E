"""
HU13: registro automático del historial de modificaciones vía signals.

Reemplaza a los triggers trg_auditoria_* del script SQL descartado. Por
cada modelo de MODELOS_AUDITADOS:
  - pre_save  guarda una foto del registro tal como está en la base, para
              tener los "datos anteriores" de un UPDATE;
  - post_save escribe un INSERT o UPDATE en HistorialModificacion;
  - post_delete escribe un DELETE con la última foto del registro.

inventario_sucursal (auditada en el SQL) no existe en este esquema: el
stock se deriva de los movimientos, así que se auditan Movimiento y
Transferencia en su lugar.
"""

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_save

from ..domain.value_objects import AccionAuditoria
from .contexto import obtener_usuario_actual
from .models import HistorialModificacion

MODELOS_AUDITADOS = [
    "usuarios.Usuario",
    "usuarios.Sucursal",
    "catalogo.Herramienta",
    "movimientos.Movimiento",
    "transferencias.Transferencia",
]

# Nunca se copian al historial (el hash de la contraseña no debe quedar
# duplicado en otra tabla).
CAMPOS_EXCLUIDOS = {"password"}

# Si un UPDATE solo cambió estos campos, no se registra: los actualiza
# Django solo (auto_now, último login) y llenarían el historial de ruido.
CAMPOS_IGNORADOS_EN_CAMBIOS = {"last_login", "actualizado_en"}


def _foto(instance) -> dict:
    """Valores de las columnas propias del registro (FKs como *_id), sin
    campos many-to-many para no disparar consultas extra."""
    return {
        campo.attname: campo.value_from_object(instance)
        for campo in instance._meta.concrete_fields
        if campo.name not in CAMPOS_EXCLUIDOS
    }


def _sin_ignorados(foto: dict) -> dict:
    return {k: v for k, v in foto.items() if k not in CAMPOS_IGNORADOS_EN_CAMBIOS}


def _registrar(instance, accion: AccionAuditoria, anteriores=None, nuevos=None):
    usuario = obtener_usuario_actual()
    usuario_fk = usuario
    # Si un usuario se borra a sí mismo, la FK apuntaría a una fila que ya
    # no existe: se guarda solo el username.
    if (
        usuario is not None
        and accion == AccionAuditoria.DELETE
        and isinstance(instance, get_user_model())
        and instance.pk == usuario.pk
    ):
        usuario_fk = None

    HistorialModificacion.objects.create(
        tabla_afectada=instance._meta.label,
        registro_id=str(instance.pk),
        accion=accion.value,
        usuario=usuario_fk,
        usuario_username=usuario.username if usuario else "",
        datos_anteriores=anteriores,
        datos_nuevos=nuevos,
    )


def _antes_de_guardar(sender, instance, raw=False, **kwargs):
    instance._auditoria_anterior = None
    if raw or instance._state.adding or instance.pk is None:
        return
    anterior = sender._default_manager.filter(pk=instance.pk).first()
    if anterior is not None:
        instance._auditoria_anterior = _foto(anterior)


def _despues_de_guardar(sender, instance, created, raw=False, **kwargs):
    if raw:  # loaddata/fixtures: no es un cambio hecho por un usuario
        return
    nuevos = _foto(instance)
    if created:
        _registrar(instance, AccionAuditoria.INSERT, nuevos=nuevos)
        return
    anteriores = getattr(instance, "_auditoria_anterior", None)
    if anteriores is not None and _sin_ignorados(anteriores) == _sin_ignorados(nuevos):
        return
    _registrar(instance, AccionAuditoria.UPDATE, anteriores=anteriores, nuevos=nuevos)


def _despues_de_borrar(sender, instance, **kwargs):
    _registrar(instance, AccionAuditoria.DELETE, anteriores=_foto(instance))


for etiqueta in MODELOS_AUDITADOS:
    modelo = apps.get_model(etiqueta)
    uid = f"auditoria_{etiqueta}"
    pre_save.connect(_antes_de_guardar, sender=modelo, dispatch_uid=f"{uid}_pre_save")
    post_save.connect(_despues_de_guardar, sender=modelo, dispatch_uid=f"{uid}_post_save")
    post_delete.connect(_despues_de_borrar, sender=modelo, dispatch_uid=f"{uid}_post_delete")
