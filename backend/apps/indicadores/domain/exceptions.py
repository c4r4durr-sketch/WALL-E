"""
Excepciones de negocio de indicadores y reportes. Las lanzan los
use_cases; la vista las traduce a la respuesta HTTP que corresponda.
"""


class ReporteNoPermitidoError(Exception):
    """El rol del actor no puede ver este reporte, o no para esa sucursal."""


class SucursalInexistenteError(Exception):
    """El reporte pide una sucursal que no existe."""


class FechaFuturaError(Exception):
    """El reporte pide un día que todavía no ocurrió."""
