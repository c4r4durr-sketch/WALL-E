# Estado del proyecto — Inventario Multisucursal (Importadora de Herramientas)

> Este archivo es la "memoria" del proyecto entre sesiones: si se cierra la
> terminal/chat y se abre uno nuevo, leer esto primero para saber qué ya
> existe, qué decisiones se tomaron y qué falta. Se actualiza cada vez que
> se avanza algo importante.

## Equipo y materia
Proyecto académico (Programación III y Análisis y Diseño II). Jostin =
backend, Beymar = frontend.

## Stack obligatorio (ya confirmado con el usuario, no volver a preguntar)
- Backend: Python 3.12, Django 5, DRF, PostgreSQL 16, JWT
  (djangorestframework-simplejwt), drf-spectacular (Swagger).
- Frontend: React 18 (no 19) + TypeScript + Vite, Tailwind CSS v4, Axios,
  TanStack Query.
- Arquitectura backend: Clean Architecture por app — `domain/` (puro, sin
  Django) → `use_cases/` (puro, sin Django) → `infrastructure/` (modelos
  ORM + repos concretos) → `interfaces/api/` (serializers/views DRF).
  `use_cases` y `domain` NUNCA importan Django.
- Apps Django (bounded contexts): `usuarios`, `catalogo`, `movimientos`,
  `transferencias`, `indicadores`.

## Dependencias extra ya aprobadas por el usuario (no volver a preguntar)
- `psycopg[binary]` (v3, no psycopg2) — driver Postgres.
- `django-environ` — carga de `.env`.
- `django-cors-headers` — CORS entre frontend (5173) y backend (8000).
- `react-router-dom` — rutas por feature.

## Decisiones/hallazgos importantes de esta máquina
- Python 3.12 NO venía instalado; se instaló vía
  `winget install --id Python.Python.3.12`. El venv del backend
  (`backend/venv`) ya usa ese 3.12.
- Esta máquina tiene un **PostgreSQL nativo** corriendo como servicio de
  Windows en el puerto **5432** (proceso `postgres`, detectado con
  `Get-NetTCPConnection`). Por eso el `postgres` de docker-compose está
  mapeado a **5433:5432** (host:contenedor) para no chocar. Si en algún
  momento se prefiere usar ese Postgres nativo en vez de Docker, cambiar
  `DATABASE_URL` en `backend/.env` a puerto 5432 y crear ahí la base/usuario
  `eoq_db`/`eoq_user`/`eoq_pass` a mano.
- Docker Desktop **no está instalado** en esta máquina (se verificó con
  `docker --version` y buscando la carpeta de instalación). No se ha
  levantado el contenedor de Postgres todavía.
- `npm create vite@latest` instaló React 19 por defecto; se bajó a
  `react@18.3.1` / `react-dom@18.3.1` a mano (ver `frontend/package.json`).
- Tailwind instalado es v4 → se usa el plugin oficial `@tailwindcss/vite`
  en `vite.config.ts` (NO `tailwind.config.js` ni PostCSS clásico). El CSS
  solo tiene `@import "tailwindcss";` en `src/index.css`.
- Los modelos ORM de cada app viven en `infrastructure/models.py`, y
  `<app>/models.py` es un shim (`from .infrastructure.models import *`)
  porque Django exige `<app>/models.py`. `MIGRATION_MODULES` en
  `config/settings.py` reubica las migraciones dentro de
  `infrastructure/migrations/` de cada app (excepto `indicadores`, que no
  tiene modelos propios).

## Qué YA existe (skeleton completo, sin lógica de negocio)
- Backend Django completo en `backend/` con las 5 apps en Clean
  Architecture, `AUTH_USER_MODEL = usuarios.Usuario` con rol
  (Administrador/Supervisor/Empleado), JWT vía SimpleJWT con claims
  custom de rol/sucursal, drf-spectacular en `/api/docs/`, CORS
  configurado. Migraciones iniciales ya generadas (`makemigrations`
  corrido y validado, falta `migrate` real contra una BD viva).
- Frontend React+TS+Vite completo en `frontend/` con carpetas por feature
  (auth, catalogo, movimientos, transferencias, dashboard), Axios
  centralizado con interceptor JWT, TanStack Query, router, Tailwind v4.
  Compila y buildea sin errores (`tsc --noEmit`, `npm run build`
  verificados).
- `docker-compose.yml` en la raíz (solo servicio `postgres:16`, puerto
  5433 en el host).
- `.env` / `.env.example` en `backend/` y `frontend/` (con datos reales de
  desarrollo, no placeholders — ya listos para usar).
- Todo el código tiene comentarios explicando el POR QUÉ de cada carpeta
  (para la sustentación).
- **No es un repositorio git todavía** (el usuario no lo ha pedido).

## Qué falta (próximos pasos, en orden)
1. Instalar Docker Desktop (o decidir usar el Postgres nativo existente,
   ver arriba) — el usuario dijo explícitamente "por ahora no" a levantar
   esto, así que no hacerlo hasta que lo pida.
2. `docker compose up -d` (desde `C:\EOQ`).
3. `cd backend && ./venv/Scripts/python.exe manage.py migrate`.
4. `./venv/Scripts/python.exe manage.py createsuperuser` (para probar
   login JWT con un usuario real).
5. Correr en paralelo: `manage.py runserver` (backend, :8000) y
   `npm run dev` (frontend, :5173, ya tiene proxy `/api` → :8000).
6. Recién ahí empezar a implementar lógica de negocio real (los
   `use_cases/` están documentados pero con `raise NotImplementedError`):
   registrar entradas/salidas con conversión caja↔unidad, transferencias
   con validación de stock, EOQ/ROP/ABC, reportes.
7. Cuando se quiera, inicializar git (`git init`) — no se ha hecho.

## Convenciones a mantener al seguir implementando
- Nunca meter lógica de negocio en `interfaces/api/views.py` ni en
  `infrastructure/models.py`: siempre pasar por un use_case en
  `use_cases/`.
- `use_cases/` y `domain/` no importan `django`, `rest_framework` ni nada
  de infraestructura — solo tipos puros de Python y las interfaces
  (`ABC`) de `domain/repositories.py`.
- Los repositorios concretos (`infrastructure/repositories.py`) son el
  único lugar que traduce entre modelo ORM y entidad de dominio.
