# Estado del proyecto — Inventario Multisucursal (WALL-E)

> "Memoria" del proyecto entre sesiones: si se abre una terminal o chat
> nuevo, leer esto primero. Se actualiza en el mismo commit que cambia algo
> importante. Versiones exactas del stack: ver `STACK_VERSIONES.md`.
>
> **Última actualización: 27/10/2026, Sprint 4** (semana 9 del
> cronograma). Rama de trabajo: `sprint4`, salida de `sprint3-cierre`
> (donde quedó fusionada la fase 1 de diseño). Todo solo en local, sin
> push. Reglas visuales: `docs/DISENO.md`.

## Equipo y materia
Proyecto académico (Programación III y Análisis y Diseño II) para una
importadora de herramientas con 2 sucursales. Jostin = backend,
Beymar = frontend. Repo: `github.com/c4r4durr-sketch/WALL-E`, rama `main`.

## Cronograma
16 semanas desde el **01/09/2026**.

| Semanas | Sprint | Estado |
|---|---|---|
| 1–3 | Sprint 1: login, usuarios, base | ✅ |
| 4–6 | Sprint 2: catálogo | ✅ (entregable del sábado 27/09: CRUD de catálogo probado — superado) |
| 7–10 | Sprint 3: movimientos | ✅ adelantado (entradas, salidas, ajustes, stock) |
| — | Dashboard (HU24) | ✅ adelantado para el 27/09 |
| — | Transferencias (HU12) | ✅ adelantado |
| — | EOQ / ROP / ABC (HU17–HU21) | ✅ adelantado |
| 8–9 | Deuda: zona horaria, usuarios en 4 capas, HU3, HU7 | ✅ (bloque a-d) |
| 9–10 | HU8 proveedores, HU14 cierre diario, HU13 pantalla de historial | ✅ adelantado (bloque e-g) |
| — | Adelanto Sprint 4: HU22, HU23, HU25 | pendiente (bloque h-j) |
| — | Adelanto Sprint 5: HU21 | ✅ (rama `sprint4`) |

## Entorno real de esta máquina (verificado 22/09/2026)
- **PostgreSQL 18.6 nativo** (servicio de Windows `postgresql-x64-18`) en
  el puerto **5433**. **No se usa Docker** (no está instalado).
  `docker-compose.yml` (postgres:16) quedó de un plan inicial y **no se usa**.
- Base `eoq_db`; usuario y contraseña solo en `backend/.env` (no versionado;
  plantilla en `backend/.env.example`). El usuario necesita el
  permiso `CREATEDB` para que `manage.py test` pueda crear la base de pruebas.
- Python 3.12.10 en `backend/venv`. Node 24 + npm 11.

## Arquitectura (no cambiar sin acordarlo)
- **Backend**: Django 5.1 + DRF + SimpleJWT + drf-spectacular. Clean
  Architecture por app: `domain/` (puro, sin Django) → `use_cases/` (puro,
  reciben repositorios como interfaces) → `infrastructure/` (modelos ORM,
  repositorios concretos, migraciones) → `interfaces/api/` (serializers y
  vistas DRF que solo orquestan).
- Apps (los 7 módulos del informe): `usuarios`, `catalogo`, `proveedores`,
  `movimientos`, `transferencias`, `indicadores`, `auditoria`.
  `indicadores` no tiene `infrastructure/` porque no tiene tablas propias.
- **Zona horaria**: `TIME_ZONE = "America/La_Paz"` (la base guarda en UTC).
  "Hoy" y los días sin venta se cuentan en hora de La Paz.
- **Errores de la API, formato único**: 400 → `{campo: ["mensaje"]}`;
  401/403/404/409 → `{"detail": "mensaje"}`. El frontend los lee con
  `shared/api/errores.ts`.
- **Diferencias con el informe**: se anotan en `docs/CAMBIOS_PARA_EL_INFORME.md`
  (no se improvisa en el código).
