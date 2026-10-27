# Diccionario de datos — Inventario Multisucursal (WALL-E)

> Base PostgreSQL `eoq_db`. Esquema generado **solo** por los modelos y
> migraciones de Django (ver `ESTADO_DEL_PROYECTO.md`). Tipos y claves
> tomados de `information_schema` de la base real (14/10/2026).

## Convención de nombres

Se aplica la convención de la base académica (`walle_importaciones_db_v7.sql`)
**solo a los nombres físicos** de la base, con `Meta.db_table` y `db_column`.
En Python (modelos, serializers, vistas, casos de uso) y en la API/frontend
los nombres **no cambian**: por eso cada columna se lista como
`nombre físico ← campo Python`.

- Tablas en plural y en minúsculas (`herramientas`, no `"Herramientas"`): en
  `psql` no hacen falta comillas.
- Cada columna lleva el nombre de su entidad: `nombre_herramienta`,
  `estado_sucursal`, `fecha_movimiento`…
- Clave primaria `cod_<entidad>`; claves foráneas `cod_<entidad>` (o
  `cod_<entidad>_<rol>` si hay dos hacia la misma tabla). Son **enteros**
  (`bigint` autoincremental), no textos tipo `'HE-00001'`.
- Fechas `fecha_<algo>_<entidad>`, estados `estado_<entidad>`.

Excepciones (se dejan con el nombre de Django a propósito):

- `usuarios.is_staff`, `usuarios.is_superuser`: los usa el admin de Django;
  no forman parte del mapa de la base académica.
- `usuarios_groups` y `usuarios_user_permissions`: tablas intermedias que
  Django crea solo para los permisos de `AbstractUser`. Siguen el nombre de
  la tabla `usuarios`, pero sus columnas (`usuario_id`, `group_id`,
  `permission_id`) son de Django.
- Tablas internas de Django sin tocar: `django_migrations`,
  `django_content_type`, `django_session`, `django_admin_log`, `auth_*`.
- Los nombres de restricciones e índices generados por Django (por ejemplo,
  `catalogo_herramienta_codigo_key`) conservan el prefijo antiguo: son
  internos y no afectan a las consultas.

## Relaciones

```
sucursales 1 ──< usuarios                 (usuarios.cod_sucursal, opcional)
sucursales 1 ──< movimientos              (movimientos.cod_sucursal)
sucursales 1 ──< transferencias           (cod_sucursal_origen / cod_sucursal_destino)
usuarios   1 ──< movimientos              (movimientos.cod_usuario: quién lo registró)
usuarios   1 ──< transferencias           (cod_usuario: quién la pidió; cod_usuario_resuelve: quién la resolvió)
usuarios   1 ──< historial_modificaciones (cod_usuario: autor del cambio, opcional)
herramientas 1 ──< movimientos            (movimientos.cod_herramienta)
herramientas 1 ──< transferencias         (transferencias.cod_herramienta)
herramientas 1 ──< historial_costos       (historial_costos.cod_herramienta)
herramientas 1 ──< promociones            (promociones.cod_herramienta)
sucursales   1 ──< promociones            (promociones.cod_sucursal)
usuarios     1 ──< promociones            (cod_usuario: quién la creó)
proveedores  1 ──< herramientas           (herramientas.cod_proveedor, opcional)
usuarios     1 ──< historial_costos       (cod_usuario: quién cambió el costo)
movimientos  1 ── 0..1 transferencias     (cod_movimiento_salida / cod_movimiento_entrada, únicos)
```

Borrado: todas las FK son `PROTECT` en Django (no se puede borrar una
sucursal, usuario, herramienta o movimiento referenciado), salvo
`historial_modificaciones.cod_usuario`, que es `SET NULL`. En PostgreSQL son
FK `DEFERRABLE INITIALLY DEFERRED` sin `ON DELETE` (la regla la aplica Django).

---

