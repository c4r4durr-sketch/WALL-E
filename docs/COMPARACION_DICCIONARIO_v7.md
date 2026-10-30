# Base real vs. diccionario v7 (16 tablas)

> Base real: `eoq_db`, leída de `information_schema` el 29/10/2026 (después
> de `catalogo.0008`). Diccionario v7: `docs/Diccionario_16_tablas_v7.md`.
> La base real tiene **18 tablas**: 9 del dominio y 9 internas de Django.

## 1. Tablas

### Coinciden (7): están en los dos

| Tabla | Diferencia principal |
|---|---|
| `sucursales` | faltan teléfono y fecha de registro |
| `usuarios` | un solo campo de apellidos; email y campos de Django; sin `cod_usuario_creador` |
| `proveedores` | sin contacto, dirección ni días de entrega (el tiempo de entrega está en la herramienta) |
| `herramientas` | sin marca, categoría, días de estancamiento ni estado; agrega costo unitario y foto |
| `transferencias` | en el v7 es solo una cabecera; la real guarda la herramienta, la cantidad y su estado |
| `promociones` | la real agrega descuento opcional, fecha de fin, motivo y usuario |
| `historial_modificaciones` | la real guarda el nombre del autor y los datos antes y después (jsonb) |

### En el diccionario v7, pero no en la base (9)

| Tabla v7 | Qué hay en el sistema |
|---|---|
| `costos` | **Equivalente: `historial_costos`.** Un costo por unidad (sin presentación) y el vigente en `herramientas.costo_unitario_herramienta`; no hay vista `VW_COSTO_VIGENTE` |
| `ingresos_inventario` | **Equivalente: `movimientos`**, con `tipo_movimiento` = ENTRADA, AJUSTE_POSITIVO o TRANSFERENCIA_ENTRADA |
| `salidas_inventario` | **Equivalente: `movimientos`**, con `tipo_movimiento` = SALIDA, AJUSTE_NEGATIVO o TRANSFERENCIA_SALIDA |
| `calculo_eoq_rop` | No se guarda: EOQ, ROP, pedido sugerido y alerta se calculan al consultar (`indicadores/domain/formulas.py`), con la demanda observada de 12 meses (HU21) |
| `sesiones_usuario` | No hace falta: la sesión es un token JWT (HU1/HU2), sin estado en la base |
| `presentaciones` | No es tabla: `tipo_unidad` UNIDAD/CAJA en cada movimiento, más `unidades_por_caja_herramienta` |
| `marcas` | No implementada (ninguna HU la pide) |
| `categorias` | No implementada (ninguna HU la pide) |
| `lotes_compra` | No implementada: una entrada (HU10) no lleva factura ni lote |

### En la base, pero no en el diccionario v7 (11)

| Tabla real | Por qué existe |
|---|---|
| `historial_costos` | HU7: cada cambio de costo con fecha y usuario (reemplaza a `costos`) |
| `movimientos` | HU9–HU12, HU27: un registro inmutable por entrada, salida, ajuste o transferencia (reemplaza a `ingresos_inventario` y `salidas_inventario`) |
| `auth_group`, `auth_group_permissions`, `auth_permission`, `usuarios_groups`, `usuarios_user_permissions` | Internas de Django (permisos de `AbstractUser`); el sistema no las usa: los permisos van por `rol_usuario` |
| `django_migrations`, `django_content_type`, `django_session`, `django_admin_log` | Internas de Django (migraciones, tipos de modelo, sesión y bitácora del admin) |

Nota: `promociones` **sí** está en el v7. En la base es la misma tabla, con
más columnas.

## 2. Columnas de las tablas que coinciden

En **todas** las tablas:

| v7 | Base real | Motivo |
|---|---|---|
| `cod_*` varchar(8) "código automático" | `cod_*` bigint autoincremental | El ORM genera claves enteras; no hay códigos tipo 'HE-00001' |
| `timestamp` | `timestamp with time zone` | Las fechas se guardan en UTC y se muestran en hora de La Paz |
| `fecha_actualizacion_*` | Solo en `herramientas` y `proveedores` | Las demás tablas no se editan o lo registra el historial |