- **El esquema de la base lo definen SOLO los modelos y migraciones de
  Django.** `base_datos.sql` se descartó (sus tablas no coincidían con las
  de Django y empezaba con `DROP SCHEMA public CASCADE`); está archivado en
  `docs/archivo/base_datos_descartado.sql` como referencia. **No ejecutarlo.**
  Tampoco ejecutar `walle_importaciones_db_v7.sql` (Jostin): también empieza
  con `DROP SCHEMA public CASCADE`.
- **Nombres físicos de la base** según la convención de la base académica
  (`walle_importaciones_db_v7.sql`): tablas en plural (`herramientas`,
  `movimientos`…), PK `cod_<entidad>`, columnas `<dato>_<entidad>`. Se aplica
  **solo en la base** con `Meta.db_table` / `db_column`; en Python, la API y
  el frontend los nombres siguen siendo los de siempre. Mapa completo en
  `docs/DICCIONARIO_DE_DATOS.md`. Al agregar un campo o modelo, seguir la
  misma convención (`db_column="<dato>_<entidad>"`).
- **Frontend**: React 18 + TypeScript + Vite + Tailwind v4 + Axios +
  TanStack Query, carpetas por feature (`features/<feature>/{api,hooks,components,pages}`).
  Iconos con `lucide-react` (sin emojis); solo escritorio. TypeScript
  `strict`, sin `any`. Fechas en hora de La Paz con `shared/formato`.

## Qué funciona hoy (en `sprint4`)

