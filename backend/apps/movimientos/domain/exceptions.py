"""
Excepciones de dominio de movimientos. Las lanzan los use_cases; la vista
las traduce a la respuesta HTTP que corresponda.

StockInsuficienteError vive acá (y no en transferencias) porque "stock
disponible en una sucursal" se calcula a partir de movimientos; el módulo
de transferencias la reutiliza en vez de duplicarla.
"""


class StockInsuficienteError(Exception):
    """Una salida (o transferencia) pide más unidades de las disponibles en
    la sucursal. Nunca se deja el stock en negativo."""

    def __init__(self, disponible: int, solicitado: int):
        super().__init__(f"Stock insuficiente: disponible {disponible}, solicitado {solicitado}.")
        self.disponible = disponible
        self.solicitado = solicitado


class HerramientaInexistenteError(Exception):
    """El movimiento referencia una herramienta que no existe."""


class SucursalInvalidaError(Exception):
    """El movimiento referencia una sucursal que no existe o está inactiva."""


class AjusteNoPermitidoError(Exception):
    """Solo Administrador y Supervisor pueden registrar ajustes de stock."""


class MotivoObligatorioError(Exception):
    """Todo ajuste de stock debe explicar por qué se hace (auditoría)."""


class SucursalNoPermitidaError(Exception):
    """El usuario intenta registrar un movimiento en una sucursal que no es
    la suya (un Empleado solo opera en su propio mostrador)."""
