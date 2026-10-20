"""Value objects puros del dominio de auditoría."""

from enum import Enum


class AccionAuditoria(str, Enum):
    """HU13: qué le pasó al registro auditado."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# Campos que Django actualiza solo (auto_now, último login). Un UPDATE que
# solo cambia estos no se registra, y en una edición no se informan como
# "campos cambiados": no son cambios hechos por una persona.
CAMPOS_AUTOMATICOS = frozenset({"last_login", "actualizado_en"})
