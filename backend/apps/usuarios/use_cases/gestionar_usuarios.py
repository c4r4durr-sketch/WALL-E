"""
Casos de uso de cuentas de usuario (HU3, HU4, HU5): listar, crear, editar
(incluye desactivar) y restablecer la contraseña.

Puros: reciben los repositorios y el validador de contraseñas como
interfaces de domain/repositories.py, nunca el ORM. Reglas que viven acá:
  - solo el Administrador gestiona cuentas;
  - nombre de usuario válido y único (sin distinguir mayúsculas);
  - Supervisor y Empleado tienen una sucursal activa (HU5);
  - la contraseña cumple la política (ValidadorPassword) al crear, al
    editar y al restablecer; editar sin contraseña no la borra;
  - un Administrador no se desactiva ni se quita el rol a sí mismo, y el
    sistema nunca se queda sin un Administrador activo.
No se eliminan cuentas: quedan referenciadas por movimientos,
transferencias y el historial de auditoría; se desactivan.
"""

from dataclasses import replace
from typing import Any, Optional

from ..domain.entities import Actor, Usuario
from ..domain.exceptions import (
    DatosUsuarioInvalidosError,
    OperacionNoPermitidaError,
    PermisoDenegadoError,
    UsernameDuplicadoError,
    UsuarioNoEncontradoError,
)
from ..domain.reglas import errores_de_username, requiere_sucursal
from ..domain.repositories import SucursalRepository, UsuarioRepository, ValidadorPassword
from ..domain.value_objects import Rol

CAMPOS_EDITABLES = {"username", "nombres", "apellidos", "email", "rol", "sucursal_id", "activo"}


def _exigir_administrador(actor: Actor) -> None:
    if Rol(actor.rol) != Rol.ADMINISTRADOR:
        raise PermisoDenegadoError("Solo el Administrador puede gestionar cuentas.")


def _normalizar(usuario: Usuario) -> Usuario:
    return replace(
        usuario,
        username=usuario.username.strip(),
        nombres=usuario.nombres.strip(),
        apellidos=usuario.apellidos.strip(),
        email=usuario.email.strip(),
        rol=Rol(usuario.rol),
    )


def _validar(
    usuarios: UsuarioRepository, sucursales: SucursalRepository, usuario: Usuario
) -> None:
    errores: dict[str, list[str]] = {}

    mensajes_username = errores_de_username(usuario.username)
    if mensajes_username:
        errores["username"] = mensajes_username
    else:
        existente = usuarios.obtener_por_username(usuario.username)
        if existente is not None and existente.id != usuario.id:
            raise UsernameDuplicadoError(usuario.username)

    if requiere_sucursal(usuario.rol):
        if usuario.sucursal_id is None:
            errores["sucursal"] = ["Supervisor y Empleado deben tener una sucursal asignada."]
        else:
            sucursal = sucursales.obtener_por_id(usuario.sucursal_id)
            if sucursal is None or not sucursal.activa:
                errores["sucursal"] = ["La sucursal no existe o no está activa."]

    if errores:
        raise DatosUsuarioInvalidosError(errores)


def _validar_password(validador: ValidadorPassword, password: str, usuario: Usuario) -> None:
    mensajes = validador.errores(password, usuario)
    if mensajes:
        raise DatosUsuarioInvalidosError({"password": mensajes})


def listar_usuarios(actor: Actor, usuarios: UsuarioRepository) -> list[Usuario]:
    _exigir_administrador(actor)
    return usuarios.listar()


def obtener_usuario(actor: Actor, usuarios: UsuarioRepository, usuario_id: int) -> Usuario:
    _exigir_administrador(actor)
    usuario = usuarios.obtener_por_id(usuario_id)
    if usuario is None:
        raise UsuarioNoEncontradoError(usuario_id)
    return usuario


def crear_usuario(
    actor: Actor,
    usuarios: UsuarioRepository,
    sucursales: SucursalRepository,
    validador: ValidadorPassword,
    datos: dict[str, Any],
    password: Optional[str],
) -> Usuario:
    _exigir_administrador(actor)
    nuevo = _normalizar(Usuario(
        id=None,
        username=datos.get("username", ""),
        nombres=datos.get("nombres", ""),
        apellidos=datos.get("apellidos", ""),
        email=datos.get("email", ""),
        rol=datos.get("rol", Rol.EMPLEADO),
        sucursal_id=datos.get("sucursal_id"),
        activo=datos.get("activo", True),
    ))
    if not password:
        raise DatosUsuarioInvalidosError({"password": ["La contraseña es obligatoria."]})
    _validar(usuarios, sucursales, nuevo)
    _validar_password(validador, password, nuevo)
    return usuarios.crear(nuevo, password)


def actualizar_usuario(
    actor: Actor,
    usuarios: UsuarioRepository,
    sucursales: SucursalRepository,
    validador: ValidadorPassword,
    usuario_id: int,
    cambios: dict[str, Any],
    password: Optional[str] = None,
) -> Usuario:
    """Aplica solo los campos recibidos (PUT o PATCH) y valida el estado
    final de la cuenta. Si llega `password`, también la reemplaza; si no
    llega, la contraseña actual se conserva. La vista lo ejecuta dentro de
    una transacción: datos y contraseña se guardan juntos o ninguno."""
    actual = obtener_usuario(actor, usuarios, usuario_id)
    actualizado = _normalizar(replace(
        actual, **{campo: valor for campo, valor in cambios.items() if campo in CAMPOS_EDITABLES}
    ))
    # Un Administrador no tiene sucursal fija: si se le asigna el rol, se
    # le quita la sucursal en vez de dejar un dato que no aplica.
    if actualizado.rol == Rol.ADMINISTRADOR and "sucursal_id" not in cambios:
        actualizado = replace(actualizado, sucursal_id=None)

    _proteger_administradores(actor, usuarios, actual, actualizado)
    _validar(usuarios, sucursales, actualizado)
    if password:
        _validar_password(validador, password, actualizado)

    guardado = usuarios.actualizar(actualizado)
    if password:
        usuarios.establecer_password(usuario_id, password)
    return guardado


def restablecer_password(
    actor: Actor,
    usuarios: UsuarioRepository,
    validador: ValidadorPassword,
    usuario_id: int,
    password: str,
) -> None:
    """HU3: el Administrador asigna una contraseña nueva a una cuenta (por
    ejemplo, cuando el empleado la olvidó). La anterior deja de servir."""
    usuario = obtener_usuario(actor, usuarios, usuario_id)
    if not password:
        raise DatosUsuarioInvalidosError({"password": ["La contraseña es obligatoria."]})
    _validar_password(validador, password, usuario)
    usuarios.establecer_password(usuario_id, password)


def _proteger_administradores(
    actor: Actor, usuarios: UsuarioRepository, actual: Usuario, actualizado: Usuario
) -> None:
    deja_de_ser_admin_activo = (
        actual.rol == Rol.ADMINISTRADOR
        and actual.activo
        and (actualizado.rol != Rol.ADMINISTRADOR or not actualizado.activo)
    )
    if not deja_de_ser_admin_activo:
        return
    if actual.id == actor.usuario_id:
        raise OperacionNoPermitidaError(
            "No puedes desactivar tu propia cuenta ni quitarte el rol de Administrador."
        )
    if usuarios.contar_administradores_activos(excluir_id=actual.id) == 0:
        raise OperacionNoPermitidaError("Debe quedar al menos un Administrador activo.")
