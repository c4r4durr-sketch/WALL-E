# WALL-E · Inventario multisucursal

Sistema web de inventario para una importadora de herramientas con dos
sucursales. Lleva el catálogo, las entradas, salidas, ajustes y
transferencias entre sucursales, y calcula cuánto y cuándo pedir (EOQ y
punto de reorden), la clasificación ABC y la antigüedad del stock. Cada
cambio queda en un historial de auditoría.

Proyecto académico (Programación III y Análisis y Diseño II). El estado
detallado y las decisiones tomadas están en `ESTADO_DEL_PROYECTO.md`; las
versiones exactas, en `STACK_VERSIONES.md`.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Django 5.1, Django REST Framework, SimpleJWT (login con token), drf-spectacular (Swagger), openpyxl (Excel) |
| Base de datos | PostgreSQL (desarrollo en el puerto 5433) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS 4, TanStack Query, Axios, lucide-react, motion |

## Requisitos

- **Python 3.12** (con el lanzador `py` de Windows o `python` en el PATH).
- **Node.js** 24 y npm 11 (sirve cualquier Node LTS reciente).
- **PostgreSQL** 16 o superior, con una base `eoq_db` y un usuario dueño
  de ella con permiso `CREATEDB` (las pruebas crean una base temporal).
- Git.

## Instalación en Windows

Los comandos son para PowerShell, desde la carpeta del repositorio.

### 1. Base de datos

En `psql` (o pgAdmin), como superusuario:

```sql
CREATE USER eoq_user WITH PASSWORD '<contraseña>' CREATEDB;
CREATE DATABASE eoq_db OWNER eoq_user;
```

### 2. Backend

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1          # si PowerShell lo bloquea: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
Copy-Item .env.example .env
```

Abrir `backend\.env` y completar:

- `DJANGO_SECRET_KEY`: una clave propia. Para generarla:
  `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`
- `DATABASE_URL`: `postgres://eoq_user:<contraseña>@localhost:5433/eoq_db`
  (cambiar el puerto si PostgreSQL usa otro, normalmente 5432).
- `DEBUG=True` solo en desarrollo.

Después:

```powershell
python manage.py migrate
python manage.py createsuperuser      # la primera cuenta, para entrar a /admin/
```

`createsuperuser` deja la cuenta con el rol Empleado. Con el servidor
levantado (paso 5), entrar a `http://localhost:8000/admin/`:

1. Usuarios → la cuenta recién creada → Rol: **Administrador** → Guardar.
2. Sucursales → Agregar, una por sucursal.

Desde ahí, las demás cuentas se crean en la pantalla Cuentas del sistema.

### 3. Datos de demo (opcional)

Con al menos una sucursal y un Administrador activos:

```powershell
$env:DEMO_PASSWORD = "<contraseña-de-demo>"
python manage.py cargar_demo --usuarios
Remove-Item Env:DEMO_PASSWORD
```

- `--usuarios` crea, si no existen, un Supervisor y un Empleado por
  sucursal activa (`supervisor_central`, `empleado_central`, …) con la
  contraseña de `DEMO_PASSWORD`. Sin esa variable, el comando se detiene.
  Nunca modifica cuentas que ya existen.
- Sin opciones, carga 4 proveedores, 20 herramientas con foto y 12 meses
  de movimientos, solo si todavía no hay herramientas.
- `--reiniciar` reemplaza el inventario (no toca usuarios, sucursales ni
  auditoría). Respaldar antes con
  `python manage.py dumpdata > respaldos\eoq_db.json`.

### 4. Frontend

En otra terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

### 5. Levantar los dos servidores

Terminal 1, backend (http://localhost:8000, Swagger en `/api/docs/`):

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

Terminal 2, frontend (http://localhost:5173):

```powershell
cd frontend
npm run dev
```

Vite redirige `/api` al backend, así que se entra solo por
`http://localhost:5173`.

Después de cada `git pull`: `python manage.py migrate` y, si cambiaron,
`pip install -r requirements.txt` y `npm install`.

## Pruebas y verificaciones

```powershell
# Backend (desde backend\, con el venv activo)
python manage.py test apps

# Frontend (desde frontend\)
npx tsc -b          # tipos
npx oxlint src      # lint
npx vite build      # compilación de producción
```

## Estructura de carpetas

### Backend (`backend/`)

```
config/                 settings.py (lee .env), urls.py
apps/
  usuarios/             cuentas, roles, sucursales, login JWT
  catalogo/             herramientas, fotos, costos, promociones; comandos cargar_demo y cargar_fotos_demo
  proveedores/
  movimientos/          entradas, salidas, ajustes y stock
  transferencias/
  indicadores/          EOQ, ROP, ABC, panel, cierre diario, antigüedad, Excel (sin tablas propias)
  auditoria/            historial de cambios (signals)
media/                  fotos subidas (no se versiona)
```

Cada app sigue Clean Architecture:

```
<app>/
  domain/               entidades y reglas puras (sin Django)
  use_cases/            casos de uso; reciben repositorios como interfaces
  infrastructure/       modelos ORM, repositorios concretos, migrations/
  interfaces/api/       serializers, vistas y urls de DRF (solo orquestan)
  tests.py
```

### Frontend (`frontend/src/`)

```
app/                    router.tsx, layout/ (barra lateral), providers/ (tema, TanStack Query)
components/ui/          sistema de diseño: Button, Input, PasswordInput, Field, Modal, Table…
features/<feature>/     auth, catalogo, movimientos, transferencias, promociones, proveedores,
                        dashboard, reportes, usuarios, auditoria
  api/                  llamadas a la API
  hooks/                hooks de TanStack Query
  components/
  pages/
shared/                 api/ (cliente HTTP, tokens, errores), formato/ (fechas en hora de La Paz), hooks/, types/
```

Las reglas visuales están en `docs/DISENO.md`.

## Roles

| Puede… | Administrador | Supervisor | Empleado |
|---|:-:|:-:|:-:|
| Ver panel, catálogo, stock, indicadores (EOQ, ROP, ABC), proveedores y promociones | ✔ | ✔ | ✔ |
| Registrar entradas y salidas | Todas las sucursales | Todas las sucursales | Solo su sucursal |
| Registrar ajustes de stock (con motivo) | ✔ | ✔ | — |
| Solicitar transferencias | ✔ | ✔ | Solo desde su sucursal |
| Completar o rechazar transferencias | ✔ | ✔ | — |
| Crear, editar y borrar herramientas | ✔ | ✔ (sin cambiar el costo) | — |
| Cambiar el costo unitario | ✔ | — | — |
| Poner y quitar promociones | Todas las sucursales | Su sucursal | — |
| Cierre diario y antigüedad del stock (y su Excel) | Todas las sucursales | Su sucursal | — |
| Ver la auditoría | ✔ | ✔ | — |
| Gestionar proveedores | ✔ | — | — |
| Gestionar cuentas (crear, editar, desactivar, restablecer contraseña) | ✔ | — | — |

Supervisor y Empleado siempre tienen una sucursal asignada; el
Administrador es global. Las cuentas no se borran: se desactivan.

## Seguridad

- `DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL` y
  `CORS_ALLOWED_ORIGINS` salen de `backend/.env`, que no se versiona. Sin
  `DJANGO_SECRET_KEY`, Django no arranca.
- Toda la API exige token salvo el login (`/api/token/`) y su renovación.
  La documentación Swagger es pública solo con `DEBUG=True`.
- El token de acceso dura 30 minutos y el de renovación, 1 día.
