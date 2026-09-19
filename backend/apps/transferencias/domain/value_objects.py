from enum import Enum


class EstadoTransferencia(str, Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    RECHAZADA = "RECHAZADA"
