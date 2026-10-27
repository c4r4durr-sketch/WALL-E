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


class ActualizacionNoPermitidaError(Exception):
    """HU21: solo el Administrador o el Supervisor cambian datos del catálogo."""


class SinVentasObservadasError(Exception):
    """HU21: sin ventas en el período no hay demanda observada con la que
    reemplazar la estimada (con D = 0 el EOQ no tiene sentido)."""
