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


# --- Promociones (HU23) ---


class PromocionNoPermitidaError(Exception):
    """Solo el Administrador crea o termina promociones."""


class PromocionNoEncontradaError(Exception):
    """No existe una promoción con ese id."""


class DatosPromocionInvalidosError(Exception):
    """Algún dato de la promoción no cumple una regla. `errores` mapea
    campo -> mensaje, para mostrarlo junto al campo."""

    def __init__(self, errores: dict[str, str]):
        super().__init__(errores)
        self.errores = errores


class PromocionNoAplicableError(Exception):
    """La herramienta no está estancada en esa sucursal, ya tiene una
    promoción vigente ahí, o la promoción ya no está vigente."""
