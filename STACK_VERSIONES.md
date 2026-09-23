# Versiones del stack — Inventario Multisucursal (WALL-E)

Versiones **exactas** instaladas y verificadas en la máquina de desarrollo
el **22/09/2026** (salida real de `python --version`, `pip freeze`,
`npm ls --depth=0` y `SELECT version();`, no copiadas de otro documento).

Si alguien del equipo tiene otra versión de algo de esta lista, lo que vale
es esta tabla: actualizar su entorno o, si el cambio es a propósito,
actualizar este archivo en el mismo commit.

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Python | **3.12.10** | venv en `backend/venv` (`backend/.python-version` = 3.12) |
| Node.js | **24.14.0** | |
| npm | **11.9.0** | |
| PostgreSQL | **18.6** (x86_64-windows) | Instalación **nativa** (servicio `postgresql-x64-18`), puerto **5433**. No se usa Docker. |
| Git | 2.52.0.windows.1 | |

Base de datos de desarrollo: `eoq_db`, usuario `eoq_user` (con permiso
`CREATEDB`, necesario para que `manage.py test` cree la base de pruebas).

## Backend — `backend/requirements.txt`

`pip freeze` coincide exactamente con `requirements.txt` (sin diferencias).

| Paquete | Versión | Para qué |
|---|---|---|
| Django | **5.1.15** | Framework web / ORM |
| djangorestframework | **3.17.2** | API REST |
| djangorestframework_simplejwt | **5.5.1** | Login JWT (access 30 min, refresh 1 día) |
| PyJWT | 2.13.0 | (dependencia de simplejwt) |
| drf-spectacular | **0.30.0** | OpenAPI / Swagger en `/api/docs/` |
| django-cors-headers | **4.9.0** | CORS frontend (5173) ↔ backend (8000) |
| django-environ | **0.14.0** | Lee `backend/.env` |
| psycopg | **3.3.5** | Driver PostgreSQL (v3, no psycopg2) |
| psycopg-binary | 3.3.5 | |
| asgiref | 3.12.1 | (dependencia de Django) |
| sqlparse | 0.6.0 | (dependencia de Django) |
| tzdata | 2026.3 | (dependencia de Django en Windows) |
| attrs | 26.1.0 | (dependencias de drf-spectacular) |
| inflection | 0.5.1 | |
| jsonschema | 4.26.0 | |
| jsonschema-specifications | 2025.9.1 | |
| referencing | 0.37.0 | |
| rpds-py | 2026.6.3 | |
| PyYAML | 6.0.3 | |
| uritemplate | 4.2.0 | |
| typing_extensions | 4.16.0 | |

## Frontend — `frontend/package.json`

Instalado = versión fijada en `package-lock.json` para todos los paquetes.

| Paquete | Instalada | Rango en package.json |
|---|---|---|
| react | **18.3.1** | ^18.3.1 (React 18 a propósito, no 19) |
| react-dom | **18.3.1** | ^18.3.1 |
| react-router-dom | **7.18.3** | ^7.18.3 |
| @tanstack/react-query | **5.102.8** | ^5.102.8 |
| axios | **1.20.0** | ^1.20.0 |
| vite | **8.2.2** | ^8.2.2 |
| @vitejs/plugin-react | 6.1.1 | ^6.1.0 |
| typescript | **6.0.3** | ~6.0.2 |
| tailwindcss | **4.3.3** | ^4.3.3 (plugin `@tailwindcss/vite`, sin tailwind.config.js) |
| @tailwindcss/vite | 4.3.3 | ^4.3.3 |
| oxlint | 1.82.0 | ^1.79.0 |
| @types/react | 18.3.31 | ^18.3.31 |
| @types/react-dom | 18.3.7 | ^18.3.7 |
| @types/node | 24.13.3 | ^24.13.3 |

> Levantar el frontend siempre con `npm run dev` desde `frontend/` (o
> `npm --prefix frontend run dev`). `npx vite` fuera de esa carpeta no
> encuentra el Vite del proyecto y descarga otra versión.

## Cómo volver a verificar

```bash
backend/venv/Scripts/python.exe --version
backend/venv/Scripts/python.exe -m pip freeze   # comparar con backend/requirements.txt
cd frontend && npm ls --depth=0
# en psql o desde Django:  SELECT version();  SHOW port;
```
