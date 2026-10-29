from rest_framework import serializers

# Serializers "planos" (no ModelSerializer): indicadores no tiene modelos
# propios, así que estos serializan los DTOs de domain/entities.py, no un
# modelo ORM.


class ResultadoEOQSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    demanda_anual = serializers.IntegerField(allow_null=True)
    costo_pedido = serializers.FloatField(allow_null=True)
    costo_almacenamiento_unitario = serializers.FloatField(allow_null=True)
    unidades_por_caja = serializers.IntegerField()
    eoq = serializers.FloatField(allow_null=True)
    eoq_ajustado_cajas = serializers.FloatField(allow_null=True)
    demanda_observada = serializers.IntegerField()
    demanda_usada = serializers.IntegerField(allow_null=True)
    fuente_demanda = serializers.CharField()
    datos_faltantes = serializers.ListField(child=serializers.CharField())


class ResultadoROPSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    demanda_anual = serializers.IntegerField(allow_null=True)
    demanda_observada = serializers.IntegerField()
    demanda_usada = serializers.IntegerField(allow_null=True)
    fuente_demanda = serializers.CharField()
    demanda_diaria_promedio = serializers.FloatField(allow_null=True)
    lead_time_dias = serializers.IntegerField(allow_null=True)
    punto_reorden = serializers.FloatField(allow_null=True)
    stock_total = serializers.IntegerField()
    requiere_reorden = serializers.BooleanField()
    datos_faltantes = serializers.ListField(child=serializers.CharField())


class ClasificacionABCSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    unidades_vendidas = serializers.IntegerField()
    porcentaje = serializers.FloatField()
    porcentaje_acumulado = serializers.FloatField()
    clase = serializers.CharField()


class AlertaReordenSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    stock_total = serializers.IntegerField()
    punto_reorden = serializers.FloatField()
    pedido_sugerido = serializers.FloatField(allow_null=True)
    unidades_por_caja = serializers.IntegerField()


class HerramientaEstancadaSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    sucursal_id = serializers.IntegerField()
    sucursal_nombre = serializers.CharField()
    stock = serializers.IntegerField()
    dias_sin_venta = serializers.IntegerField()
    nunca_vendida = serializers.BooleanField()


class PanelAuditoriaSerializer(serializers.Serializer):
    total_alertas_stock = serializers.IntegerField()
    total_herramientas_estancadas = serializers.IntegerField()
    total_herramientas = serializers.IntegerField()
    total_sucursales_activas = serializers.IntegerField()
    herramientas_sin_datos_rop = serializers.IntegerField()
    dias_para_estancamiento = serializers.IntegerField()
    alertas = AlertaReordenSerializer(many=True)
    estancadas = HerramientaEstancadaSerializer(many=True)


# --- Cierre diario (HU14) ---


class FiltroCierreDiarioSerializer(serializers.Serializer):
    # Opcional para el Supervisor (se usa su sucursal); el Administrador
    # debe indicarla. Sin fecha, es el día de hoy (hora de La Paz).
    sucursal = serializers.IntegerField(min_value=1, required=False)
    fecha = serializers.DateField(required=False)


class LineaCierreSerializer(serializers.Serializer):
    movimiento_id = serializers.IntegerField()
    fecha_hora = serializers.DateTimeField()
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    tipo_movimiento = serializers.CharField()
    tipo_unidad = serializers.CharField()
    cantidad = serializers.IntegerField()
    cantidad_unidades = serializers.IntegerField()
    usuario = serializers.CharField()
    motivo = serializers.CharField()


class TotalPorTipoSerializer(serializers.Serializer):
    tipo_movimiento = serializers.CharField()
    movimientos = serializers.IntegerField()
    unidades = serializers.IntegerField()


class CierreDiarioSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    sucursal_id = serializers.IntegerField()
    sucursal_nombre = serializers.CharField()
    lineas = LineaCierreSerializer(many=True)
    totales = TotalPorTipoSerializer(many=True)
    total_salidas_unidades = serializers.IntegerField()
    cantidad_salidas = serializers.IntegerField()


# --- Reporte de antigüedad (HU22) ---


class FiltroAntiguedadSerializer(serializers.Serializer):
    # Sin sucursal: el Administrador ve todas; el Supervisor, la suya.
    sucursal = serializers.IntegerField(min_value=1, required=False)
    dias_minimos = serializers.IntegerField(min_value=0, required=False, default=0)


class LineaAntiguedadSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    sucursal_id = serializers.IntegerField()
    sucursal_nombre = serializers.CharField()
    stock = serializers.IntegerField()
    ultima_venta = serializers.DateTimeField(allow_null=True)
    dias_sin_venta = serializers.IntegerField()
    nunca_vendida = serializers.BooleanField()
    tramo = serializers.CharField()
    estancada = serializers.BooleanField()
    costo_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    valor_inmovilizado = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)


class TotalTramoSerializer(serializers.Serializer):
    tramo = serializers.CharField()
    lineas = serializers.IntegerField()
    unidades = serializers.IntegerField()


class ReporteAntiguedadSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    sucursal_id = serializers.IntegerField(allow_null=True)
    dias_minimos = serializers.IntegerField()
    dias_para_estancamiento = serializers.IntegerField()
    lineas = LineaAntiguedadSerializer(many=True)
    tramos = TotalTramoSerializer(many=True)
    total_unidades = serializers.IntegerField()
    total_estancadas = serializers.IntegerField()
    valor_inmovilizado_estancado = serializers.DecimalField(max_digits=14, decimal_places=2)
    lineas_sin_costo = serializers.IntegerField()


# --- Promociones (HU23) ---


class CrearPromocionSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField(min_value=1)
    sucursal_id = serializers.IntegerField(min_value=1)
    descuento_porcentaje = serializers.IntegerField()
    fecha_fin = serializers.DateField()
    motivo = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class FiltroPromocionesSerializer(serializers.Serializer):
    vigentes = serializers.BooleanField(required=False, default=False)


class PromocionSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="promocion.id")
    herramienta_id = serializers.IntegerField(source="promocion.herramienta_id")
    herramienta_codigo = serializers.CharField(source="promocion.herramienta_codigo")
    herramienta_nombre = serializers.CharField(source="promocion.herramienta_nombre")
    sucursal_id = serializers.IntegerField(source="promocion.sucursal_id")
    sucursal_nombre = serializers.CharField(source="promocion.sucursal_nombre")
    descuento_porcentaje = serializers.IntegerField(source="promocion.descuento_porcentaje")
    fecha_inicio = serializers.DateField(source="promocion.fecha_inicio")
    fecha_fin = serializers.DateField(source="promocion.fecha_fin")
    motivo = serializers.CharField(source="promocion.motivo")
    usuario = serializers.CharField(source="promocion.usuario_username")
    creado_en = serializers.DateTimeField(source="promocion.creado_en")
    estado = serializers.CharField()