## sucursales
Modelo `usuarios.Sucursal`. Las sucursales de la importadora.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_sucursal` | `id` | bigint (identity) | no | **PK** |
| `nombre_sucursal` | `nombre` | varchar(100) | no | |
| `direccion_sucursal` | `direccion` | varchar(255) | no (vacío permitido) | |
| `estado_sucursal` | `activa` | boolean | no | default `true` |

## usuarios
Modelo `usuarios.Usuario` (`AUTH_USER_MODEL`, hereda de `AbstractUser`).

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_usuario` | `id` | bigint (identity) | no | **PK** |
| `nombre_usuario` | `username` | varchar(150) | no | **UNIQUE** (login) |
| `contrasena_usuario` | `password` | varchar(128) | no | hash PBKDF2 de Django |
| `nombres_usuario` | `first_name` | varchar(150) | no (vacío permitido) | |
| `apellidos_usuario` | `last_name` | varchar(150) | no (vacío permitido) | |
| `email_usuario` | `email` | varchar(254) | no (vacío permitido) | |
| `rol_usuario` | `rol` | varchar(20) | no | `ADMINISTRADOR` / `SUPERVISOR` / `EMPLEADO`; default `EMPLEADO` |
| `cod_sucursal` | `sucursal` | bigint | sí | **FK** → `sucursales.cod_sucursal` (obligatoria para Supervisor y Empleado, lo valida el dominio) |
| `estado_usuario` | `is_active` | boolean | no | default `true` |
| `fecha_registro_usuario` | `date_joined` | timestamptz | no | |
| `fecha_ultimo_acceso_usuario` | `last_login` | timestamptz | sí | |
| `is_staff` | `is_staff` | boolean | no | (nombre de Django) |
| `is_superuser` | `is_superuser` | boolean | no | (nombre de Django) |

## herramientas
Modelo `catalogo.Herramienta`. Catálogo y datos de entrada de EOQ/ROP.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_herramienta` | `id` | bigint (identity) | no | **PK** |
| `codigo_fabrica_herramienta` | `codigo` | varchar(30) | no | **UNIQUE** |
| `nombre_herramienta` | `nombre` | varchar(150) | no | |
| `modelo_herramienta` | `modelo` | varchar(100) | no (vacío permitido) | |
| `unidades_por_caja_herramienta` | `unidades_por_caja` | integer | no | ≥ 0 en BD, ≥ 1 validado; default 1 |
| `demanda_anual_herramienta` | `demanda_anual` | integer | sí | ≥ 0 (D de EOQ) |
| `costo_pedido_herramienta` | `costo_pedido` | numeric(12,2) | sí | S de EOQ |
| `costo_almacenamiento_herramienta` | `costo_almacenamiento_unitario` | numeric(12,2) | sí | H de EOQ |
| `dias_entrega_herramienta` | `tiempo_entrega_dias` | integer | sí | ≥ 0 (lead time del ROP) |
| `costo_unitario_herramienta` | `costo_unitario` | numeric(12,2) | sí | > 0 (lo valida el caso de uso); HU7, cada cambio va a `historial_costos` |
| `cod_proveedor` | `proveedor` | bigint | sí | **FK** → `proveedores.cod_proveedor` (HU8; solo se asigna uno activo) |
| `imagen_herramienta` | `imagen` | varchar(255) | sí | ruta de la foto dentro de `MEDIA_ROOT` (`productos/…`); obligatoria al dar de alta (lo exige la API), nula en las herramientas anteriores; JPG, PNG o WebP de hasta 5 MB |
| `fecha_registro_herramienta` | `creado_en` | timestamptz | no | se fija al crear |
| `fecha_actualizacion_herramienta` | `actualizado_en` | timestamptz | no | se actualiza en cada guardado |

## proveedores
Modelo `proveedores.Proveedor` (HU8). Directorio de proveedores. Un
proveedor con herramientas asociadas no se elimina: se desactiva.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_proveedor` | `id` | bigint (identity) | no | **PK** |
| `nombre_proveedor` | `nombre` | varchar(150) | no | **UNIQUE** (además, único sin distinguir mayúsculas, lo valida el caso de uso) |
| `telefono_proveedor` | `telefono` | varchar(30) | no | 7 a 15 dígitos (caso de uso) |
| `email_proveedor` | `email` | varchar(254) | no (vacío permitido) | |
| `estado_proveedor` | `activo` | boolean | no | default `true` |
| `fecha_registro_proveedor` | `creado_en` | timestamptz | no | se fija al crear |
| `fecha_actualizacion_proveedor` | `actualizado_en` | timestamptz | no | se actualiza en cada guardado |

