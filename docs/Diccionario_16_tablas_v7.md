# Diccionario de datos — diseño v7 (16 tablas)

Solo referencia: NO ejecutar SQL con DROP SCHEMA sobre la base del sistema.


## sucursales
Sucursales fisicas de Walle-Importaciones (actualmente 2)

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_sucursal | varchar(8) | No | PK | Código automático |
| nombre_sucursal | varchar(100) | No | Único | — |
| direccion_sucursal | varchar(255) | Sí | — | — |
| telefono_sucursal | varchar(30) | Sí | — | — |
| estado_sucursal | boolean | No | — | Por defecto true |
| fecha_registro_sucursal | timestamp | No | — | Por defecto now |

## usuarios
Cuentas del sistema; solo el Administrador puede crearlas (HU4)

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_usuario | varchar(8) | No | PK | Código automático |
| nombres_usuario | varchar(100) | No | — | — |
| apellido_paterno_usuario | varchar(100) | No | — | — |
| apellido_materno_usuario | varchar(100) | Sí | — | — |
| nombre_usuario | varchar(50) | No | Único | — |
| contrasena_usuario | varchar(255) | No | — | — |
| rol_usuario | varchar(15) | No | — | Valores: ADMINISTRADOR, SUPERVISOR, EMPLEADO |
| cod_sucursal | varchar(8) | Sí | FK → sucursales | — |
| estado_usuario | boolean | No | — | Por defecto true |
| cod_usuario_creador | varchar(8) | Sí | FK → usuarios | — |
| fecha_registro_usuario | timestamp | No | — | Por defecto now |
| fecha_actualizacion_usuario | timestamp | No | — | Por defecto now |

## sesiones_usuario
HU1 inicio de sesion / HU2 cierre de sesion

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_sesion | varchar(8) | No | PK | Código automático |
| cod_usuario | varchar(8) | No | FK → usuarios | — |
| fecha_inicio_sesion | timestamp | No | — | Por defecto now |
| fecha_fin_sesion | timestamp | Sí | — | — |
| ip_sesion | varchar(45) | Sí | — | — |

## proveedores
HU8 directorio de proveedores; DIAS_ENTREGA_PROVEEDOR soporta HU16 (ROP)

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_proveedor | varchar(8) | No | PK | Código automático |
| nombre_proveedor | varchar(150) | No | — | — |
| nombre_contacto_proveedor | varchar(150) | Sí | — | — |
| telefono_proveedor | varchar(30) | Sí | — | — |
| email_proveedor | varchar(150) | Sí | — | — |
| direccion_proveedor | varchar(255) | Sí | — | — |
| dias_entrega_proveedor | integer | Sí | — | Check dias_entrega_proveedor >= 0 |
| estado_proveedor | boolean | No | — | Por defecto true |
| fecha_registro_proveedor | timestamp | No | — | Por defecto now |

## marcas
Catalogo de marcas comerciales de las herramientas

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_marca | varchar(8) | No | PK | Código automático |
| nombre_marca | varchar(100) | No | Único | — |
| estado_marca | boolean | No | — | Por defecto true |
| fecha_registro_marca | timestamp | No | — | Por defecto now |

## categorias
Clasificacion de herramientas por tipo/rubro

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_categoria | varchar(8) | No | PK | Código automático |
| nombre_categoria | varchar(100) | No | Único | — |
| estado_categoria | boolean | No | — | Por defecto true |
| fecha_registro_categoria | timestamp | No | — | Por defecto now |

## presentaciones
Presentaciones de costo/empaque: UNIDAD, CAJA

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_presentacion | varchar(8) | No | PK | Código automático |
| nombre_presentacion | varchar(50) | No | Único | — |

## herramientas
HU6 catalogo, HU15 parametros EOQ, HU26 conversion caja-unidad

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_herramienta | varchar(8) | No | PK | Código automático |
| codigo_fabrica_herramienta | varchar(50) | No | Único | — |
| nombre_herramienta | varchar(150) | No | — | — |
| modelo_herramienta | varchar(100) | Sí | — | — |
| cod_marca | varchar(8) | Sí | FK → marcas | — |
| cod_categoria | varchar(8) | Sí | FK → categorias | — |
| cod_proveedor | varchar(8) | Sí | FK → proveedores | — |
| unidades_por_caja_herramienta | integer | No | — | Check unidades_por_caja_herramienta > 0; por defecto 1 |
| demanda_anual_herramienta | numeric(12,2) | Sí | — | Check demanda_anual_herramienta >= 0 |
| costo_pedido_herramienta | numeric(12,2) | Sí | — | Check costo_pedido_herramienta >= 0 |
| costo_almacenamiento_herramienta | numeric(12,2) | Sí | — | Check costo_almacenamiento_herramienta >= 0 |
| dias_entrega_herramienta | integer | Sí | — | Check dias_entrega_herramienta >= 0 |
| dias_estancamiento_herramienta | integer | No | — | Por defecto 40 |
| estado_herramienta | boolean | No | — | Por defecto true |
| fecha_registro_herramienta | timestamp | No | — | Por defecto now |
| fecha_actualizacion_herramienta | timestamp | No | — | Por defecto now |

