# Guía de estudio del código (WALL-E · Inventario multisucursal)

Guía para defender el proyecto ante el ingeniero. Cada respuesta dice
**dónde está** (archivo y línea) y **cómo se hizo** (fragmento corto del
código real). Las rutas son relativas a la raíz del repositorio. Los números
de línea corresponden al código del commit en que se agregó esta guía: si
después se edita un archivo, pueden correrse unas líneas; busca el nombre de
la función.

Cómo usarla: lee primero el mapa general (sección 1), después recorre los
flujos (sección 2) abriendo cada archivo en el editor. Las secciones 4 y 5
sirven de repaso rápido antes de la defensa.

---

## Índice

1. [Mapa general](#1-mapa-general)
2. [Flujos de punta a punta](#2-flujos-de-punta-a-punta)
   - 2.1 Login
   - 2.2 Crear una herramienta con foto (y el recorte)
   - 2.3 Registrar una salida
   - 2.4 Transferencia: solicitar y completar
   - 2.5 EOQ, ROP y ABC, y cómo llegan al Panel
   - 2.6 Poner una promoción como Supervisor
   - 2.7 Exportar a Excel
   - 2.8 Auditoría con signals
3. [Frontend en detalle](#3-frontend-en-detalle)
4. [Dónde está cada cosa (40 preguntas)](#4-dónde-está-cada-cosa)
5. [20 preguntas probables de defensa](#5-20-preguntas-probables-de-defensa)
6. [Glosario](#6-glosario)

---

## 1. Mapa general

### 1.1 Cómo se conectan las tres partes

```
 Navegador (React, puerto 5173)
   │  axios: GET/POST /api/...  + cabecera  Authorization: Bearer <token>
   ▼
 Vite (solo en desarrollo) ── proxy /api ──►  Django + DRF (puerto 8000)
                                                │  vistas → casos de uso → repositorios
                                                ▼
                                             ORM de Django
                                                │  SQL
                                                ▼
                                             PostgreSQL (base eoq_db)
```

1. **Frontend → backend.** Todas las pantallas llaman a la API con un solo
   cliente axios, `frontend/src/shared/api/httpClient.ts`. Su `baseURL` es
   `/api` (línea 14):

   ```ts
   const baseURL = import.meta.env.VITE_API_URL ?? '/api'
   ```

   En desarrollo, Vite redirige `/api` al backend
   (`frontend/vite.config.ts:12-17`):

   ```ts
   proxy: {
     '/api': {
       target: 'http://localhost:8000',
       changeOrigin: true,
     },
   },
   ```

2. **Backend.** `backend/config/urls.py:17-33` solo arma las rutas: el login
   (`api/token/`), Swagger y un prefijo por app:

   ```python
   path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
   path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
   ...
   path("api/catalogo/", include("apps.catalogo.interfaces.api.urls")),
   path("api/movimientos/", include("apps.movimientos.interfaces.api.urls")),
   ```

3. **Backend → base de datos.** La conexión sale del `.env`
   (`backend/config/settings.py:96-98`):

   ```python
   DATABASES = {
       "default": env.db("DATABASE_URL"),
   }
   ```

   Cada modelo define el nombre de su tabla con `db_table`: `herramientas`
   (`catalogo/infrastructure/models.py:80`), `historial_costos` (:109),
   `promociones` (:146), `movimientos`
   (`movimientos/infrastructure/models.py:52`), `transferencias`
   (`transferencias/infrastructure/models.py:87`), `proveedores`
   (`proveedores/infrastructure/models.py:19`), `sucursales` y `usuarios`
   (`usuarios/infrastructure/models.py:44` y `:92`),
   `historial_modificaciones` (`auditoria/infrastructure/models.py:46`).

### 1.2 Carpetas del frontend (`frontend/src/`)

| Carpeta | Qué tiene | Ejemplo |
|---|---|---|
| `app/` | Lo que arma la aplicación entera: el router, el marco con la barra lateral y los providers globales. | `app/router.tsx`, `app/layout/Sidebar.tsx`, `app/layout/navegacion.ts`, `app/providers/ThemeProvider.tsx`, `app/providers/QueryProvider.tsx` |
| `components/ui/` | El sistema de diseño: piezas reutilizables sin lógica de negocio. Ninguna pantalla escribe colores a mano, usa estas. | `Button.tsx`, `Input.tsx`, `PasswordInput.tsx`, `Field.tsx`, `Modal.tsx`, `Table.tsx`, `index.ts` |
| `features/<feature>/` | Una carpeta por funcionalidad (`auth`, `catalogo`, `movimientos`, `transferencias`, `promociones`, `proveedores`, `dashboard`, `reportes`, `usuarios`, `auditoria`). Cada una tiene `api/`, `hooks/`, `components/` y `pages/`. | `features/catalogo/api/catalogoApi.ts`, `features/catalogo/hooks/useHerramientas.ts`, `features/catalogo/pages/CatalogoPage.tsx` |
| `shared/` | Lo que usan varias features y no es visual: el cliente HTTP, los tokens, los errores, los formatos de fecha y número, hooks genéricos y los tipos de rol. | `shared/api/httpClient.ts`, `shared/api/tokenStorage.ts`, `shared/api/errores.ts`, `shared/formato/index.ts`, `shared/types/roles.ts` |

Regla: `shared/` no importa nada de `features/` (lo dice el comentario de
`shared/api/tokenStorage.ts:1-3`), y las features no dependen entre sí para
navegar: solo `app/router.tsx` conoce todas las páginas
(`app/router.tsx:32-34`).

### 1.3 Capas de cada app del backend (`backend/apps/<app>/`)

Apps: `usuarios`, `catalogo`, `proveedores`, `movimientos`,
`transferencias`, `indicadores` (sin tablas propias) y `auditoria`. Todas
siguen Clean Architecture con cuatro capas:

| Capa | Qué tiene | ¿Conoce Django? | Ejemplo |
|---|---|---|---|
| `domain/` | Entidades (dataclasses), value objects (enums), excepciones y reglas puras. También las **interfaces** de repositorio (clases abstractas). | No | `movimientos/domain/stock.py`, `indicadores/domain/formulas.py`, `usuarios/domain/value_objects.py` |
| `use_cases/` | Los casos de uso: las reglas de negocio. Reciben los repositorios como parámetro (la interfaz, nunca el ORM). | No | `movimientos/use_cases/registrar_movimiento.py` |
| `infrastructure/` | Modelos del ORM, repositorios concretos que traducen modelo ↔ entidad, y las migraciones (`infrastructure/migrations/`). | Sí | `movimientos/infrastructure/models.py`, `movimientos/infrastructure/repositories.py` |
| `interfaces/api/` | Serializers, vistas y urls de DRF. La vista valida la forma, llama al caso de uso y traduce excepciones a HTTP. | Sí | `movimientos/interfaces/api/views.py` |

Que el dominio no dependa de Django lo explica
`backend/apps/usuarios/domain/repositories.py:1-12`:

```python
Son ABCs sin ninguna dependencia de Django. use_cases depende de estas
interfaces, no de una implementación concreta (Inversión de Dependencias):
así los casos de uso se pueden probar con un fake/mock que las implemente,
sin necesitar una base de datos real.
```

Las migraciones se movieron a `infrastructure/` en
`backend/config/settings.py:105-112` (`MIGRATION_MODULES`).

---

## 2. Flujos de punta a punta

### 2.1 Login: del botón a `/api/token/`

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | El usuario escribe usuario y contraseña. El campo de contraseña es `PasswordInput` con `autoComplete="current-password"`. | `frontend/src/features/auth/pages/LoginPage.tsx:51-74` |
| 2 | Al enviar, `handleSubmit` evita la recarga y llama a `mutate` del hook `useLogin`. | `LoginPage.tsx:21-27` |
| 3 | `useLogin` es un `useMutation` cuya función es `login` y que al tener éxito llama a `saveSession`. | `features/auth/hooks/useLogin.ts:8-13` |
| 4 | `login` hace `POST /token/` (sobre `baseURL` `/api` → `/api/token/`). | `features/auth/api/authApi.ts:15-18` |
| 5 | El backend recibe en `api/token/` la vista `CustomTokenObtainPairView`. | `backend/config/urls.py:20`, `backend/apps/usuarios/interfaces/api/views.py:34-38` |
| 6 | El serializer agrega al token el rol, la sucursal y el nombre. | `backend/apps/usuarios/interfaces/api/serializers.py:57-66` |
| 7 | El frontend guarda los dos tokens en `localStorage`. | `features/auth/session.ts:42-44` → `shared/api/tokenStorage.ts:15-18` |
| 8 | `LoginPage` navega a `/`. | `LoginPage.tsx:25` |
| 9 | Desde ahí, **cada** petición lleva el token: lo agrega el interceptor de axios. | `shared/api/httpClient.ts:24-30` |

**Paso 2, el botón** (`LoginPage.tsx:21-27`):

```tsx
function handleSubmit(event: FormEvent) {
  event.preventDefault()
  mutate(
    { username, password },
    { onSuccess: () => navigate('/', { replace: true }) },
  )
}
```

Si el backend responde 401, el error se muestra dentro del formulario
(`LoginPage.tsx:29-35`): "Usuario o contraseña incorrectos.".

**Paso 4, la llamada** (`authApi.ts:15-18`):

```ts
export async function login(credentials: LoginCredentials): Promise<TokenPair> {
  const { data } = await httpClient.post<TokenPair>('/token/', credentials)
  return data
}
```

**Paso 6, lo que lleva el token** (`usuarios/interfaces/api/serializers.py:58-66`):

```python
def get_token(cls, user):
    token = super().get_token(user)
    token["username"] = user.username
    token["first_name"] = user.first_name
    token["last_name"] = user.last_name
    token["rol"] = user.rol
    token["sucursal_id"] = user.sucursal_id
    token["sucursal_nombre"] = user.sucursal.nombre if user.sucursal_id else None
    return token
```

**Paso 7, dónde se guarda** (`shared/api/tokenStorage.ts:4-5` y `15-18`):

```ts
const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
...
export function saveTokens(access: string, refresh?: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}
```

**Paso 9, el interceptor que agrega el token** (`httpClient.ts:24-30`):

```ts
httpClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})
```

**Renovación automática.** El access token dura 30 minutos y el refresh, un
día (`backend/config/settings.py:164-168`). Cuando una petición recibe 401,
el interceptor de respuesta pide un access nuevo a `/token/refresh/` y
reintenta una sola vez (`httpClient.ts:59-83`). Si varias peticiones fallan
a la vez, todas esperan el mismo refresh (`refreshEnCurso`, línea 38). Si el
refresh también falla, borra los tokens y manda a `/login`
(`httpClient.ts:77-80`):

```ts
} catch {
  clearTokens()
  window.location.assign('/login')
  return Promise.reject(error)
}
```

**Leer la sesión sin pedirle nada al backend.** `getSession` decodifica la
parte central del JWT (base64) y revisa `exp`
(`features/auth/session.ts:27-40` y `56-63`). Así la barra lateral sabe el
rol sin un endpoint `/me`.

**Cerrar sesión.** No hay endpoint: se borran los tokens y se navega a
`/login` (`features/auth/hooks/useLogout.ts:6-12`).

**Del lado del backend**, toda la API exige token por defecto
(`backend/config/settings.py:152-158`):

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
```

---

### 2.2 Crear una herramienta con foto (incluido el recorte)

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | La página del catálogo lista con `useHerramientas` y abre el formulario en un panel lateral. | `features/catalogo/pages/CatalogoPage.tsx:104` y `:322` |
| 2 | El formulario incluye `FotoDropzone`, que entrega la foto ya recortada con `onCambiar`. | `features/catalogo/components/HerramientaForm.tsx:165-170` |
| 3 | Al elegir el archivo se valida el tipo y el peso, y se centra la imagen. | `features/catalogo/components/FotoDropzone.tsx:53-74` |
| 4 | Al mover o hacer zoom, se recalcula el encuadre y se exporta un JPEG cuadrado con `<canvas>`. | `FotoDropzone.tsx:44-51`, `features/catalogo/components/recorte.ts:52-67` |
| 5 | Al enviar, el formulario exige la foto en el alta y llama a `crear.mutate`. | `HerramientaForm.tsx:109-136` |
| 6 | La API arma un `FormData` (multipart) con los campos y la foto. | `features/catalogo/api/catalogoApi.ts:43-63` |
| 7 | Al tener éxito se invalida la caché `['herramientas']` y la tabla se recarga sola. | `features/catalogo/hooks/useCrearHerramienta.ts:6-12` |
| 8 | En el backend, `create` valida con `HerramientaAltaSerializer` (foto obligatoria) y abre una transacción. | `backend/apps/catalogo/interfaces/api/views.py:78-92` |
| 9 | El caso de uso valida reglas (código único, formato y peso de la foto, costo) y guarda. | `backend/apps/catalogo/use_cases/gestionar_herramientas.py:149-170` |
| 10 | El repositorio guarda la foto en `media/productos/` con un nombre propio y hace un solo `save()`. | `backend/apps/catalogo/infrastructure/repositories.py:71-100`, `infrastructure/models.py:71-72` |

**El recorte, paso a paso** (`recorte.ts`):

- Tipos y tamaño aceptados (líneas 6-7) y validación (17-21):

  ```ts
  export const TIPOS_ACEPTADOS = ['image/jpeg', 'image/png', 'image/webp']
  export const TAMANO_MAXIMO = 5 * 1024 * 1024
  ```

- `escala` (24-26) calcula cuánto agrandar la imagen para que cubra el visor
  cuadrado; `limitar` (29-34) impide que queden bordes vacíos al arrastrar;
  `centrado` (37-40) es el encuadre inicial; `conZoom` (43-49) hace zoom
  manteniendo fijo el centro.
- `exportarRecorte` (52-67) dibuja en un canvas de 1024 × 1024 (`LADO_SALIDA`,
  línea 9) la parte visible y la convierte a JPEG con calidad 0,9:

  ```ts
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, LADO_SALIDA, LADO_SALIDA)
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(imagen, -e.x / s, -e.y / s, lado / s, lado / s, 0, 0, LADO_SALIDA, LADO_SALIDA)
  return new Promise((resolver, rechazar) =>
    canvas.toBlob((blob) => (blob ? resolver(blob) : rechazar(new Error('No se pudo recortar la imagen.'))), 'image/jpeg', 0.9),
  )
  ```

  El fondo blanco evita que un PNG transparente quede negro al pasar a JPEG.

- En el componente, `entregar` espera un momento (`setTimeout`) antes de
  exportar, para no recortar en cada píxel del arrastre
  (`FotoDropzone.tsx:44-51`):

  ```ts
  function entregar(imagen: HTMLImageElement, e: Encuadre, demora = 0) {
    window.clearTimeout(espera.current)
    espera.current = window.setTimeout(() => {
      exportarRecorte(imagen, e, LADO)
        .then(onCambiar)
  ```

  El arrastre usa eventos de puntero (`alPresionar`, `alArrastrar`,
  `alSoltarPuntero`, líneas 89-106) y el zoom un control deslizante
  (líneas 170-179).

**El envío** (`HerramientaForm.tsx:114` y `131-135`):

```tsx
if (!editando && !foto) locales.imagen = 'La foto del producto es obligatoria.'
...
if (herramienta) {
  actualizar.mutate({ id: herramienta.id, ...payload, imagen: foto }, { onSuccess: onTerminar })
} else if (foto) {
  crear.mutate({ ...payload, imagen: foto }, { onSuccess: onTerminar })
}
```

**El multipart** (`catalogoApi.ts:43-50` y `60-63`):

```ts
function aFormData(payload: HerramientaPayload, imagen: Blob): FormData {
  const datos = new FormData()
  for (const [campo, valor] of Object.entries(payload)) {
    datos.append(campo, valor === null ? '' : String(valor))
  }
  datos.append('imagen', imagen, 'foto.jpg')
  return datos
}
```

**La vista** (`catalogo/interfaces/api/views.py:79-92`):

```python
def create(self, request):
    # Acepta JSON o multipart; la foto es obligatoria (HerramientaAltaSerializer).
    serializer = HerramientaAltaSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    datos = dict(serializer.validated_data)
    imagen = datos.pop("imagen")
    # La herramienta, su foto y su fila de historial de costos, juntas o ninguna.
    with transaction.atomic():
        herramienta = self._ejecutar(
            casos.registrar_herramienta, datos, ...
```

**El backend no confía en la extensión.** `ImageField` abre el archivo con
Pillow y el formato sale del contenido real
(`catalogo/interfaces/api/serializers.py:21-27`). El caso de uso acepta solo
JPG, PNG o WebP de hasta 5 MB (`gestionar_herramientas.py:109-117`, con las
constantes en `catalogo/domain/entities.py:44-45`).

**El caso de uso** (`gestionar_herramientas.py:162-170`):

```python
nueva = _validar(nueva)
_validar_imagen(imagen)
_verificar_codigo_unico(repo, nueva)
_verificar_proveedor(proveedores, None, nueva)
cambia_costo = _verificar_cambio_de_costo(actor, None, nueva)
guardada = repo.guardar(nueva, imagen)
if cambia_costo:
    _registrar_cambio_de_costo(historial, actor, None, guardada)
return guardada
```

**El repositorio** guarda la foto con el código de la herramienta como nombre
y `save=False`, para que vaya en el mismo INSERT que el resto
(`catalogo/infrastructure/repositories.py:85-86`):

```python
nombre = f"{slugify(herramienta.codigo) or 'herramienta'}.{_EXTENSION_POR_FORMATO.get(imagen.formato, 'img')}"
modelo.imagen.save(nombre, imagen.contenido, save=False)
```

Si la base rechaza el código por duplicado, borra el archivo recién subido
(líneas 92-97).

---

### 2.3 Registrar una salida

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | Al Empleado se le fija su sucursal en el formulario. | `features/movimientos/pages/MovimientosPage.tsx:55` |
| 2 | El formulario muestra el equivalente en unidades si se eligió "Cajas" (solo informativo). | `features/movimientos/components/MovimientoForm.tsx:32-33` y `:92` |
| 3 | `handleSubmit` envía herramienta, sucursal, tipo, unidad y cantidad. | `MovimientoForm.tsx:40-52` |
| 4 | `POST /api/movimientos/`. | `features/movimientos/api/movimientosApi.ts:69-70` |
| 5 | Al tener éxito se invalidan `['movimientos']` y `['stock']`. | `features/movimientos/hooks/useMovimientos.ts:25-35` |
| 6 | La vista elige `registrar_salida` y lo corre **dentro de `transaction.atomic()`**. | `backend/apps/movimientos/interfaces/api/views.py:111-121` y `81-108` |
| 7 | El caso de uso valida, convierte cajas a unidades, bloquea y verifica el stock. | `backend/apps/movimientos/use_cases/registrar_movimiento.py:63-123` |
| 8 | El bloqueo es un `SELECT ... FOR UPDATE` sobre la fila de la herramienta. | `backend/apps/movimientos/infrastructure/repositories.py:113-117` |
| 9 | El stock se calcula sumando y restando movimientos; no se guarda en ninguna tabla. | `backend/apps/movimientos/domain/stock.py:14-21` y `39-45` |
| 10 | Si no alcanza, la vista responde 400 con el mensaje "Stock insuficiente…". | `views.py:101-107` |

**Conversión de cajas a unidades** (`registrar_movimiento.py:93-99`):

```python
tipo_unidad = TipoUnidad(tipo_unidad)
if unidades_fijas is not None:
    unidades = unidades_fijas
elif tipo_unidad == TipoUnidad.CAJA:
    unidades = cajas_a_unidades(cantidad, herramienta.unidades_por_caja)
else:
    unidades = cantidad
```

`cajas_a_unidades` vive en `backend/apps/indicadores/domain/formulas.py:87-97`
y es una multiplicación con validaciones:

```python
if unidades_por_caja <= 0:
    raise ValueError("unidades_por_caja debe ser mayor que 0.")
if cantidad_cajas < 0:
    raise ValueError("La cantidad de cajas no puede ser negativa.")
return cantidad_cajas * unidades_por_caja
```

El movimiento guarda las dos cosas: `cantidad` (lo que escribió el usuario) y
`cantidad_unidades` (el equivalente fijo,
`movimientos/infrastructure/models.py:40-43`). El stock se calcula con
`cantidad_unidades`, así que si mañana cambia el tamaño de caja, el
historial no cambia.

**Validación de stock con bloqueo** (`registrar_movimiento.py:101-109`):

```python
if resta_stock(tipo):
    # Salidas y ajustes negativos pasan por el MISMO bloqueo: se toma
    # ANTES de leer el stock, así si otra operación que resta stock de
    # esta herramienta está en curso, esta espera a que termine y ve el
    # stock ya descontado.
    movimientos.bloquear_stock(herramienta_id)
    disponible = _stock_actual(movimientos, herramienta_id, sucursal_id)
    if unidades > disponible:
        raise StockInsuficienteError(disponible=disponible, solicitado=unidades)
```

**El `select_for_update`** (`movimientos/infrastructure/repositories.py:113-117`):

```python
def bloquear_stock(self, herramienta_id: int) -> None:
    # SELECT ... FOR UPDATE sobre la fila de la herramienta: toda salida
    # de esa herramienta pasa por acá, así que quedan en fila una tras
    # otra. Requiere una transacción abierta (la abre la vista).
    list(HerramientaModel.objects.select_for_update().filter(pk=herramienta_id).values_list("pk"))
```

**Por qué hace falta.** Sin bloqueo, dos vendedores podrían leer "hay 5" al
mismo tiempo, vender 5 cada uno y dejar el stock en −5. Con el bloqueo, el
segundo espera a que el primero termine su transacción y lee "hay 0". La
transacción la abre la vista (`movimientos/interfaces/api/views.py:89`):

```python
with transaction.atomic():
    movimiento = registrar(self.movimientos, self.herramientas, self.sucursales, *args)
```

La prueba `test_salida_bloquea_el_stock_antes_de_validar`
(`backend/apps/movimientos/tests.py:137`) comprueba que se bloquea.

**Cómo se deriva el stock** (`movimientos/domain/stock.py:14-21` y `39-45`):

```python
EFECTO_EN_STOCK = {
    TipoMovimiento.ENTRADA: +1,
    TipoMovimiento.SALIDA: -1,
    TipoMovimiento.AJUSTE_POSITIVO: +1,
    TipoMovimiento.AJUSTE_NEGATIVO: -1,
    TipoMovimiento.TRANSFERENCIA_SALIDA: -1,
    TipoMovimiento.TRANSFERENCIA_ENTRADA: +1,
}
...
def stock_desde_totales(unidades_por_tipo: dict[TipoMovimiento, int]) -> int:
    return sum(
        EFECTO_EN_STOCK[TipoMovimiento(tipo)] * unidades
        for tipo, unidades in unidades_por_tipo.items()
    )
```

Los totales por tipo salen de **una** consulta agregada con `SUM`
(`movimientos/infrastructure/repositories.py:63-69`):

```python
filas = (
    MovimientoModel.objects.filter(herramienta_id=herramienta_id, sucursal_id=sucursal_id)
    .values("tipo_movimiento")
    .annotate(total=Sum("cantidad_unidades"))
)
```

Los movimientos **no se editan ni se borran**: el repositorio lo rechaza
(`repositories.py:120-121`) y la vista no tiene PUT/PATCH/DELETE
(`views.py:42-44`). Un error se corrige con un ajuste
(`registrar_movimiento.py:165-188`), que solo pueden hacer Administrador y
Supervisor, con motivo obligatorio.

---

### 2.4 Transferencia: solicitar y completar

Estados: `PENDIENTE`, `COMPLETADA`, `RECHAZADA`
(`backend/apps/transferencias/domain/value_objects.py:4-7`). El resumen del
flujo está en el docstring de
`backend/apps/transferencias/use_cases/gestionar_transferencias.py:9-18`.

**Solicitar**

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | El formulario llama a `useSolicitarTransferencia().mutate`. | `features/transferencias/components/SolicitudForm.tsx:31` y `:48` |
| 2 | `POST /api/transferencias/`. | `features/transferencias/api/transferenciasApi.ts:44-46` |
| 3 | La vista valida y llama a `solicitar_transferencia`. | `backend/apps/transferencias/interfaces/api/views.py:89-112` |
| 4 | Un Empleado solo puede pedir desde su sucursal. | `gestionar_transferencias.py:83-84` |
| 5 | Convierte cajas a unidades y valida el stock en origen **sin bloquear** (aviso temprano). | `gestionar_transferencias.py:86-96` |
| 6 | Se guarda como `PENDIENTE`. **El stock todavía no se mueve.** | `gestionar_transferencias.py:98-108` |

```python
# Validación temprana (sin bloqueo): avisar ya si no alcanza. La
# definitiva, con bloqueo, se hace al completar.
disponible = stock_disponible(movimientos, herramienta_id, sucursal_origen_id)
if unidades > disponible:
    raise StockInsuficienteError(disponible=disponible, solicitado=unidades)
```

**Completar**

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | Solo Administrador y Supervisor ven los botones. | `features/transferencias/permisos.ts:6-8` |
| 2 | El botón llama a `completar.mutate(t.id)`. | `features/transferencias/components/TablaTransferencias.tsx:86-87` |
| 3 | `POST /api/transferencias/<id>/completar/`. | `transferenciasApi.ts:50-52` |
| 4 | La vista corre el caso de uso dentro de `transaction.atomic()`. | `transferencias/interfaces/api/views.py:114-118` y `145-150` |
| 5 | Verifica rol y que siga `PENDIENTE`, bloqueando la fila de la transferencia con `select_for_update`. | `gestionar_transferencias.py:111-121`, `transferencias/infrastructure/repositories.py:62` |
| 6 | Registra la salida en origen y la entrada en destino reutilizando el caso de uso de movimientos (mismo bloqueo y validación de stock). | `gestionar_transferencias.py:136-145`, `movimientos/use_cases/registrar_movimiento.py:136-159` |
| 7 | Marca la transferencia `COMPLETADA` con quién y cuándo, y guarda los ids de los dos movimientos. | `gestionar_transferencias.py:146-153` |
| 8 | Si el stock ya no alcanza, responde 409 y no se mueve nada. | `transferencias/interfaces/api/views.py:128-134` |
| 9 | En el frontend se invalidan `transferencias`, `stock`, `movimientos` y `panel`. | `features/transferencias/hooks/useTransferencias.ts:16-23` |

El caso de uso (`gestionar_transferencias.py:135-153`):

```python
transferencia = _pendiente_para_resolver(transferencias, actor, transferencia_id)
salida, entrada = registrar_movimientos_de_transferencia(
    movimientos, herramientas, sucursales, actor,
    transferencia.herramienta_id,
    transferencia.sucursal_origen_id,
    transferencia.sucursal_destino_id,
    transferencia.tipo_unidad,
    transferencia.cantidad,
    transferencia.cantidad_unidades,
    referencia=f"Transferencia #{transferencia.id}",
)
return transferencias.guardar(replace(
    transferencia,
    estado=EstadoTransferencia.COMPLETADA,
    ...
```

**Por qué una sola transacción.** La salida, la entrada y el cambio de estado
van juntos: si algo falla (por ejemplo, stock insuficiente en la salida), se
deshace todo y no queda stock "en el aire". Y como la fila de la
transferencia está bloqueada, dos supervisores que aprietan "Completar" a la
vez no la completan dos veces: el segundo ve que ya no está `PENDIENTE` y
recibe 409 (`views.py:123-127`).

**Rechazar** pide motivo obligatorio y no toca el stock
(`gestionar_transferencias.py:156-173`, `views.py:152-160`).

---

### 2.5 EOQ, ROP y ABC, y cómo llegan al Panel

**Fórmulas puras** (`backend/apps/indicadores/domain/formulas.py`), sin
Django:

- EOQ, líneas 22-38: `EOQ = raiz(2 · D · S / H)`

  ```python
  if demanda_anual is None or costo_pedido is None:
      return None
  if costo_almacenamiento_unitario is None or costo_almacenamiento_unitario <= 0:
      return None
  ...
  return math.sqrt((2 * demanda_anual * costo_pedido) / costo_almacenamiento_unitario)
  ```

- ROP, líneas 41-53: `ROP = (D / 365) · días de entrega`

  ```python
  return (demanda_anual / DIAS_POR_ANIO) * tiempo_entrega_dias
  ```

- Qué D se usa, líneas 61-71: la demanda **observada** (salidas reales de
  los últimos 12 meses); si no hubo ventas, la estimada del catálogo.

  ```python
  if observada > 0:
      return observada, DEMANDA_OBSERVADA
  return estimada, DEMANDA_ESTIMADA
  ```

- Ajuste a cajas cerradas, líneas 74-84 (30 unidades con cajas de 12 → 36):

  ```python
  return math.ceil(cantidad_unidades / unidades_por_caja) * unidades_por_caja
  ```

**Qué cuenta como venta.** Solo `SALIDA`: ni ajustes ni transferencias
(`backend/apps/movimientos/domain/stock.py:23-26`):

```python
TIPOS_QUE_CUENTAN_COMO_DEMANDA = frozenset({TipoMovimiento.SALIDA})
```

Las ventas de 12 meses salen de una consulta para todas las herramientas
(`indicadores/use_cases/calcular_eoq.py:34-39`; el período es
`PERIODO_DEMANDA_DIAS = 365`, `indicadores/domain/entities.py:17`).

**Casos de uso**

- `resultado_eoq` (`calcular_eoq.py:42-72`) arma el resultado, incluidos los
  datos que faltan (por ejemplo, sin costo de almacenamiento) y el EOQ
  ajustado a cajas (línea 67).
- `resultado_rop` (`calcular_punto_reorden.py:28-51`) compara con el stock
  **total** de todas las sucursales (línea 49):

  ```python
  requiere_reorden=rop is not None and stock_total <= rop,
  ```

- ABC (`indicadores/use_cases/clasificar_abc.py:31-60`): ordena por unidades
  vendidas de mayor a menor y clasifica por el porcentaje acumulado
  **anterior** a cada herramienta. Umbrales `UMBRAL_A = 80.0` y
  `UMBRAL_B = 95.0` (`indicadores/domain/entities.py:21-22`).

  ```python
  if unidades == 0:
      clase = "C"
  elif acumulado < UMBRAL_A:
      clase = "A"
  elif acumulado < UMBRAL_B:
      clase = "B"
  else:
      clase = "C"
  acumulado += porcentaje
  ```

  Al usar el acumulado anterior, la más vendida siempre es A aunque ella sola
  supere el 80 % (docstring, líneas 11-12).

**El Panel** (`indicadores/use_cases/panel_auditoria.py:38-107`) **no tiene
fórmulas propias**: reutiliza `resultado_rop` y `resultado_eoq`
(líneas 72-92):

```python
vendidas = ventas_de_12_meses(movimientos, ahora)
...
for herramienta in catalogo.values():
    observada = vendidas.get(herramienta.id, 0)
    rop = resultado_rop(herramienta, stock_total[herramienta.id], observada)
    ...
    if rop.requiere_reorden:
        alertas.append(AlertaReorden(
            ...
            pedido_sugerido=resultado_eoq(herramienta, observada).eoq_ajustado_cajas,
```

También detecta las herramientas estancadas: con stock y más de
`DIAS_PARA_ESTANCAMIENTO = 40` días sin venta
(`panel_auditoria.py:52-70`, constante en `indicadores/domain/entities.py:88`).
Ordena lo más urgente primero (líneas 95-96).

**Endpoints** (`indicadores/interfaces/api/urls.py:18-22`): `eoq/<id>/`,
`rop/<id>/`, `abc/`, `abc/excel/`, `panel/`. La vista del panel
(`indicadores/interfaces/api/views.py:146-154`):

```python
def get(self, request):
    panel = construir_panel(
        MovimientoRepositoryDjango(),
        HerramientaRepositoryDjango(),
        SucursalRepositoryDjango(),
        hoy=timezone.localdate(),
        ahora=timezone.now(),
    )
    return Response(PanelAuditoriaSerializer(panel).data)
```

**Llegada al frontend**

1. `obtenerPanel` hace `GET /indicadores/panel/`
   (`features/dashboard/api/indicadoresApi.ts:105-106`).
2. `usePanel` lo envuelve en `useQuery` con la clave `['panel']`
   (`features/dashboard/hooks/usePanel.ts:6-8`).
3. `DashboardPage` muestra 4 tarjetas y 2 tablas
   (`features/dashboard/pages/DashboardPage.tsx:13`, `41-59`):

   ```tsx
   <StatTile
     etiqueta="Alertas de reorden"
     valor={panel.total_alertas_stock}
     alerta={panel.total_alertas_stock > 0}
   ...
   <TablaAlertasReorden alertas={panel.alertas} sinDatos={panel.herramientas_sin_datos_rop} limite={5} />
   <TablaEstancadas estancadas={panel.estancadas} dias={panel.dias_para_estancamiento} />
   ```

4. El punto de reorden se muestra con coma decimal mediante `decimal()`
   (`features/dashboard/components/TablasPanel.tsx:81`, función en
   `shared/formato/index.ts:65-67`).

EOQ y ROP de una herramienta usan `enabled` para no consultar hasta que se
elige una (`features/dashboard/hooks/useIndicadores.ts:9-23`).

---

### 2.6 Poner una promoción como Supervisor

Regla de negocio: solo se promociona una herramienta **estancada** (con
stock y más de 40 días sin venta) en esa sucursal, y solo puede haber una
promoción vigente por herramienta y sucursal. El Supervisor solo opera en su
sucursal; el Administrador, en todas.

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | En Antigüedad del stock aparece "Promocionar" solo si el rol puede gestionar en esa sucursal y la línea está estancada. | `features/reportes/pages/AntiguedadPage.tsx:178-179` |
| 2 | `puedeGestionarEn` decide en el frontend (solo para mostrar el botón). | `features/promociones/permisos.ts:10-13` |
| 3 | Se abre `PromocionForm`, que valida y llama a `crear.mutate`. | `AntiguedadPage.tsx:199`, `features/promociones/components/PromocionForm.tsx:60-75` |
| 4 | `POST /api/indicadores/promociones/`. | `features/promociones/api/promocionesApi.ts:41-43` |
| 5 | Al tener éxito se invalida `['promociones']`. | `features/promociones/hooks/usePromociones.ts:20-28` |
| 6 | La vista llama a `crear_promocion` y traduce los errores: 403 sin permiso, 400 datos inválidos, 409 si no aplica. | `backend/apps/indicadores/interfaces/api/views.py:278-299` |
| 7 | El caso de uso verifica rol, sucursal, datos, que esté estancada y que no haya otra vigente. | `backend/apps/indicadores/use_cases/promociones.py:79-119` |

Frontend (`features/promociones/permisos.ts:10-13`):

```ts
export function puedeGestionarEn(sesion: { rol: Rol; sucursal_id: number | null }, sucursalId: number): boolean {
  if (sesion.rol === Rol.ADMINISTRADOR) return true
  return sesion.rol === Rol.SUPERVISOR && sesion.sucursal_id === sucursalId
}
```

Backend, la misma regla, que es la que vale
(`indicadores/use_cases/promociones.py:61-64`):

```python
def _verificar_sucursal(actor: Actor, sucursal_id: int) -> None:
    """El Supervisor solo gestiona las promociones de su sucursal."""
    if Rol(actor.rol) == Rol.SUPERVISOR and actor.sucursal_id != sucursal_id:
        raise PromocionNoPermitidaError()
```

Que esté estancada y sin otra vigente (`promociones.py:99-108`):

```python
estancada = any(
    l.herramienta_id == herramienta_id and l.estancada
    for l in lineas_de_antiguedad(movimientos, herramientas, sucursales, hoy, sucursal_id)
)
if not estancada:
    raise PromocionNoAplicableError(...)
if any(p.vigente(hoy) for p in promociones.de_herramienta_en_sucursal(herramienta_id, sucursal_id)):
    raise PromocionNoAplicableError("Esta herramienta ya tiene una promoción vigente en esa sucursal.")
```

El descuento es opcional y la fecha de fin debe ser hoy o después
(`promociones.py:67-76`). Quitar una promoción antes de tiempo es
`terminar_promocion` (`promociones.py:122-130`), que la marca `activa=False`.

---

### 2.7 Exportar a Excel

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | La página pone el botón `ExportarExcel` con la URL del reporte. | `features/dashboard/pages/ClasificacionABCPage.tsx:19` (también en `AntiguedadPage.tsx:83` y `CierreDiarioPage.tsx:72`) |
| 2 | Si el reporte está vacío, avisa y no descarga. | `features/reportes/components/ExportarExcel.tsx:26-30` |
| 3 | `descargarArchivo` pide el archivo **con axios** (lleva el token) como `blob`. | `shared/api/descargar.ts:8-18` |
| 4 | El backend arma la clasificación, responde 409 si está vacía y genera el `.xlsx`. | `backend/apps/indicadores/interfaces/api/views.py:116-135` |
| 5 | `openpyxl` crea el libro en memoria: título, cabecera congelada, anchos y formatos. | `backend/apps/indicadores/interfaces/excel.py:57-96` |
| 6 | La respuesta lleva el tipo `xlsx` y `Content-Disposition: attachment; filename=...`. | `excel.py:99-102` |

**Por qué no un `<a href>`**: un enlace normal no manda la cabecera
`Authorization`, y la API la exige. Por eso se descarga con axios y se crea
un enlace temporal (`shared/api/descargar.ts:10-18`):

```ts
const respuesta = await httpClient.get<Blob>(url, { params, responseType: 'blob' })
const disposicion = String(respuesta.headers['content-disposition'] ?? '')
const nombre = /filename="?([^"]+)"?/.exec(disposicion)?.[1] ?? nombrePorDefecto
const enlace = document.createElement('a')
enlace.href = URL.createObjectURL(respuesta.data)
enlace.download = nombre
enlace.click()
```

Si la API responde con error, el cuerpo llega como Blob y se convierte a JSON
para mostrar el mensaje (`descargar.ts:20-26`).

**Backend** (`indicadores/interfaces/api/views.py:119-135`):

```python
def _no_vacio(filas) -> None:
    """HU25 CA3: un reporte vacío no genera archivo (409 con aviso)."""
    if not filas:
        raise Conflicto(REPORTE_VACIO)
...
def get(self, request):
    clasificacion = _clasificacion_abc()
    _no_vacio(clasificacion)
    return respuesta_excel(*excel_abc(clasificacion, timezone.localdate()))
```

La generación (`excel.py:64-79` y `94-96`):

```python
libro = Workbook()
hoja = libro.active
hoja.title = titulo[:31]  # límite de Excel para el nombre de la hoja
...
hoja.freeze_panes = f"A{fila_cabecera + 1}"
...
salida = BytesIO()
libro.save(salida)
return salida.getvalue()
```

Los datos del Excel de ABC salen del mismo caso de uso que la pantalla
(`excel.py:148-160`), así que siempre coinciden.

---

### 2.8 Auditoría: cómo se registra con signals y cómo se muestra

Idea: cada vez que se guarda o borra un registro de una tabla auditada,
Django dispara un **signal** y una función escribe una fila en
`historial_modificaciones` con antes, después, quién y cuándo. Reemplaza a
los triggers SQL del diseño original (`backend/apps/auditoria/apps.py:5-14`).

| # | Qué pasa | Dónde |
|---|---|---|
| 1 | Un middleware guarda el request actual en una `ContextVar`. | `backend/config/settings.py:67`, `backend/apps/auditoria/interfaces/middleware.py:9-18` |
| 2 | Al arrancar Django, `ready()` importa el módulo de signals y así los conecta. | `auditoria/apps.py:20-22` |
| 3 | Se conectan `pre_save`, `post_save` y `post_delete` para 7 modelos. | `auditoria/infrastructure/signals.py:25-33` y `111-116` |
| 4 | `pre_save` guarda una foto del registro tal como está en la base (los "datos anteriores"). | `signals.py:85-91` |
| 5 | `post_save` registra INSERT o UPDATE; si solo cambiaron campos automáticos, no registra nada. | `signals.py:94-104` |
| 6 | `post_delete` registra DELETE. | `signals.py:107-108` |
| 7 | El autor sale del request (`request.user`) o, en un comando, del nombre del comando. | `signals.py:61-82`, `auditoria/infrastructure/contexto.py:22-39` |
| 8 | La contraseña nunca se copia al historial. | `signals.py:35-37` |

Conexión de los signals (`signals.py:111-116`):

```python
for etiqueta in MODELOS_AUDITADOS:
    modelo = apps.get_model(etiqueta)
    uid = f"auditoria_{etiqueta}"
    pre_save.connect(_antes_de_guardar, sender=modelo, dispatch_uid=f"{uid}_pre_save")
    post_save.connect(_despues_de_guardar, sender=modelo, dispatch_uid=f"{uid}_post_save")
    post_delete.connect(_despues_de_borrar, sender=modelo, dispatch_uid=f"{uid}_post_delete")
```

Escritura de la fila (`signals.py:74-82`):

```python
HistorialModificacion.objects.create(
    tabla_afectada=instance._meta.label,
    registro_id=str(instance.pk),
    accion=accion.value,
    usuario=usuario_fk,
    usuario_username=usuario.username if usuario else comando_actual.get(),
    datos_anteriores=anteriores,
    datos_nuevos=nuevos,
)
```

**Por qué se guarda el request y no el usuario** (`contexto.py:6-9`): con JWT,
el usuario se autentica dentro de la vista de DRF, después del middleware.
Cuando el signal lee `request.user`, ya ve al usuario real.

**Requisito para que funcione:** guardar con `.save()` por instancia (no
`queryset.update()`, que no dispara signals). Por eso los repositorios lo
hacen así (`backend/apps/movimientos/infrastructure/repositories.py:1-5` y
`catalogo/infrastructure/repositories.py:180`).

**Cómo se muestra**

- API: `GET /api/auditoria/historial/` con filtros y paginación
  (`auditoria/interfaces/api/urls.py:6-7`, `views.py:24-52`).
- Solo Administrador y Supervisor (`auditoria/use_cases/consultar_historial.py:26`
  y `38-40`); el Empleado recibe 403.
- El caso de uso calcula qué campos cambiaron en cada edición
  (`consultar_historial.py:43-52`).
- Frontend: `useHistorial` (`features/auditoria/hooks/useHistorial.ts:4-11`)
  en `HistorialPage.tsx:64`; cada fila se expande con `DetalleCambio`
  (`HistorialPage.tsx:185`), que muestra una tabla Campo / Antes / Después
  (`features/auditoria/components/DetalleCambio.tsx:19-40`).
- La ruta `/historial` está protegida por rol (`app/router.tsx:59-65`) y el
  menú la oculta al Empleado (`app/layout/navegacion.ts:74`).

---

## 3. Frontend en detalle

### 3.1 El patrón api → hooks → pages

Cada feature separa tres responsabilidades:

| Capa | Responsabilidad | Ejemplo (catálogo) |
|---|---|---|
| `api/` | Funciones que llaman a la API con `httpClient` y devuelven datos tipados. No saben nada de React. | `features/catalogo/api/catalogoApi.ts:54-57` `listarHerramientas` |
| `hooks/` | Envuelven esas funciones en TanStack Query (`useQuery` / `useMutation`) y deciden qué caché invalidar. | `features/catalogo/hooks/useHerramientas.ts:6-8`, `useCrearHerramienta.ts:6-12` |
| `pages/` y `components/` | Solo usan los hooks y dibujan. | `features/catalogo/pages/CatalogoPage.tsx:104` |

Ejemplo completo, el listado del catálogo:

```ts
// api/catalogoApi.ts:54-57
export async function listarHerramientas(): Promise<Herramienta[]> {
  const { data } = await httpClient.get<Herramienta[]>(URL)
  return data
}

// hooks/useHerramientas.ts:6-8
export function useHerramientas() {
  return useQuery({ queryKey: ['herramientas'], queryFn: listarHerramientas })
}

// pages/CatalogoPage.tsx:104
const { data: herramientas, isLoading, isError, refetch } = useHerramientas()
```

Ventaja: si cambia una URL, se toca solo `api/`; si cambia qué se refresca,
solo `hooks/`; la página no sabe de HTTP.

### 3.2 TanStack Query

- **Un solo `QueryClient`** para toda la app
  (`app/providers/QueryProvider.tsx:8` y `11`), puesto en `App.tsx:14`.
- **`useQuery`** (leer): recibe una `queryKey` (el nombre de la caché) y una
  `queryFn`. Devuelve `data`, `isLoading`, `isError`, `refetch`. Si dos
  componentes usan la misma clave, se hace **una** sola petición: por ejemplo,
  `useFotos` reutiliza la caché `['herramientas']` del catálogo para mostrar
  fotos en otras tablas (`features/catalogo/hooks/useFotos.ts:7-13`).
- **`enabled`**: no consulta hasta que hay un dato, por ejemplo una
  herramienta elegida (`features/movimientos/hooks/useMovimientos.ts:6-12`).
- **`placeholderData`**: muestra los datos anteriores mientras llegan los
  nuevos, sin parpadeo (`features/promociones/hooks/usePromociones.ts:8`).
- **`useMutation`** (escribir): recibe `mutationFn` y un `onSuccess`.
  Devuelve `mutate`, `isPending` y `error`.
- **Invalidar la caché**: en `onSuccess` se llama a
  `queryClient.invalidateQueries({ queryKey: [...] })`. Eso marca los datos
  como viejos y todos los `useQuery` con esa clave vuelven a pedirlos solos.

  ```ts
  // features/transferencias/hooks/useTransferencias.ts:16-23
  function useRefrescar() {
    const queryClient = useQueryClient()
    return () => {
      for (const clave of ['transferencias', 'stock', 'movimientos', 'panel']) {
        queryClient.invalidateQueries({ queryKey: [clave] })
      }
    }
  }
  ```

  La clave funciona como prefijo: invalidar `['stock']` refresca
  `['stock', 5]`, `['stock', 7]`, etc.
- TanStack Query también vuelve a pedir los datos al volver a la pestaña
  (comportamiento por defecto, mencionado en
  `features/dashboard/hooks/usePanel.ts:4-5`).

### 3.3 El router y las rutas protegidas por rol

`app/router.tsx:42-78` define todo. La estructura:

```tsx
export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedRoute />,          // exige sesión
    children: [
      {
        element: <AppLayout />,           // barra lateral
        children: [
          { path: '/', element: <DashboardPage /> },
          ...
          {
            element: <RequireRol roles={[Rol.ADMINISTRADOR, Rol.SUPERVISOR]} />,
            children: [
              { path: '/cierre-diario', element: <CierreDiarioPage /> },
              { path: '/antiguedad', element: <AntiguedadPage /> },
              { path: '/historial', element: <HistorialPage /> },
            ],
          },
          {
            element: <RequireRol roles={[Rol.ADMINISTRADOR]} />,
            children: [
              { path: '/usuarios', element: <UsuariosPage /> },
              { path: '/usuarios/nuevo', element: <CrearUsuarioPage /> },
```

- `ProtectedRoute` (`features/auth/components/ProtectedRoute.tsx:6-12`): sin
  sesión, `<Navigate to="/login" />`; con sesión, `<Outlet />` (dibuja la
  ruta hija).
- `RequireRol` (`features/auth/components/RequireRol.tsx:7-16`): si el rol
  no está en la lista, manda a `/` (líneas 12-14).
- Son **"layout routes"**: no tienen `path`, solo envuelven a sus hijas.
- Importante: esto solo **oculta** pantallas. La seguridad real está en el
  backend, que vuelve a verificar el rol en cada petición (403).

### 3.4 El menú por rol (`app/layout/navegacion.ts`)

- Cada ítem tiene `ruta`, `texto`, `icono` y, opcionalmente, `roles`
  (`navegacion.ts:24-29`). Sin `roles`, lo ven todos.
- `GRUPOS` (líneas 41-77) define los grupos: Inventario, Análisis, Compras,
  Administración. Ejemplo: `{ ruta: '/usuarios', texto: 'Cuentas', icono: Users, roles: [Rol.ADMINISTRADOR] }`
  (línea 73).
- `gruposVisibles` filtra por rol y quita los grupos que quedan vacíos
  (líneas 79-83):

  ```ts
  export function gruposVisibles(rol: Rol): GrupoNav[] {
    return GRUPOS.map((g) => ({ ...g, items: g.items.filter((i) => !i.roles || i.roles.includes(rol)) })).filter(
      (g) => g.items.length > 0,
    )
  }
  ```

- La barra lateral lo usa con el rol de la sesión
  (`app/layout/Sidebar.tsx:48`).

### 3.5 Modo oscuro (ThemeProvider e index.css)

1. **Los colores son variables CSS** con valor claro en `:root`
   (`frontend/src/index.css:14-42`) y oscuro en `.dark` (`index.css:44-68`).
2. **`@theme inline`** (`index.css:70-103`) convierte esas variables en
   utilidades de Tailwind: `--color-acc: var(--acc)` (línea 73) genera
   `bg-acc`, `text-acc`, etc.
3. **La variante `dark`** se activa con la clase `.dark` en `<html>`
   (`index.css:12`):

   ```css
   @custom-variant dark (&:where(.dark, .dark *));
   ```

4. **`ThemeProvider`** (`app/providers/ThemeProvider.tsx:23-51`) decide el
   tema: lo que el usuario eligió (guardado en `localStorage` con la clave
   `tema`, línea 10) o, si nunca eligió, la preferencia del sistema
   (líneas 24-26). Pone o quita la clase (líneas 35-37):

   ```tsx
   useEffect(() => {
     document.documentElement.classList.toggle('dark', tema === 'oscuro')
   }, [tema])
   ```

5. **El botón** de la barra lateral llama a `alternar`
   (`app/layout/Sidebar.tsx:123-124`), que cambia y guarda
   (`ThemeProvider.tsx:39-47`).
6. **Sin parpadeo:** un script en `frontend/index.html:8-16` pone la clase
   antes de que React cargue.
7. El contexto y el hook `useTema` están aparte en `app/providers/tema.ts:13-19`.

Como los componentes solo usan `bg-surf`, `text-ink`, etc., cambiar el tema
no requiere tocar ningún componente.

### 3.6 Componentes de `components/ui` más importantes

Todos se exportan desde `components/ui/index.ts:3-23`.

| Componente | Qué resuelve | Dónde |
|---|---|---|
| `Button` | Botón en píldora con variantes `primary` (la única naranja), `secondary`, `ghost`; `cargando` lo deshabilita y muestra un spinner. Por defecto `type="button"`. | `components/ui/Button.tsx:19-43`, clases en `botones.ts:13-44` |
| `Field` | Etiqueta + control + ayuda o error, conectados por `id` y `aria-describedby` mediante un contexto. | `components/ui/Field.tsx:20-43`, `campo.ts:13-17` |
| `Input`, `Select`, `Textarea` | Controles con el estilo común; dentro de un `Field` toman su `id` y su estado de error. | `components/ui/Input.tsx:10-22`, `campo.ts:21-28` |
| `PasswordInput` | Contraseña con botón de ojo accesible; se oculta al enviar el formulario. | `components/ui/PasswordInput.tsx:17-51` |
| `Modal` y `SidePanel` | Ventana centrada y panel lateral, sobre Radix Dialog (foco atrapado, Escape, aria-modal) y animados con motion. | `components/ui/Modal.tsx:2`, `60`, `90` |
| `Table`, `THead`, `Th`, `Tr`, `Td` | Tabla con estilo común; `numerico` alinea cifras a la derecha. | `components/ui/Table.tsx:8-47` |
| `Aviso`, `Badge`, `EmptyState`, `Skeleton` | Mensajes, etiquetas, estado vacío y esqueletos de carga. | `components/ui/Aviso.tsx:17`, `Badge.tsx:18`, `EmptyState.tsx:17`, `Skeleton.tsx:6-56` |
| `cx` | Une clases ignorando las vacías. | `components/ui/cx.ts:2-4` |

`PasswordInput` en detalle (`PasswordInput.tsx:22-27` y `33-37`):

```tsx
useEffect(() => {
  const form = contenedor.current?.closest('form')
  if (!form) return
  const ocultar = () => setVisible(false)
  form.addEventListener('submit', ocultar)
  return () => form.removeEventListener('submit', ocultar)
}, [])
...
<Input type={visible ? 'text' : 'password'} className={cx('pr-11', className)} {...props} />
<button
  type="button"
  aria-label={etiqueta}
  aria-pressed={visible}
```

`autoComplete` es obligatorio y solo acepta `'current-password' | 'new-password'`
(línea 13), así TypeScript no deja olvidarlo.

### 3.7 Carga por ruta con React.lazy

Cada página se descarga solo cuando se abre su ruta
(`app/router.tsx:9-15`):

```tsx
function perezosa<K extends string>(cargar: () => Promise<Record<K, ComponentType>>, nombre: K) {
  return lazy(() => cargar().then((modulo) => ({ default: modulo[nombre] })))
}

const CatalogoPage = perezosa(() => import('../features/catalogo/pages/CatalogoPage'), 'CatalogoPage')
```

- `import()` dinámico hace que Vite genere un archivo JS aparte por página.
- `perezosa` existe porque las páginas se exportan con nombre y `React.lazy`
  espera un `export default`.
- Mientras llega el archivo, `<Suspense>` de `AppLayout` muestra un esqueleto
  (`app/layout/AppLayout.tsx:26-28` y `35-47`).
- El login no es perezoso (`router.tsx:3`): es lo primero que se ve.

---

## 4. Dónde está cada cosa

| # | Pregunta | Respuesta (archivo:línea) |
|---|---|---|
| 1 | ¿Dónde se valida que no haya stock negativo? | `backend/apps/movimientos/use_cases/registrar_movimiento.py:101-109` |
| 2 | ¿Dónde está el `select_for_update` de las salidas? | `backend/apps/movimientos/infrastructure/repositories.py:113-117` |
| 3 | ¿Dónde se abre la transacción de una salida? | `backend/apps/movimientos/interfaces/api/views.py:89` |
| 4 | ¿Dónde se calcula el stock? | `backend/apps/movimientos/domain/stock.py:39-45` (+ `repositories.py:63-69`) |
| 5 | ¿Dónde se convierte de cajas a unidades? | `backend/apps/indicadores/domain/formulas.py:87-97`, usado en `registrar_movimiento.py:96-97` |
| 6 | ¿Dónde se impide que un Empleado opere en otra sucursal? | `registrar_movimiento.py:90-91` (y en transferencias `gestionar_transferencias.py:83-84`) |
| 7 | ¿Dónde se impide editar o borrar un movimiento? | `movimientos/infrastructure/repositories.py:120-121`, `movimientos/interfaces/api/views.py:42-44` |
| 8 | ¿Dónde se cambia el color naranja? | `frontend/src/index.css:15` (claro, `--acc: #c2410c`) y `:45` (oscuro, `--acc: #f2692f`) |
| 9 | ¿Dónde se activa el modo oscuro? | `frontend/src/app/providers/ThemeProvider.tsx:35-37` y `index.css:12` |
| 10 | ¿Dónde se guarda el token? | `frontend/src/shared/api/tokenStorage.ts:15-18` (`localStorage`) |
| 11 | ¿Dónde se agrega el token a cada petición? | `frontend/src/shared/api/httpClient.ts:24-30` |
| 12 | ¿Dónde se renueva el token vencido? | `httpClient.ts:40-51` y `59-83` |
| 13 | ¿Dónde dura 30 minutos el token? | `backend/config/settings.py:164-168` |
| 14 | ¿Dónde se agrega el rol al token? | `backend/apps/usuarios/interfaces/api/serializers.py:58-66` |
| 15 | ¿Dónde lee el frontend el rol del usuario? | `frontend/src/features/auth/session.ts:56-63` |
| 16 | ¿Dónde se protegen las rutas por rol? | `frontend/src/app/router.tsx:59-73` y `features/auth/components/RequireRol.tsx:12-14` |
| 17 | ¿Dónde se decide qué ve cada rol en el menú? | `frontend/src/app/layout/navegacion.ts:41-83` |
| 18 | ¿Dónde se exige estar autenticado en toda la API? | `backend/config/settings.py:156` |
| 19 | ¿Dónde se impide que un Empleado edite el catálogo? | `backend/apps/usuarios/interfaces/api/permissions.py:31-43`, usado en `catalogo/interfaces/api/views.py:38` |
| 20 | ¿Dónde se impide que un Supervisor cambie el costo? | `backend/apps/catalogo/use_cases/gestionar_herramientas.py:84-96` |
| 21 | ¿Dónde se valida que el código de herramienta sea único? | `gestionar_herramientas.py:132-135` y `unique=True` en `catalogo/infrastructure/models.py:8` |
| 22 | ¿Dónde se recorta la foto? | `frontend/src/features/catalogo/components/recorte.ts:52-67` |
| 23 | ¿Dónde se valida el formato y peso de la foto? | Front: `recorte.ts:17-21`. Back: `gestionar_herramientas.py:109-117` |
| 24 | ¿Dónde se guardan las fotos en disco? | `catalogo/infrastructure/models.py:71-72` (`upload_to="productos/"`) y `settings.py:145` (`MEDIA_ROOT`) |
| 25 | ¿Dónde está la fórmula del EOQ? | `backend/apps/indicadores/domain/formulas.py:22-38` |
| 26 | ¿Dónde está la fórmula del ROP? | `formulas.py:41-53` |
| 27 | ¿Dónde se decide si usar demanda observada o estimada? | `formulas.py:61-71` |
| 28 | ¿Dónde se redondea el pedido a cajas cerradas? | `formulas.py:74-84` |
| 29 | ¿Dónde se clasifica en A, B y C? | `backend/apps/indicadores/use_cases/clasificar_abc.py:31-60`; umbrales en `indicadores/domain/entities.py:21-22` |
| 30 | ¿Dónde se arman las alertas del Panel? | `backend/apps/indicadores/use_cases/panel_auditoria.py:72-92` |
| 31 | ¿Dónde se definen los 40 días de estancamiento? | `backend/apps/indicadores/domain/entities.py:88` |
| 32 | ¿Dónde se limita al Supervisor a su sucursal en promociones? | `backend/apps/indicadores/use_cases/promociones.py:61-64` |
| 33 | ¿Dónde se genera el Excel? | `backend/apps/indicadores/interfaces/excel.py:57-96` |
| 34 | ¿Dónde se descarga el Excel en el frontend? | `frontend/src/shared/api/descargar.ts:8-29` |
| 35 | ¿Dónde se conectan los signals de auditoría? | `backend/apps/auditoria/infrastructure/signals.py:111-116` |
| 36 | ¿Dónde se sabe quién hizo el cambio? | `auditoria/interfaces/middleware.py:9-18` y `auditoria/infrastructure/contexto.py:32-39` |
| 37 | ¿Dónde se excluye la contraseña de la auditoría? | `signals.py:35-37` |
| 38 | ¿Dónde se exige sucursal a Supervisor y Empleado? | `backend/apps/usuarios/domain/reglas.py:14-18`, aplicado en `usuarios/use_cases/gestionar_usuarios.py:65-67` |
| 39 | ¿Dónde se configura la base de datos, la clave secreta y CORS? | `backend/config/settings.py:96-98`, `:26` y `:186-188` (valores en `backend/.env`) |
| 40 | ¿Dónde se traducen los errores de la API a mensajes en pantalla? | `frontend/src/shared/api/errores.ts:9-29` |
| 41 | ¿Dónde se carga cada página por separado? | `frontend/src/app/router.tsx:13-30` |
| 42 | ¿Dónde se redirige `/api` al backend en desarrollo? | `frontend/vite.config.ts:12-17` |
| 43 | ¿Dónde se valida la contraseña (largo mínimo, comunes)? | `backend/config/settings.py:119-124`, aplicado en `gestionar_usuarios.py:77-80` |
| 44 | ¿Dónde se prueba que todas las vistas pidan token? | `backend/apps/usuarios/tests.py:391` (`TodasLasVistasExigenSesionTests`) |

---

## 5. 20 preguntas probables de defensa

**1. ¿Por qué el stock no es una columna de una tabla?**
Porque se deriva de los movimientos: así no puede desincronizarse del
historial, que es la fuente de verdad auditable. Cada tipo suma o resta.
Abrir: `backend/apps/movimientos/domain/stock.py:1-21`.

**2. ¿Qué pasa si dos personas venden la última unidad al mismo tiempo?**
La segunda espera: la salida bloquea la fila de la herramienta con
`SELECT ... FOR UPDATE` antes de leer el stock, dentro de una transacción.
Cuando le toca, ve 0 y recibe "Stock insuficiente".
Abrir: `movimientos/use_cases/registrar_movimiento.py:101-109` y
`movimientos/infrastructure/repositories.py:113-117`.

**3. ¿Cómo sabe el backend quién es el usuario?**
Por el JWT en la cabecera `Authorization: Bearer ...`; DRF lo valida con
`JWTAuthentication`.
Abrir: `backend/config/settings.py:152-158` y `frontend/src/shared/api/httpClient.ts:24-30`.

**4. Si oculto un botón en el frontend, ¿eso es seguridad?**
No. El frontend solo oculta; el backend vuelve a verificar rol y sucursal en
cada caso de uso y responde 403. Hay una prueba que recorre todas las rutas y
exige 401 sin token.
Abrir: `frontend/src/features/catalogo/permisos.ts:3-6` (el comentario lo
dice) y `backend/apps/usuarios/tests.py:391`.

**5. ¿Qué es Clean Architecture en tu proyecto?**
Cuatro capas por app: `domain` (reglas puras), `use_cases` (casos de uso),
`infrastructure` (ORM) e `interfaces/api` (DRF). Los casos de uso reciben
repositorios abstractos, así se prueban sin base de datos.
Abrir: `backend/apps/usuarios/domain/repositories.py:1-12`.

**6. ¿Por qué un repositorio y no usar el ORM directo en la vista?**
Para que la regla de negocio no dependa de Django: el caso de uso usa la
interfaz (`HerramientaRepository`) y la vista inyecta la implementación con
ORM.
Abrir: `catalogo/domain/repositories.py:10-36` y
`catalogo/interfaces/api/views.py:42-46`.

**7. ¿Cómo se calcula el EOQ y de dónde sale la demanda?**
`raiz(2·D·S/H)`. D es lo vendido en los últimos 12 meses (solo salidas
reales); si no hubo ventas, la demanda estimada del catálogo.
Abrir: `indicadores/domain/formulas.py:22-38` y `61-71`.

**8. ¿Cuándo aparece una alerta de reorden?**
Cuando el stock total (todas las sucursales) es menor o igual al ROP. El
pedido sugerido es el EOQ redondeado a cajas cerradas.
Abrir: `indicadores/use_cases/calcular_punto_reorden.py:49` y
`indicadores/use_cases/panel_auditoria.py:83-92`.

**9. ¿Cómo funciona la clasificación ABC?**
Ordena por unidades vendidas, acumula el porcentaje y clasifica con el
acumulado anterior: menos de 80 % → A, menos de 95 % → B, el resto y las que
no vendieron → C.
Abrir: `indicadores/use_cases/clasificar_abc.py:31-60`.

**10. ¿Por qué un ajuste negativo no cuenta como venta?**
Porque corrige un error de conteo; si contara, inflaría la demanda del EOQ y
del ABC. Solo `SALIDA` es demanda.
Abrir: `movimientos/domain/stock.py:23-26`.

**11. ¿Cómo garantizas que una transferencia no deje stock a medias?**
Completar corre en una sola transacción: salida en origen, entrada en
destino y cambio de estado. Si algo falla, se deshace todo. La fila de la
transferencia se bloquea para que no se complete dos veces.
Abrir: `transferencias/interfaces/api/views.py:114-118` y
`transferencias/infrastructure/repositories.py:62`.

**12. ¿Cómo se registra la auditoría sin escribirla en cada vista?**
Con signals de Django (`pre_save`, `post_save`, `post_delete`) conectados a 7
modelos. El autor sale del request, que un middleware guarda en una
`ContextVar`.
Abrir: `auditoria/infrastructure/signals.py:25-33` y `111-116`.

**13. ¿Qué pasa cuando vence el token de 30 minutos?**
El interceptor de axios recibe 401, pide un token nuevo con el refresh (dura
un día) y reintenta la petición. Si el refresh también venció, borra los
tokens y manda al login.
Abrir: `frontend/src/shared/api/httpClient.ts:55-83`.

**14. ¿Cómo se actualiza la pantalla después de guardar sin recargar?**
Con TanStack Query: el `onSuccess` de la mutación invalida la caché y los
`useQuery` con esa clave vuelven a pedir los datos.
Abrir: `features/catalogo/hooks/useCrearHerramienta.ts:6-12`.

**15. ¿Cómo funciona el modo oscuro?**
Variables CSS con valor claro y oscuro; la clase `dark` en `<html>` cambia
los valores. `ThemeProvider` decide la clase y la recuerda en `localStorage`.
Abrir: `frontend/src/index.css:14-68` y `app/providers/ThemeProvider.tsx:35-37`.

**16. ¿Cómo se sube la foto y por qué se recorta en el navegador?**
Se recorta a un cuadrado de 1024 px en JPEG con `<canvas>`, así todas las
fotos tienen el mismo formato y pesan poco. Se envía en `multipart/form-data`.
El backend vuelve a validar formato y peso.
Abrir: `features/catalogo/components/recorte.ts:52-67` y
`features/catalogo/api/catalogoApi.ts:43-63`.

**17. ¿Por qué el Excel no se baja con un enlace normal?**
Porque un `<a href>` no manda el token. Se pide con axios como `blob` y se
crea un enlace temporal. Si el reporte está vacío, el backend responde 409.
Abrir: `frontend/src/shared/api/descargar.ts:8-18` y
`indicadores/interfaces/api/views.py:119-135`.

**18. ¿Por qué la aplicación carga rápido si tiene muchas pantallas?**
Cada página se descarga recién al abrirla (`React.lazy` + `import()`); el
paquete inicial trae el login y la barra lateral.
Abrir: `frontend/src/app/router.tsx:9-30`.

**19. ¿Dónde están las credenciales de la base de datos?**
En `backend/.env`, que no se versiona; `settings.py` las lee con
django-environ. Sin `DJANGO_SECRET_KEY`, Django no arranca.
Abrir: `backend/config/settings.py:16-28` y `96-98`.

**20. ¿Qué es una migración y dónde están las tuyas?**
Un archivo que describe un cambio de estructura de la base (crear tabla,
agregar columna). Están en `infrastructure/migrations/` de cada app, por
ejemplo `backend/apps/catalogo/infrastructure/migrations/0006_imagen_de_herramienta.py`.
Abrir: `backend/config/settings.py:100-112`.

---

## 6. Glosario

- **JWT (JSON Web Token):** un texto firmado por el servidor con tres partes
  separadas por puntos (cabecera, datos y firma). Los datos (usuario, rol,
  vencimiento) se pueden leer, pero no cambiar sin romper la firma. En el
  proyecto hay dos: el *access* (30 minutos, va en cada petición) y el
  *refresh* (1 día, sirve para pedir un access nuevo).
  Ver `settings.py:164-168` y `features/auth/session.ts:27-29`.

- **API REST:** una forma de exponer datos por HTTP donde cada URL es un
  recurso (`/api/catalogo/herramientas/`) y el método indica la acción: GET
  lee, POST crea, PUT/PATCH edita, DELETE borra. Responde en JSON con códigos
  como 200, 201, 400, 401, 403, 404, 409.

- **ORM (Object-Relational Mapping):** traduce clases de Python a tablas de
  la base. En vez de escribir SQL, se escribe
  `MovimientoModel.objects.filter(...)` y Django genera el `SELECT`. Ver
  `movimientos/infrastructure/repositories.py:63-69`.

- **Migración:** archivo generado por Django (`makemigrations`) que describe
  un cambio en la estructura de la base; `migrate` lo aplica. Permite que
  todos tengan la misma estructura. Ver `apps/*/infrastructure/migrations/`.

- **Signal:** aviso que Django emite cuando pasa algo (por ejemplo, después
  de guardar un modelo). Una función "conectada" se ejecuta sola. Se usa para
  la auditoría. Ver `auditoria/infrastructure/signals.py:111-116`.

- **Hook (React):** función que empieza con `use` y permite a un componente
  tener estado o efectos (`useState`, `useEffect`) o reutilizar lógica
  (`useHerramientas`, `useLogin`). Solo se llama dentro de componentes o de
  otros hooks.

- **Caché:** copia guardada de datos para no volver a pedirlos. TanStack
  Query guarda cada respuesta bajo su `queryKey`; invalidarla obliga a pedir
  de nuevo. Ver `features/transferencias/hooks/useTransferencias.ts:16-23`.

- **Serializer (DRF):** clase que valida los datos que llegan (tipos, largos,
  obligatorios) y convierte los objetos a JSON para la respuesta. En el
  proyecto solo valida la **forma**; las reglas de negocio están en los casos
  de uso. Ver `catalogo/interfaces/api/serializers.py:37-45`.

- **Caso de uso:** función que implementa una operación del negocio
  ("registrar salida", "completar transferencia") con todas sus reglas. No
  conoce HTTP ni el ORM: recibe repositorios. Ver
  `movimientos/use_cases/registrar_movimiento.py:131-133`.

- **Repositorio:** objeto que guarda y busca entidades. La **interfaz**
  (clase abstracta en `domain/repositories.py`) dice qué métodos hay; la
  **implementación** (en `infrastructure/repositories.py`) los hace con el
  ORM. Así el caso de uso no depende de Django y se puede probar con un
  repositorio falso. Ver `catalogo/domain/repositories.py:10-36` y
  `catalogo/infrastructure/repositories.py:71-100`.