| Módulo | Backend | Frontend |
|---|---|---|
| **Login JWT** | `POST /api/token/`, `/api/token/refresh/`; el token lleva rol y sucursal | Login, rutas protegidas por sesión y por rol, **refresh automático** del access (30 min) mientras el refresh (1 día) siga vigente |
| **Usuarios** (HU3/HU4/HU5) | Use case `gestionar_usuarios.py`, solo Admin: crear, editar, desactivar (no hay DELETE: 405), `POST /usuarios/<id>/restablecer-password/`. Sucursal activa obligatoria para Supervisor y Empleado; username único sin mayúsculas; política de contraseñas de Django (en español); nadie se desactiva ni se quita el rol a sí mismo y siempre queda un Admin activo (409) | `/usuarios` (lista, editar, restablecer contraseña, desactivar/activar) y `/usuarios/nuevo`, solo Admin |
| **Auditoría** (HU13) | App `auditoria` (4 capas): signals guardan INSERT/UPDATE/DELETE de Usuario, Sucursal, Herramienta, Proveedor, Movimiento, Transferencia con autor y datos antes/después (sin contraseñas). `GET /api/auditoria/historial/` (filtros por días, usuario, tabla, acción; paginado; campos cambiados) y `.../opciones/`. Admin y Supervisor; Empleado 403; solo lectura | `/historial` (Admin y Supervisor): filtros, paginación y detalle antes/después. También en `/admin/` |
| **Proveedores** (HU8) | App `proveedores` (4 capas). CRUD `/api/proveedores/` con `?buscar=` y `?activos=`; nombre único sin mayúsculas, teléfono obligatorio (7–15 dígitos), correo opcional. Solo el Admin escribe (403), todos consultan. Con herramientas asociadas no se elimina (409): se desactiva. Herramienta → proveedor (opcional, solo activos) | `/proveedores`: búsqueda, alta, edición, activar/desactivar, eliminar sin herramientas; selector y columna de proveedor en el catálogo |
| **Catálogo** (HU6/HU7) | CRUD real con use cases; código único, caja ≥ 1 unidad, datos EOQ/ROP opcionales. Admin/Supervisor escriben, Empleado solo lee (403). **Costo unitario** (HU7): > 0, solo el Admin lo cambia (403), no se puede quitar; cada cambio va a `historial_costos` en la misma transacción; `GET /catalogo/herramientas/<id>/historial-costos/`. Borrar una herramienta con movimientos o historial de costos → **409** | `/catalogo`: alta, edición, borrado con confirmación, columna de costo y panel de historial de costos (todos los roles); el Supervisor ve el costo deshabilitado |
| **Movimientos** (HU9/HU11) | Entrada, salida, **ajuste** (+/−, motivo obligatorio, solo Admin/Supervisor). Conversión caja→unidad. **Nunca stock negativo** (bloqueo `select_for_update`). Stock derivado de los movimientos. Inmutables para todos (405, `/admin/` solo lectura). Empleado solo opera en su sucursal | `/movimientos`: registro, sección de ajuste aparte, stock por sucursal e historial con motivo |
| **Fórmulas** | `indicadores/domain/formulas.py`: EOQ, ROP, ajuste a cajas, cajas↔unidades (probadas) | — |
| **Transferencias** (HU12) | Solicitar (cualquier rol; Empleado solo desde su sucursal) → PENDIENTE sin mover stock. Admin/Supervisor COMPLETAN (salida en origen + entrada en destino, misma validación y bloqueo de stock; si ya no alcanza → 409) o RECHAZAN con motivo. No se completa dos veces (bloqueo). Sin editar ni borrar | `/transferencias`: solicitud, pendientes/todas, completar y rechazar en la fila |
| **Indicadores** (HU17–HU21) | `GET /api/indicadores/eoq/<id>/` (EOQ con D/S/H del catálogo, ajustado a cajas, + demanda observada de 12 meses), `rop/<id>/` (ROP vs stock total, `requiere_reorden`), `abc/` (por unidades vendidas en 12 meses: A < 80 % acumulado previo, B < 95 %, C resto y sin ventas). Si faltan datos: 200 con `null` + `datos_faltantes`. **HU21**: `POST .../eoq/<id>/actualizar-demanda/` (Admin y Supervisor; Empleado 403; sin ventas en 12 meses 409) pasa lo vendido a `demanda_anual` del catálogo | `/indicadores`: tabla ABC; al elegir una herramienta, "cuánto pedir" (EOQ) y "cuándo pedir" (ROP); si lo vendido no coincide con la demanda estimada, botón "Usar lo vendido" (Admin y Supervisor) |
| **Cierre diario** (HU14) | `GET /api/indicadores/cierre-diario/?sucursal=&fecha=`: movimientos del día en hora de La Paz, totales por tipo, salidas destacadas. Admin cualquier sucursal, Supervisor la suya, Empleado 403; fecha futura 400 | `/cierre-diario` (Admin y Supervisor): fecha y sucursal, tarjetas de totales, tabla y aviso si no hubo salidas |
| **Dashboard** (HU24) | `GET /api/indicadores/panel/` (todos los roles): alertas de reorden (stock total ≤ ROP, con pedido sugerido = EOQ en cajas), herramientas sin ventas hace > 40 días, totales. Equivale a las vistas SQL `vw_panel_auditoria` / `vw_alertas_reorden` / `vw_herramientas_estancadas` | `/` (inicio): indicadores + tablas de alertas y estancadas |

Pruebas: `backend/venv/Scripts/python.exe manage.py test apps` → **211 pruebas OK**.

**Fase 1 de diseño** (cerrada y fusionada en `sprint3-cierre` el 27/10): todas las pantallas sobre el sistema
de `docs/DISENO.md` (componentes en `frontend/src/components/ui/`, barra
lateral en `frontend/src/app/layout/`), modo claro y oscuro, y **foto
obligatoria** al dar de alta una herramienta (`herramientas.imagen_herramienta`,
archivos en `backend/media/productos/`, fuera del repo). Para tener fotos de
muestra: `manage.py cargar_fotos_demo` (solo completa las que no tienen).
Frontend: `npx tsc -b`, `npx vite build` y `npx oxlint src` sin errores
(el build avisa que el paquete JS pesa 621 kB: se divide por rutas en el
Sprint 4).

## Pendiente (en orden)
1. Bloque h-j: HU22 (reporte de antigüedad), HU23 (promoción), HU25 (Excel).
3. `docker-compose.yml`: decidir si se borra o se actualiza (hoy no refleja
   el entorno real; ya no tiene credenciales escritas).

