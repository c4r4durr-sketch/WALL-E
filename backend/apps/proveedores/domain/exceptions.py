"""
Excepciones de negocio de proveedores. Las lanzan los use_cases; la vista
las traduce a la respuesta HTTP que corresponda.
"""


class ProveedorNoEncontradoError(Exception):
    """No existe un proveedor con ese id."""


class NombreProveedorDuplicadoError(Exception):
    """Ya existe otro proveedor con ese nombre (sin distinguir mayúsculas)."""


class ProveedorEnUsoError(Exception):
    """No se puede eliminar: tiene herramientas asociadas. Se desactiva."""


class PermisoDenegadoError(Exception):
    """Solo el Administrador registra, edita o elimina proveedores."""


class DatosProveedorInvalidosError(Exception):
    """Algún dato no cumple una regla de negocio. `errores` mapea
    campo -> mensaje, para mostrarlo junto al campo."""

    def __init__(self, errores: dict[str, str]):
        super().__init__(errores)
        self.errores = errores
