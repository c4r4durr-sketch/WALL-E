"""
Excepciones de negocio de auditoría. Las lanzan los use_cases; la vista
las traduce a la respuesta HTTP que corresponda.
"""


class ConsultaNoPermitidaError(Exception):
    """Solo el Administrador y el Supervisor consultan el historial."""


class FiltroInvalidoError(Exception):
    """El filtro no tiene sentido (por ejemplo, `desde` posterior a
    `hasta`). `errores` mapea campo -> mensaje."""

    def __init__(self, errores: dict[str, str]):
        super().__init__(errores)
        self.errores = errores