## Decisiones tomadas (para no volver a discutirlas)
- Borrar herramienta con movimientos o historial de costos → 409; **no** hay
  campo "activo" en herramientas.
- Las cuentas de usuario no se borran: se desactivan.
- Proveedores: solo el Administrador los gestiona; con herramientas no se
  borran (se desactivan); uno inactivo no se asigna a herramientas nuevas.
- Cierre diario e historial: Admin y Supervisor (en el cierre, el
  Supervisor solo ve su sucursal). El "día" siempre es el de La Paz.
- HU7 es **costo unitario de compra** (no precio de venta); solo el
  Administrador lo cambia; historial propio en `historial_costos` (la
  auditoría genérica sigue registrando todo, pero es oculta).
- Movimientos inmutables; los errores se corrigen con ajustes.
- Cada movimiento guarda `cantidad_unidades` al registrarse (cambiar el
  tamaño de caja no altera el stock histórico).
- Los ajustes y las transferencias no cuentan como demanda para EOQ/ABC.
- EOQ/ROP usan la demanda anual **estimada** del catálogo (la misma del panel);
  la demanda observada (ventas de 12 meses) se muestra al lado para comparar.
- HU21: "actualizar la demanda" reemplaza `demanda_anual` por las ventas
  de los últimos 12 meses **sin anualizar** (con menos de un año de
  historia, la pantalla avisa y decide el usuario). Sin ventas no se
  actualiza (409). Admin y Supervisor, como el resto del catálogo.
- ABC por **unidades vendidas** (se decidió antes de HU7; pasar a valor está
  anotado en `docs/CAMBIOS_PARA_EL_INFORME.md`). Una
  herramienta es A si el acumulado *anterior* a ella es < 80 % (la más
  vendida siempre es A).
- Empleado: solo su sucursal en movimientos; solo lectura en catálogo.
- Convención de nombres de la base académica aplicada **solo en la base**
  (14/10/2026): no se renombró nada en Python, serializers ni frontend. Las
  migraciones solo renombran tablas y columnas (los datos se conservan).
  `is_staff`, `is_superuser` y las tablas de permisos de Django
  (`usuarios_groups`, `usuarios_user_permissions`, `auth_*`, `django_*`)
  quedan con su nombre de Django. Las PK siguen siendo enteros.
- La auditoría guarda la etiqueta del modelo (`catalogo.Herramienta`) y los
  nombres de campo de Python, no los nombres físicos: no cambia con el renombre.
- Estancamiento: más de 40 días sin una SALIDA real (los ajustes no son
  ventas); si nunca se vendió, se cuenta desde su primer movimiento en esa
  sucursal (el SQL original la marcaba estancada desde el primer día).

## Cómo levantar el proyecto
```bash
# Backend (desde backend/)
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py runserver          # :8000, Swagger en /api/docs/
# Frontend (desde frontend/)
npm run dev                                            # :5173, proxy /api -> :8000
```
Después de cada `git pull`: correr `migrate` y, si cambió
`requirements.txt` o `package.json`, `pip install -r requirements.txt` y
`npm install`. Fase 1 suma `catalogo.0006` (columna de la foto, nula) y
las dependencias Pillow, motion, @radix-ui/react-dialog y
@fontsource-variable/inter. (Al 20/10 la base local tiene
pendientes las 5 migraciones de nombres del 14/10, `catalogo.0004` y
`0005`, `proveedores.0001`, `movimientos.0008` y `auditoria.0003`: solo
agregan tablas, columnas e índices, o renombran; no borran datos.)

## Convenciones
- Nada de lógica de negocio en `views.py` ni en `models.py`: va en un use case.
- `domain/` y `use_cases/` no importan Django ni DRF.
- Los repositorios concretos son el único lugar que traduce ORM ↔ entidad,
  y guardan con `.save()`/`.delete()` por instancia (así se dispara la auditoría).
- Un commit por paso/sub-paso; ramas por paso, se fusionan a `main` tras revisión.
