"""Implementación concreta (ORM) del repositorio de historial, de solo
lectura. Único lugar de auditoría que traduce entre el modelo ORM y la
entidad de dominio."""

from django.apps import apps
from django.db.models import Q

from ..domain.entities import FiltroHistorial, OpcionFiltro, RegistroHistorial
from ..domain.repositories import HistorialRepository
from ..domain.value_objects import AUTORES_DE_COMANDOS, AccionAuditoria, OrigenHistorial
from .models import HistorialModificacion


def _nombre_de_tabla(etiqueta: str) -> str:
    """'catalogo.Herramienta' -> 'Herramientas' (verbose_name_plural del
    modelo). Si el modelo ya no existe, se muestra la etiqueta tal cual."""
    try:
        return str(apps.get_model(etiqueta)._meta.verbose_name_plural).capitalize()
    except (LookupError, ValueError):
        return etiqueta


def _a_entidad(modelo: HistorialModificacion) -> RegistroHistorial:
    return RegistroHistorial(
        id=modelo.id,
        fecha=modelo.fecha,
        tabla=modelo.tabla_afectada,
        tabla_nombre=_nombre_de_tabla(modelo.tabla_afectada),
        registro_id=modelo.registro_id,
        accion=AccionAuditoria(modelo.accion),
        usuario_id=modelo.usuario_id,
        usuario_username=modelo.usuario_username,
        datos_anteriores=modelo.datos_anteriores,
        datos_nuevos=modelo.datos_nuevos,
    )


class HistorialRepositoryDjango(HistorialRepository):
    def buscar(self, filtro: FiltroHistorial, desde: int, limite: int) -> tuple[int, list[RegistroHistorial]]:
        condiciones = Q()
        # fecha__date compara en TIME_ZONE (La Paz), no en UTC; usa el
        # índice por fecha.
        if filtro.desde:
            condiciones &= Q(fecha__date__gte=filtro.desde)
        if filtro.hasta:
            condiciones &= Q(fecha__date__lte=filtro.hasta)
        if filtro.usuario_id is not None:
            condiciones &= Q(usuario_id=filtro.usuario_id)
        if filtro.tabla:
            condiciones &= Q(tabla_afectada=filtro.tabla)
        if filtro.accion:
            condiciones &= Q(accion=AccionAuditoria(filtro.accion).value)
        if filtro.origen:
            # Sin usuario y sin nombre (o firmado por cargar_demo). Un
            # usuario borrado también deja la FK en NULL, pero conserva su
            # nombre: sigue contando como cambio de un usuario.
            de_comandos = Q(usuario__isnull=True, usuario_username__in=AUTORES_DE_COMANDOS)
            condiciones &= de_comandos if filtro.origen == OrigenHistorial.COMANDOS else ~de_comandos
        consulta = HistorialModificacion.objects.filter(condiciones).order_by("-fecha", "-id")
        total = consulta.count()
        return total, [_a_entidad(m) for m in consulta[desde:desde + limite]]

    def tablas(self) -> list[OpcionFiltro]:
        # order_by() vacío: el orden por defecto del modelo (-fecha) entraría
        # en el SELECT DISTINCT y repetiría cada tabla una vez por fecha.
        etiquetas = HistorialModificacion.objects.order_by().values_list("tabla_afectada", flat=True).distinct()
        return sorted(
            (OpcionFiltro(e, _nombre_de_tabla(e)) for e in etiquetas), key=lambda o: o.texto
        )

    def autores(self) -> list[OpcionFiltro]:
        filas = (
            HistorialModificacion.objects.filter(usuario__isnull=False)
            .values_list("usuario_id", "usuario__username")
            .distinct()
            .order_by("usuario__username")
        )
        return [OpcionFiltro(str(usuario_id), username) for usuario_id, username in filas]
