"""Value objects puros del dominio de auditoría."""

from enum import Enum


class AccionAuditoria(str, Enum):
    """HU13: qué le pasó al registro auditado."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class OrigenHistorial(str, Enum):
    """Quién originó el cambio: un usuario desde la aplicación, o un
    comando (cargar_demo, createsuperuser, la consola), que no tiene
    usuario."""

    USUARIOS = "USUARIOS"
    COMANDOS = "COMANDOS"


# Nombre con el que firma sus registros el comando cargar_demo (en la
# columna del nombre de usuario; la FK al usuario queda en NULL). Los
# registros de otros comandos van sin nombre.
AUTOR_CARGAR_DEMO = "cargar_demo"
AUTORES_DE_COMANDOS = frozenset({"", AUTOR_CARGAR_DEMO})


# Campos que Django actualiza solo (auto_now, último login). Un UPDATE que
# solo cambia estos no se registra, y en una edición no se informan como
# "campos cambiados": no son cambios hechos por una persona.
CAMPOS_AUTOMATICOS = frozenset({"last_login", "actualizado_en"})
