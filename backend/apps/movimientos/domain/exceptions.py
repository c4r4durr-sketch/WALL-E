"""
Excepciones de dominio. Son tipos, no lógica: quién las lanza (y cuándo) lo
decide un use_case, no esta clase.

StockInsuficienteError vive acá (y no en transferencias) porque "stock
disponible en una sucursal" se calcula a partir de movimientos; el módulo
de transferencias la reutiliza en vez de duplicarla.
"""


class StockInsuficienteError(Exception):
    """Se lanzará cuando un use_case intente registrar una salida o una
    transferencia por más cantidad de la disponible en la sucursal origen."""
