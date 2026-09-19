"""
Casos de uso de transferencias (ej: crear_transferencia).

Va a depender de MovimientoRepository (apps.movimientos.domain.repositories)
para calcular el stock disponible en la sucursal origen y lanzar
StockInsuficienteError (apps.movimientos.domain.exceptions) si no alcanza,
en vez de reimplementar esa validación acá.

Sin implementar todavía (solo el esqueleto).
"""
