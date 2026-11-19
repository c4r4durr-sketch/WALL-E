"""
Reglas de negocio puras del dominio de usuarios (sin Django).

HU5: todo Supervisor y todo Empleado trabaja en una sucursal fija, así que
su cuenta no puede quedar sin sucursal. El Administrador es global y es el
único rol que puede no tenerla. (Era la constraint chk_sucursal_obligatoria
del script SQL descartado.)
"""

from .value_objects import Rol

ROLES_CON_SUCURSAL_OBLIGATORIA = frozenset({Rol.SUPERVISOR, Rol.EMPLEADO})


def requiere_sucursal(rol: str) -> bool:
    return Rol(rol) in ROLES_CON_SUCURSAL_OBLIGATORIA


# El formato del usuario (3 a 30 caracteres, letras sin tildes, números,
# punto, guion y guion bajo) y el de los nombres están en
# apps/comun/reglas.py, compartidos con el resto de los formularios.
