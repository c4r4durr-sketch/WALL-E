from rest_framework import serializers

# Reportes estadísticos (/api/indicadores/estadisticas/...). Serializers
# planos de los DTOs de domain/estadisticas.py. Los montos van como texto
# (DecimalField), igual que el resto de la API; los meses como "AAAA-MM".

_MONTO = {"max_digits": 18, "decimal_places": 2}


class FiltroEstadisticasSerializer(serializers.Serializer):
    # Sin fechas: los últimos 12 meses. Sin sucursal: todas (Administrador)
    # o la propia (Supervisor). Que no sean futuras ni "hasta" < "desde" lo
    # revisa el caso de uso.
    desde = serializers.DateField(required=False)
    hasta = serializers.DateField(required=False)
    sucursal = serializers.IntegerField(min_value=1, required=False)


class PeriodoSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    sucursal_id = serializers.IntegerField(allow_null=True)


class _Mes(serializers.DateField):
    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m", **kwargs)


class MovimientosMesSerializer(serializers.Serializer):
    mes = _Mes()
    entradas = serializers.IntegerField()
    salidas = serializers.IntegerField()
    ajustes_positivos = serializers.IntegerField()
    ajustes_negativos = serializers.IntegerField()


class MovimientosPorMesSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    meses = MovimientosMesSerializer(many=True)


class VentaHerramientaSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    unidades = serializers.IntegerField()
    monto = serializers.DecimalField(**_MONTO, allow_null=True)


class TopHerramientasSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    herramientas = VentaHerramientaSerializer(many=True)


class StockSucursalSerializer(serializers.Serializer):
    sucursal_id = serializers.IntegerField()
    nombre = serializers.CharField()
    unidades = serializers.IntegerField()
    valor = serializers.DecimalField(**_MONTO)
    unidades_sin_costo = serializers.IntegerField()


class StockPorSucursalSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    sucursales = StockSucursalSerializer(many=True)
    total_unidades = serializers.IntegerField()
    total_valor = serializers.DecimalField(**_MONTO)


class TotalClaseSerializer(serializers.Serializer):
    clase = serializers.CharField()
    herramientas = serializers.IntegerField()
    valor = serializers.DecimalField(**_MONTO)
    porcentaje_valor = serializers.FloatField()


class PuntoParetoSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    valor = serializers.DecimalField(**_MONTO)
    porcentaje = serializers.FloatField()
    porcentaje_acumulado = serializers.FloatField()
    clase = serializers.CharField()


class EstadisticaABCSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    clases = TotalClaseSerializer(many=True)
    pareto = PuntoParetoSerializer(many=True)
    valor_total = serializers.DecimalField(**_MONTO)
    herramientas_sin_costo = serializers.IntegerField()


class TramoValorSerializer(serializers.Serializer):
    tramo = serializers.CharField()
    herramientas = serializers.IntegerField()
    unidades = serializers.IntegerField()
    valor = serializers.DecimalField(**_MONTO)


class AntiguedadPorTramoSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    tramos = TramoValorSerializer(many=True)
    valor_total = serializers.DecimalField(**_MONTO)
    lineas_sin_costo = serializers.IntegerField()


class CantidadEstadoSerializer(serializers.Serializer):
    estado = serializers.CharField()
    cantidad = serializers.IntegerField()


class TransferenciasMesSerializer(serializers.Serializer):
    mes = _Mes()
    pendientes = serializers.IntegerField()
    completadas = serializers.IntegerField()
    rechazadas = serializers.IntegerField()


class EstadisticaTransferenciasSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    por_estado = CantidadEstadoSerializer(many=True)
    por_mes = TransferenciasMesSerializer(many=True)
    total = serializers.IntegerField()


class ResumenEstadisticoSerializer(serializers.Serializer):
    periodo = PeriodoSerializer()
    total_movimientos = serializers.IntegerField()
    unidades_vendidas = serializers.IntegerField()
    valor_inventario = serializers.DecimalField(**_MONTO)
    alertas_reorden = serializers.IntegerField()
    herramientas_estancadas = serializers.IntegerField()
