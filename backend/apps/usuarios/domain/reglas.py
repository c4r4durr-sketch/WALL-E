"""
Reglas de negocio puras del dominio de usuarios (sin Django).

HU5: todo Supervisor y todo Empleado trabaja en una sucursal fija, así que
su cuenta no puede quedar sin sucursal. El Administrador es global y es el
único rol que puede no tenerla. (Era la constraint chk_sucursal_obligatoria
del script SQL descartado.)
"""

import re

from .value_objects import Rol

ROLES_CON_SUCURSAL_OBLIGATORIA = frozenset({Rol.SUPERVISOR, Rol.EMPLEADO})


def requiere_sucursal(rol: str) -> bool:
    return Rol(rol) in ROLES_CON_SUCURSAL_OBLIGATORIA


# Mismos caracteres que acepta el username de Django (letras, números y
# @ . + - _), sin espacios; mínimo 3 para que no haya cuentas tipo "a".
USERNAME_LARGO_MINIMO = 3
USERNAME_LARGO_MAXIMO = 150
_USERNAME_VALIDO = re.compile(r"^[\w.@+-]+$")


def errores_de_username(username: str) -> list[str]:
    if not username:
        return ["El nombre de usuario es obligatorio."]
    if len(username) < USERNAME_LARGO_MINIMO:
        return [f"Debe tener al menos {USERNAME_LARGO_MINIMO} caracteres."]
    if len(username) > USERNAME_LARGO_MAXIMO:
        return [f"No puede tener más de {USERNAME_LARGO_MAXIMO} caracteres."]
    if not _USERNAME_VALIDO.match(username):
        return ["Solo letras, números y los símbolos @ . + - _ (sin espacios)."]
    return []
