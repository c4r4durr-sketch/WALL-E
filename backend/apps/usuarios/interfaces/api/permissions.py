"""
Permisos DRF basados en el campo `rol` del usuario autenticado.

Viven en interfaces/api porque son un detalle de "cómo se expone la API"
(DRF), no una regla de negocio del dominio: la regla de negocio real
("solo un Administrador puede crear empleados", etc.) se aplicará dentro
del use_case correspondiente; estos permisos solo evitan que la petición
HTTP llegue a la vista si el rol no corresponde.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from ...domain.value_objects import Rol


class EsAdministrador(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.rol == Rol.ADMINISTRADOR.value)


class EsSupervisor(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.rol == Rol.SUPERVISOR.value)


class EsEmpleado(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.rol == Rol.EMPLEADO.value)


class LecturaParaTodosEscrituraAdministradorOSupervisor(BasePermission):
    """Cualquier usuario autenticado puede consultar (GET/HEAD/OPTIONS);
    crear, editar o borrar queda para Administrador y Supervisor. Un
    Empleado que intenta escribir recibe 403. (Se combina con
    IsAuthenticated, que va primero y responde 401 sin sesión.)"""

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.rol in {Rol.ADMINISTRADOR.value, Rol.SUPERVISOR.value}
        )


class EsAdministradorOSupervisor(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.rol in {Rol.ADMINISTRADOR.value, Rol.SUPERVISOR.value}
        )
