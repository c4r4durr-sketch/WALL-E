"""
Casos de uso de movimientos (ver registrar_movimiento.py): registrar
entrada/salida con conversión caja->unidad y validación de stock, y
consultar stock e historial.

calcular el stock disponible vive en domain/stock.py y en
registrar_movimiento._stock_actual para que transferencias (validar stock
en origen) e indicadores (rotación para ABC) lo reutilicen en vez de
copiarlo.
"""
