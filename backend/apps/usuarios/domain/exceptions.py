"""
Excepciones de negocio de usuarios. Las lanzan los use_cases; la vista las
traduce a la respuesta HTTP que corresponda.
"""


class UsuarioNoEncontradoError(Exception):
    """No existe un usuario con ese id."""


class UsernameDuplicadoError(Exception):
    """Ya existe otra cuenta con ese nombre de usuario."""


class PermisoDenegadoError(Exception):
    """El rol del actor no puede ejecutar esta operación."""


class OperacionNoPermitidaError(Exception):
    """La operación dejaría al sistema en un estado inválido: un
    Administrador que se desactiva o se quita el rol a sí mismo, o que deja
    al sistema sin ningún Administrador activo."""


class DatosUsuarioInvalidosError(Exception):
    """Algún dato no cumple una regla de negocio. `errores` mapea
    campo -> lista de mensajes, para mostrarlos junto a cada campo."""

    def __init__(self, errores: dict[str, list[str]]):
        super().__init__(errores)
        self.errores = errores