## costos
HU7: historial de costo por herramienta y presentacion; el vigente se obtiene con VW_COSTO_VIGENTE

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_costo | varchar(8) | No | PK | Código automático |
| cod_herramienta | varchar(8) | No | FK → herramientas | — |
| cod_presentacion | varchar(8) | No | FK → presentaciones | — |
| valor_costo | numeric(12,2) | No | — | Check valor_costo >= 0 |
| fecha_inicio_costo | timestamp | No | — | Por defecto now |
| cod_usuario | varchar(8) | No | FK → usuarios | — |

## lotes_compra
HU10: cabecera de una compra/encomienda recibida de un proveedor

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_lote | varchar(8) | No | PK | Código automático |
| cod_proveedor | varchar(8) | No | FK → proveedores | — |
| numero_factura_lote | varchar(50) | Sí | — | — |
| fecha_lote | timestamp | No | — | Por defecto now |
| cod_usuario | varchar(8) | No | FK → usuarios | — |
| observaciones_lote | text | Sí | — | — |

## transferencias
HU12: cabecera de una transferencia de mercaderia entre sucursales

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_transferencia | varchar(8) | No | PK | Código automático |
| cod_sucursal_origen | varchar(8) | No | FK → sucursales | — |
| cod_sucursal_destino | varchar(8) | No | FK → sucursales | — |
| cod_usuario_autoriza | varchar(8) | No | FK → usuarios | — |
| cod_usuario | varchar(8) | No | FK → usuarios | — |
| fecha_transferencia | timestamp | No | — | Por defecto now |
| observaciones_transferencia | text | Sí | — | — |

## ingresos_inventario
HU10: ingreso de mercaderia por compra (via LOTES_COMPRA), transferencia (via TRANSFERENCIAS) o ajuste

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_ingreso | varchar(8) | No | PK | Código automático |
| cod_herramienta | varchar(8) | No | FK → herramientas | — |
| cod_sucursal | varchar(8) | No | FK → sucursales | — |
| tipo_ingreso | varchar(15) | No | — | Valores: COMPRA, TRANSFERENCIA, AJUSTE |
| cantidad_unidades_ingreso | integer | No | — | Check cantidad_unidades_ingreso > 0 |
| cantidad_cajas_ingreso | numeric(10,2) | Sí | — | — |
| cod_lote | varchar(8) | Sí | FK → lotes_compra | — |
| cod_transferencia | varchar(8) | Sí | FK → transferencias | — |
| cod_usuario | varchar(8) | No | FK → usuarios | — |
| fecha_ingreso | timestamp | No | — | Por defecto now |
| observaciones_ingreso | text | Sí | — | — |

## salidas_inventario
HU9: salida de producto por consumo, transferencia (via TRANSFERENCIAS) o ajuste

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_salida | varchar(8) | No | PK | Código automático |
| cod_herramienta | varchar(8) | No | FK → herramientas | — |
| cod_sucursal | varchar(8) | No | FK → sucursales | — |
| tipo_salida | varchar(15) | No | — | Valores: SALIDA, TRANSFERENCIA, AJUSTE |
| cantidad_unidades_salida | integer | No | — | Check cantidad_unidades_salida > 0 |
| cod_transferencia | varchar(8) | Sí | FK → transferencias | — |
| cod_usuario | varchar(8) | No | FK → usuarios | — |
| fecha_salida | timestamp | No | — | Por defecto now |
| observaciones_salida | text | Sí | — | — |

## promociones
HU23: etiquetado visual de promocion para herramientas estancadas

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_promocion | varchar(8) | No | PK | Código automático |
| cod_herramienta | varchar(8) | No | FK → herramientas | — |
| cod_sucursal | varchar(8) | No | FK → sucursales | — |
| activo_promocion | boolean | No | — | Por defecto true |
| fecha_inicio_promocion | date | No | — | Por defecto current_date |

## historial_modificaciones
HU13: log de quien y cuando edita un registro de catalogo o de usuarios

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_historial | varchar(8) | No | PK | Código automático |
| tabla_historial | varchar(50) | No | — | — |
| registro_historial | varchar(8) | No | — | — |
| cod_usuario | varchar(8) | Sí | FK → usuarios | — |
| accion_historial | varchar(15) | No | — | Valores: INSERTAR, MODIFICAR, ELIMINAR |
| fecha_historial | timestamp | No | — | Por defecto now |

## calculo_eoq_rop
HU17 EOQ, HU18 alerta ROP, HU19 sugerencia, HU20 ajuste caja, HU21 tendencia

| Columna | Tipo | Nulo | Clave | Restricción |
|---|---|---|---|---|
| cod_calculo | varchar(8) | No | PK | Código automático |
| cod_herramienta | varchar(8) | No | FK → herramientas | — |
| fecha_calculo | timestamp | No | — | Por defecto now |
| demanda_anual_calculo | numeric(12,2) | No | — | — |
| eoq_calculado | numeric(12,2) | No | — | — |
| eoq_cajas_calculado | numeric(12,2) | Sí | — | — |
| rop_calculado | numeric(12,2) | Sí | — | — |
| stock_calculo | integer | Sí | — | — |
| alerta_calculo | boolean | No | — | Por defecto false |
| cantidad_sugerida_calculo | numeric(12,2) | Sí | — | — |