## historial_costos
Modelo `catalogo.HistorialCosto` (HU7). Una fila por cada vez que se carga o
cambia el costo unitario de una herramienta. Solo se insertan filas.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_historial_costo` | `id` | bigint (identity) | no | **PK** |
| `cod_herramienta` | `herramienta` | bigint | no | **FK** → `herramientas.cod_herramienta`; índice `historial_costo_herr_fecha_idx` (con la fecha, descendente) |
| `costo_anterior_historial_costo` | `costo_anterior` | numeric(12,2) | sí | null la primera vez que se carga el costo |
| `costo_nuevo_historial_costo` | `costo_nuevo` | numeric(12,2) | no | |
| `cod_usuario` | `usuario` | bigint | no | **FK** → `usuarios.cod_usuario` (quién lo cambió) |
| `fecha_historial_costo` | `fecha` | timestamptz | no | se fija al crear |

## promociones
Modelo `catalogo.Promocion` (HU23, sprint 4, migración `catalogo.0007`).
Descuento sobre una herramienta **estancada** en una sucursal. No se edita
ni se borra: se termina con `activa_promocion = false`. Reglas del caso de
uso (`indicadores/use_cases/promociones.py`): solo el Administrador la crea
o la termina; solo si la herramienta tiene stock y más de 40 días sin venta
en esa sucursal; una sola vigente por herramienta y sucursal. Auditada en
`historial_modificaciones`.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_promocion` | `id` | bigint (identity) | no | **PK** |
| `cod_herramienta` | `herramienta` | bigint | no | **FK** → `herramientas.cod_herramienta`; índice `promocion_herr_suc_idx` (con la sucursal) |
| `cod_sucursal` | `sucursal` | bigint | no | **FK** → `sucursales.cod_sucursal` |
| `descuento_promocion` | `descuento_porcentaje` | smallint | no | CHECK `promocion_descuento_1_a_90` (1 a 90 %) |
| `fecha_inicio_promocion` | `fecha_inicio` | date | no | el día en que se crea (hora de La Paz) |
| `fecha_fin_promocion` | `fecha_fin` | date | no | inclusive; CHECK `promocion_fin_no_antes_de_inicio` |
| `motivo_promocion` | `motivo` | varchar(255) | no | puede ser vacío |
| `activa_promocion` | `activa` | boolean | no | default true; false = terminada antes de tiempo |
| `cod_usuario` | `usuario` | bigint | no | **FK** → `usuarios.cod_usuario` (quién la creó) |
| `fecha_registro_promocion` | `creado_en` | timestamptz | no | se fija al crear |

Vigente = `activa_promocion` y hoy entre `fecha_inicio_promocion` y
`fecha_fin_promocion` (lo calcula el caso de uso, no se guarda).

