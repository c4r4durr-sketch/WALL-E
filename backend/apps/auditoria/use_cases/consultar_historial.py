"""
Casos de uso de consulta del historial de modificaciones (HU13): búsqueda
paginada con filtros y las opciones para armar esos filtros.

Puros: reciben el repositorio como interfaz. Reglas que viven acá:
  - solo Administrador y Supervisor consultan (el historial es oculto
    para el Empleado);
  - `desde` no puede ser posterior a `hasta`;
  - páginas de TAMANO_PAGINA registros (máximo TAMANO_MAXIMO);
  - en una edición se informa qué campos cambiaron.
El historial es de solo lectura: no hay casos de uso para modificarlo.
"""

from dataclasses import replace

from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol

from ..domain.entities import FiltroHistorial, OpcionFiltro, PaginaHistorial, RegistroHistorial
from ..domain.exceptions import ConsultaNoPermitidaError, FiltroInvalidoError
from ..domain.repositories import HistorialRepository
from ..domain.value_objects import CAMPOS_AUTOMATICOS, AccionAuditoria, OrigenHistorial

TAMANO_PAGINA = 25
TAMANO_MAXIMO = 100
ROLES_CON_ACCESO = frozenset({Rol.ADMINISTRADOR, Rol.SUPERVISOR})
ETIQUETA_ACCION = {
    AccionAuditoria.INSERT: "Alta",
    AccionAuditoria.UPDATE: "Edición",
    AccionAuditoria.DELETE: "Baja",
}
ETIQUETA_ORIGEN = {
    OrigenHistorial.USUARIOS: "Usuarios",
    OrigenHistorial.COMANDOS: "Comandos (cargar_demo y otros)",
}


def _exigir_acceso(actor: Actor) -> None:
    if Rol(actor.rol) not in ROLES_CON_ACCESO:
        raise ConsultaNoPermitidaError()


def campos_cambiados(registro: RegistroHistorial) -> tuple[str, ...]:
    """Campos cuyo valor difiere entre antes y después (solo ediciones),
    sin contar los que Django actualiza solo."""
    if registro.accion != AccionAuditoria.UPDATE:
        return ()
    antes = registro.datos_anteriores or {}
    despues = registro.datos_nuevos or {}
    return tuple(sorted(
        c for c in (antes.keys() | despues.keys()) - CAMPOS_AUTOMATICOS if antes.get(c) != despues.get(c)
    ))


def consultar_historial(
    repo: HistorialRepository,
    actor: Actor,
    filtro: FiltroHistorial,
    pagina: int = 1,
    tamano: int = TAMANO_PAGINA,
) -> PaginaHistorial:
    _exigir_acceso(actor)
    if filtro.desde and filtro.hasta and filtro.desde > filtro.hasta:
        raise FiltroInvalidoError({"desde": "La fecha inicial no puede ser posterior a la final."})
    pagina = max(1, pagina)
    tamano = min(max(1, tamano), TAMANO_MAXIMO)
    total, registros = repo.buscar(filtro, desde=(pagina - 1) * tamano, limite=tamano)
    return PaginaHistorial(
        total=total,
        pagina=pagina,
        tamano=tamano,
        resultados=tuple(replace(r, campos_cambiados=campos_cambiados(r)) for r in registros),
    )


def opciones_de_filtro(repo: HistorialRepository, actor: Actor) -> dict[str, list[OpcionFiltro]]:
    _exigir_acceso(actor)
    return {
        "tablas": repo.tablas(),
        "usuarios": repo.autores(),
        "acciones": [OpcionFiltro(a.value, ETIQUETA_ACCION[a]) for a in AccionAuditoria],
        "origenes": [OpcionFiltro(o.value, ETIQUETA_ORIGEN[o]) for o in OrigenHistorial],
    }
