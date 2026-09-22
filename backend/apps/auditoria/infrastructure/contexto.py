"""
Request en curso, guardado por interfaces/middleware.py para que los
signals de auditoría sepan quién hizo el cambio (equivalente al
`SET app.usuario_actual` que exigía el trigger SQL original).

Se guarda el request (no el usuario) porque con JWT el usuario todavía no
está autenticado cuando corre el middleware: DRF lo autentica después,
dentro de la vista, y en ese momento lo asigna también a este mismo
request. Cuando el signal lee `request.user` ya ve al usuario real.
"""

from contextvars import ContextVar

request_actual: ContextVar = ContextVar("request_actual", default=None)


def obtener_usuario_actual():
    """Usuario autenticado del request en curso, o None si el cambio no
    viene de un request (shell, migraciones, comandos) o es anónimo."""
    request = request_actual.get()
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return None
    return usuario