## movimientos
Modelo `movimientos.Movimiento`. Entradas, salidas, ajustes y los
movimientos generados por transferencias. Inmutables; el stock se deriva de
aquí (suma de `cantidad_unidades_movimiento`).

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_movimiento` | `id` | bigint (identity) | no | **PK** |
| `cod_herramienta` | `herramienta` | bigint | no | **FK** → `herramientas.cod_herramienta` |
| `cod_sucursal` | `sucursal` | bigint | no | **FK** → `sucursales.cod_sucursal` |
| `cod_usuario` | `usuario` | bigint | no | **FK** → `usuarios.cod_usuario` |
| `tipo_movimiento` | `tipo_movimiento` | varchar(25) | no | `ENTRADA`, `SALIDA`, `AJUSTE_POSITIVO`, `AJUSTE_NEGATIVO`, `TRANSFERENCIA_ENTRADA`, `TRANSFERENCIA_SALIDA` |
| `tipo_unidad_movimiento` | `tipo_unidad` | varchar(10) | no | `UNIDAD` / `CAJA` |
| `cantidad_movimiento` | `cantidad` | integer | no | ≥ 0, en la unidad indicada |
| `cantidad_unidades_movimiento` | `cantidad_unidades` | integer | no | ≥ 0, equivalente en unidades fijado al registrar |
| `motivo_movimiento` | `motivo` | varchar(255) | no (vacío permitido) | obligatorio en ajustes (lo valida el caso de uso) |
| `fecha_movimiento` | `creado_en` | timestamptz | no | se fija al crear |

## transferencias
Modelo `transferencias.Transferencia`. Solicitud de traspaso entre
sucursales; al completarse genera un movimiento de salida y otro de entrada.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_transferencia` | `id` | bigint (identity) | no | **PK** |
| `cod_herramienta` | `herramienta` | bigint | no | **FK** → `herramientas.cod_herramienta` |
| `cod_sucursal_origen` | `sucursal_origen` | bigint | no | **FK** → `sucursales.cod_sucursal` |
| `cod_sucursal_destino` | `sucursal_destino` | bigint | no | **FK** → `sucursales.cod_sucursal` |
| `cod_usuario` | `usuario` | bigint | no | **FK** → `usuarios.cod_usuario` (quien solicita) |
| `tipo_unidad_transferencia` | `tipo_unidad` | varchar(10) | no | `UNIDAD` / `CAJA` |
| `cantidad_transferencia` | `cantidad` | integer | no | ≥ 0 |
| `cantidad_unidades_transferencia` | `cantidad_unidades` | integer | no | ≥ 0, fijado al solicitar |
| `estado_transferencia` | `estado` | varchar(12) | no | `PENDIENTE` / `COMPLETADA` / `RECHAZADA`; default `PENDIENTE` |
| `cod_usuario_resuelve` | `resuelto_por` | bigint | sí | **FK** → `usuarios.cod_usuario` |
| `fecha_resolucion_transferencia` | `resuelto_en` | timestamptz | sí | |
| `motivo_rechazo_transferencia` | `motivo_rechazo` | varchar(255) | no (vacío permitido) | |
| `cod_movimiento_salida` | `movimiento_salida` | bigint | sí | **FK UNIQUE** → `movimientos.cod_movimiento` |
| `cod_movimiento_entrada` | `movimiento_entrada` | bigint | sí | **FK UNIQUE** → `movimientos.cod_movimiento` |
| `fecha_registro_transferencia` | `creado_en` | timestamptz | no | se fija al crear |

## historial_modificaciones
Modelo `auditoria.HistorialModificacion` (HU13). La escriben los signals de
`apps/auditoria/infrastructure/signals.py`.

| Columna | ← Campo Python | Tipo | Nulo | Clave / restricción |
|---|---|---|---|---|
| `cod_historial` | `id` | bigint (identity) | no | **PK** |
| `tabla_historial` | `tabla_afectada` | varchar(100) | no | índice `historial_tabla_registro_idx` (con `registro_historial`) |
| `registro_historial` | `registro_id` | varchar(64) | no | PK del registro afectado, como texto (no es FK) |
| `accion_historial` | `accion` | varchar(10) | no | `INSERT` / `UPDATE` / `DELETE` |
| `cod_usuario` | `usuario` | bigint | sí | **FK** → `usuarios.cod_usuario` (SET NULL) |
| `nombre_usuario_historial` | `usuario_username` | varchar(150) | no (vacío permitido) | copia del username del autor |
| `datos_anteriores_historial` | `datos_anteriores` | jsonb | sí | |
| `datos_nuevos_historial` | `datos_nuevos` | jsonb | sí | |
| `fecha_historial` | `fecha` | timestamptz | no | se fija al crear |

`tabla_historial` guarda la **etiqueta del modelo** (`catalogo.Herramienta`,
`usuarios.Usuario`, …), no el nombre físico de la tabla, y las claves del
JSON son los **nombres de campo de Python** (`codigo`, `herramienta_id`…).
Así el historial anterior y el posterior al renombre se leen igual. La
contraseña nunca se copia al historial.