### Por tabla

En "Solo en la base" van entre paréntesis la HU o el motivo.

| Tabla | Solo en v7 | Solo en la base | Mismo nombre, distinto tipo o regla |
|---|---|---|---|
| `sucursales` | `telefono_sucursal`, `fecha_registro_sucursal` | — | `nombre_sucursal` no es único en la base |
| `usuarios` | `apellido_paterno_usuario`, `apellido_materno_usuario`, `cod_usuario_creador`, `fecha_actualizacion_usuario` | `apellidos_usuario` (uno solo), `email_usuario`, `fecha_ultimo_acceso_usuario`, `is_superuser`, `is_staff` (de Django) | `nombre_usuario` 50 → 150; `contrasena_usuario` 255 → 128 (hash de Django); `rol_usuario` 15 → 20 |
| `proveedores` | `nombre_contacto_proveedor`, `direccion_proveedor`, `dias_entrega_proveedor` | `fecha_actualizacion_proveedor` | `telefono_proveedor` obligatorio en la base; `nombre_proveedor` único; `email_proveedor` 150 → 254 |
| `herramientas` | `cod_marca`, `cod_categoria`, `dias_estancamiento_herramienta`, `estado_herramienta` | `costo_unitario_herramienta` (HU7), `imagen_herramienta` (foto obligatoria al dar de alta) | `codigo_fabrica_herramienta` 50 → 30; `demanda_anual_herramienta` numeric(12,2) → integer; los 40 días de estancamiento son una regla fija del código, no una columna |
| `transferencias` | `cod_usuario_autoriza`, `fecha_transferencia`, `observaciones_transferencia` | `cod_herramienta`, `cantidad_transferencia`, `tipo_unidad_transferencia`, `cantidad_unidades_transferencia`, `estado_transferencia` (PENDIENTE/COMPLETADA/RECHAZADA), `motivo_rechazo_transferencia`, `cod_usuario_resuelve`, `fecha_resolucion_transferencia`, `cod_movimiento_salida`, `cod_movimiento_entrada`, `fecha_registro_transferencia` | Quien autoriza (`cod_usuario_resuelve`) es opcional mientras está pendiente |
| `promociones` | — | `descuento_promocion` (opcional, 1–90 %), `fecha_fin_promocion`, `motivo_promocion`, `cod_usuario`, `fecha_registro_promocion` | `activo_promocion` → **`activa_promocion`**; `fecha_inicio_promocion` sin default (la pone el caso de uso: hoy) |
| `historial_modificaciones` | — | `nombre_usuario_historial`, `datos_anteriores_historial`, `datos_nuevos_historial` (jsonb) | Acciones INSERTAR/MODIFICAR/ELIMINAR → **INSERT/UPDATE/DELETE**; `tabla_historial` 50 → 100; `registro_historial` 8 → 64; audita también movimientos, transferencias, proveedores y promociones, no solo catálogo y usuarios |

### Tablas equivalentes con otro nombre

| v7 | Base real |
|---|---|
| `costos.valor_costo` | `historial_costos.costo_nuevo_historial_costo` (+ `costo_anterior_historial_costo`) |
| `costos.fecha_inicio_costo` | `historial_costos.fecha_historial_costo` |
| `costos.cod_presentacion` | — (el costo es por unidad) |
| `ingresos_inventario` / `salidas_inventario` `.tipo_*` | `movimientos.tipo_movimiento` (6 valores) |
| `.cantidad_unidades_*` | `movimientos.cantidad_unidades_movimiento` |
| `ingresos_inventario.cantidad_cajas_ingreso` | `movimientos.tipo_unidad_movimiento` + `cantidad_movimiento` |
| `.observaciones_*` | `movimientos.motivo_movimiento` (obligatorio en ajustes) |
| `.fecha_*` | `movimientos.fecha_movimiento` |
| `.cod_transferencia` | Al revés: `transferencias.cod_movimiento_salida` / `cod_movimiento_entrada` |
| `ingresos_inventario.cod_lote` | — (sin lotes) |
