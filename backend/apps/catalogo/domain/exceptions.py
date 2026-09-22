"""
Excepciones de negocio del catálogo. Las lanzan los use_cases (o el
repositorio, cuando la base detecta la violación); la vista las traduce a
la respuesta HTTP que corresponda.
"""


class HerramientaNoEncontradaError(Exception):
    """No existe una herramienta con ese id."""


class CodigoDuplicadoError(Exception):
    """Ya existe otra herramienta con el mismo código de caja."""


class HerramientaEnUsoError(Exception):
    """No se puede eliminar: tiene movimientos o transferencias registrados
    (borrarla dejaría el historial de stock inconsistente)."""


class DatosHerramientaInvalidosError(Exception):
    """Algún dato de la herramienta no cumple una regla de negocio.
    `errores` mapea campo -> mensaje, para mostrarlo junto al campo."""

    def __init__(self, errores: dict[str, str]):
        super().__init__(errores)
        self.errores = errores
