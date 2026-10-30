"""
Implementaciones concretas de los repositorios de domain/repositories.py,
usando el ORM de Django. Son el único lugar del proyecto que debería
mezclar "modelo ORM" con "entidad de dominio" (hacen la conversión entre
ambos mundos). Guardan con .save() por instancia para que se disparen los
signals de auditoría (HU13).
"""

from typing import Optional

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction

from ..domain.entities import Sucursal, Usuario
from ..domain.exceptions import UsernameDuplicadoError
from ..domain.repositories import SucursalRepository, UsuarioRepository, ValidadorPassword
from ..domain.value_objects import Rol
from .models import Sucursal as SucursalModel
from .models import Usuario as UsuarioModel


def _usuario_a_entidad(modelo: UsuarioModel) -> Usuario:
    return Usuario(
        id=modelo.id,
        username=modelo.username,
        nombres=modelo.first_name,
        apellidos=modelo.last_name,
        email=modelo.email,
        rol=Rol(modelo.rol),
        sucursal_id=modelo.sucursal_id,
        activo=modelo.is_active,
        sucursal_nombre=modelo.sucursal.nombre if modelo.sucursal_id else None,
    )


def _copiar_a_modelo(usuario: Usuario, modelo: UsuarioModel) -> None:
    modelo.username = usuario.username
    modelo.first_name = usuario.nombres
    modelo.last_name = usuario.apellidos
    modelo.email = usuario.email
    modelo.rol = Rol(usuario.rol).value
    modelo.sucursal_id = usuario.sucursal_id
    modelo.is_active = usuario.activo


def _guardar(modelo: UsuarioModel) -> None:
    try:
        # atomic: si la base rechaza el username (dos altas simultáneas),
        # no deja rota la transacción del request.
        with transaction.atomic():
            modelo.save()
    except IntegrityError as error:
        if "nombre_usuario" not in str(error) and "username" not in str(error):
            raise
        raise UsernameDuplicadoError(modelo.username) from error


class UsuarioRepositoryDjango(UsuarioRepository):
    def _consulta(self):
        # select_related: el nombre de la sucursal sale en la misma consulta
        # (sin una consulta extra por usuario al listar).
        return UsuarioModel.objects.select_related("sucursal")

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        modelo = self._consulta().filter(pk=usuario_id).first()
        return _usuario_a_entidad(modelo) if modelo else None

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        modelo = self._consulta().filter(username__iexact=username).first()
        return _usuario_a_entidad(modelo) if modelo else None

    def listar(self) -> list[Usuario]:
        return [_usuario_a_entidad(m) for m in self._consulta().order_by("username")]

    def crear(self, usuario: Usuario, password: str) -> Usuario:
        modelo = UsuarioModel()
        _copiar_a_modelo(usuario, modelo)
        modelo.set_password(password)
        _guardar(modelo)
        return self.obtener_por_id(modelo.id)

    def actualizar(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel.objects.get(pk=usuario.id)
        _copiar_a_modelo(usuario, modelo)
        _guardar(modelo)
        return self.obtener_por_id(modelo.id)

    def establecer_password(self, usuario_id: int, password: str) -> None:
        modelo = UsuarioModel.objects.get(pk=usuario_id)
        modelo.set_password(password)
        modelo.save(update_fields=["password"])

    def contar_administradores_activos(self, excluir_id: Optional[int] = None) -> int:
        consulta = UsuarioModel.objects.filter(rol=Rol.ADMINISTRADOR.value, is_active=True)
        if excluir_id is not None:
            consulta = consulta.exclude(pk=excluir_id)
        return consulta.count()


class ValidadorPasswordDjango(ValidadorPassword):
    """Aplica AUTH_PASSWORD_VALIDATORS de settings (largo mínimo, comunes,
    solo números, parecida a los datos del usuario). Los mensajes salen en
    español por LANGUAGE_CODE = "es". Compara contra un Usuario ORM en
    memoria, sin guardarlo."""

    def errores(self, password: str, usuario: Usuario) -> list[str]:
        modelo = UsuarioModel()
        _copiar_a_modelo(usuario, modelo)
        try:
            validate_password(password, user=modelo)
        except DjangoValidationError as error:
            return list(error.messages)
        return []


def _sucursal_a_entidad(modelo: SucursalModel) -> Sucursal:
    return Sucursal(
        id=modelo.id, nombre=modelo.nombre, direccion=modelo.direccion, activa=modelo.activa
    )


class SucursalRepositoryDjango(SucursalRepository):
    # Implementado (solo lectura) en el paso 4.3: movimientos lo necesita
    # para validar la sucursal y mostrar el stock por sucursal.
    def obtener_por_id(self, sucursal_id: int) -> Optional[Sucursal]:
        modelo = SucursalModel.objects.filter(pk=sucursal_id).first()
        return _sucursal_a_entidad(modelo) if modelo else None

    def listar(self) -> list[Sucursal]:
        return [_sucursal_a_entidad(m) for m in SucursalModel.objects.order_by("id")]
