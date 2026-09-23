"""
Excepciones de negocio de transferencias. Las de stock, herramienta y
sucursal se reutilizan de apps.movimientos.domain.exceptions (misma regla,
un solo lugar); acá solo las propias del flujo de transferencia.
"""


class TransferenciaNoEncontradaError(Exception):
    """No existe una transferencia con ese id."""


class MismaSucursalError(Exception):
    """Origen y destino son la misma sucursal."""


class TransferenciaYaResueltaError(Exception):
    """Solo una transferencia PENDIENTE se puede completar o rechazar."""

    def __init__(self, estado: str):
        super().__init__(estado)
        self.estado = estado


class ResolucionNoPermitidaError(Exception):
    """Solo Administrador y Supervisor completan o rechazan transferencias."""


class MotivoRechazoObligatorioError(Exception):
    """Rechazar una transferencia exige explicar por qué."""
