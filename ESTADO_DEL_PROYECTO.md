# Estado del proyecto — Inventario Multisucursal (WALL-E)

> "Memoria" del proyecto entre sesiones: si se abre una terminal o chat
> nuevo, leer esto primero. Se actualiza en el mismo commit que cambia algo
> importante. Versiones exactas del stack: ver `STACK_VERSIONES.md`.
>
> **Última actualización: 22/09/2026** (semana 4 del cronograma).

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
| — | Transferencias, EOQ/ROP/ABC, dashboard | pendiente (ver abajo) |

## Entorno real de esta máquina (verificado 22/09/2026)
- **PostgreSQL 18.6 nativo** (servicio de Windows `postgresql-x64-18`) en
  el puerto **5433**. **No se usa Docker** (no está instalado).
  `docker-compose.yml` (postgres:16) quedó de un plan inicial y **no se usa**.
- Base `eoq_db`, usuario `eoq_user` / `eoq_pass` (ver `backend/.env`), con
  permiso `CREATEDB` para que `manage.py test` pueda crear la base de pruebas.
- Python 3.12.10 en `backend/venv`. Node 24 + npm 11.

## Arquitectura (no cambiar sin acordarlo)
- **Backend**: Django 5.1 + DRF + SimpleJWT + drf-spectacular. Clean
  Architecture por app: `domain/` (puro, sin Django) → `use_cases/` (puro,
  reciben repositorios como interfaces) → `infrastructure/` (modelos ORM,
  repositorios concretos, migraciones) → `interfaces/api/` (serializers y
  vistas DRF que solo orquestan).
- Apps: `usuarios`, `catalogo`, `movimientos`, `transferencias`,
  `indicadores`, `auditoria`.
- **El esquema de la base lo definen SOLO los modelos y migraciones de
  Django.** `base_datos.sql` se descartó (sus tablas no coincidían con las
  de Django y empezaba con `DROP SCHEMA public CASCADE`); está archivado en
  `docs/archivo/base_datos_descartado.sql` como referencia. **No ejecutarlo.**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind v4 + Axios +
  TanStack Query, carpetas por feature (`features/<feature>/{api,hooks,components,pages}`).

## Qué funciona hoy (en `main`)

| Módulo | Backend | Frontend |
|---|---|---|
| **Login JWT** | `POST /api/token/`, `/api/token/refresh/`; el token lleva rol y sucursal | Login, rutas protegidas por sesión y por rol, **refresh automático** del access (30 min) mientras el refresh (1 día) siga vigente |
| **Usuarios** (HU4/HU5) | CRUD solo Admin; **Supervisor y Empleado deben tener sucursal** (400 si falta) | Crear cuenta (`/usuarios/nuevo`, solo Admin) |
| **Auditoría** (HU13) | App `auditoria`: signals guardan INSERT/UPDATE/DELETE de Usuario, Sucursal, Herramienta, Movimiento, Transferencia con autor y datos antes/después (sin contraseñas) | Solo lectura en `/admin/` → "Historial de modificaciones" |
| **Catálogo** (HU6) | CRUD real con use cases; código único, caja ≥ 1 unidad, datos EOQ/ROP opcionales. Admin/Supervisor escriben, Empleado solo lee (403). Borrar una herramienta con movimientos → **409** | `/catalogo`: alta, edición, borrado con confirmación; Empleado solo ve la tabla |
| **Movimientos** (HU9/HU11) | Entrada, salida, **ajuste** (+/−, motivo obligatorio, solo Admin/Supervisor). Conversión caja→unidad. **Nunca stock negativo** (bloqueo `select_for_update`). Stock derivado de los movimientos. Inmutables para todos (405, `/admin/` solo lectura). Empleado solo opera en su sucursal | `/movimientos`: registro, sección de ajuste aparte, stock por sucursal e historial con motivo |
| **Fórmulas** | `indicadores/domain/formulas.py`: EOQ, ROP, ajuste a cajas, cajas↔unidades (probadas) | — |

Pruebas: `backend/venv/Scripts/python.exe manage.py test apps` → **69 pruebas OK**.

## Pendiente (en orden)
1. **Dashboard real (HU24)** — reemplazar la pantalla de bienvenida por el
   panel de alertas (equivalente de `vw_panel_auditoria`). *Para el 27/09.*
2. **Transferencias (HU12, paso 4.4)** — semana siguiente. Una transferencia
   completada debe descontar en origen y sumar en destino reutilizando la
   validación/bloqueo de stock de movimientos.
3. **EOQ / ROP / ABC (HU17–HU21, paso 4.5)** — conectar los endpoints
   `/api/indicadores/eoq|rop|abc/` (hoy 501) a `formulas.py`. Para la
   demanda usar solo lo que `movimientos/domain/stock.py::cuenta_como_demanda`
   acepta (salidas; los ajustes no cuentan).
4. Reportes (cierre diario HU14, estancamiento HU22, promoción HU23,
   Excel HU25).
5. `docker-compose.yml`: decidir si se borra o se actualiza (hoy no refleja
   el entorno real).

## Decisiones tomadas (para no volver a discutirlas)
- Borrar herramienta con movimientos → 409; **no** hay campo "activo".
- Movimientos inmutables; los errores se corrigen con ajustes.
- Cada movimiento guarda `cantidad_unidades` al registrarse (cambiar el
  tamaño de caja no altera el stock histórico).
- Los ajustes no cuentan como demanda para EOQ/ABC.
- Empleado: solo su sucursal en movimientos; solo lectura en catálogo.

## Cómo levantar el proyecto
```bash
# Backend (desde backend/)
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py runserver          # :8000, Swagger en /api/docs/
# Frontend (desde frontend/)
npm run dev                                            # :5173, proxy /api -> :8000
```
Después de cada `git pull`: correr `migrate`.

## Convenciones
- Nada de lógica de negocio en `views.py` ni en `models.py`: va en un use case.
- `domain/` y `use_cases/` no importan Django ni DRF.
- Los repositorios concretos son el único lugar que traduce ORM ↔ entidad,
  y guardan con `.save()`/`.delete()` por instancia (así se dispara la auditoría).
- Un commit por paso/sub-paso; ramas por paso, se fusionan a `main` tras revisión.
