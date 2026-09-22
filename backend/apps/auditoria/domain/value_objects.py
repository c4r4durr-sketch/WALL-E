"""Value objects puros del dominio de auditoría."""

from enum import Enum


class AccionAuditoria(str, Enum):
    """HU13: qué le pasó al registro auditado."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
