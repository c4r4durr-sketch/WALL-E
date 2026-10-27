# Cambios para el informe

> Diferencias entre el código y `Informe_Walle_Importaciones.docx` /
> `Historias_Backlog_Sprint_Walle.docx`. Cada punto dice qué cambiar en el
> informe (o qué decidir) y por qué. Se agregan puntos a medida que avanzan
> las historias; se marcan como resueltos cuando el informe se actualiza.

## Pendientes de decidir

1. **Diccionario de datos de 16 tablas.** No está en el repo ni en el
   informe actual (los capítulos de diseño tienen marcadores "ACA PONES").
   `docs/DICCIONARIO_DE_DATOS.md` documenta las tablas **reales** (hoy 8:
   se sumó `proveedores`).
   Al pasar el diccionario al informe, partir de ese archivo, no del script
   v7.

2. **¿Dónde viven los reportes?** El informe habla de un "Módulo de
   Reportes y Auditoría", pero los 7 módulos del backend no incluyen
   `reportes`. Se está implementando así: cierre diario (HU14), antigüedad
   (HU22) y Excel (HU25) en `indicadores`; historial de modificaciones
   (HU13) en `auditoria`. El diagrama de paquetes debería reflejarlo.

## Para corregir en el informe

### Capítulo 2 (delimitación)
3. **Umbral de estancamiento.** 2.3 dice "sin salidas en 1 mes"; el
   backlog (HU22), la tabla 11 y el sistema usan **40 días**. Unificar a
   40 días.

### Capítulo 3 (diseño)
4. **Rutas de la API en los diagramas de secuencia.** Las reales son:
   | Informe | Sistema |
   |---|---|
   | `POST /api/usuarios/` | `POST /api/usuarios/usuarios/` |
   | `POST /api/herramientas/` | `POST /api/catalogo/herramientas/` |
   | `POST /api/indicadores/eoq` | `GET /api/indicadores/eoq/<id>/` (y `GET .../rop/<id>/`): son consultas, no crean nada |
   | `GET /api/reportes/estancadas` | se define con HU22 (ver punto 2) |

5. **Cuatro capas "en cada módulo".** `indicadores` no tiene capa
   `infrastructure` porque no tiene tablas propias: usa los repositorios de
   `catalogo` y `movimientos` a través de sus interfaces. Decirlo así en
   3.2.1 en lugar de afirmar que los 7 módulos tienen las cuatro capas.

6. **Clasificación ABC.** Existe en el sistema (`GET /api/indicadores/abc/`
   y pantalla "Indicadores") pero no aparece en el informe. Agregarla a la
   tabla 12 (Asistente de Compras) y al objetivo específico de EOQ/ROP.
   Hoy clasifica por **unidades vendidas**; con el costo unitario de HU7 se
   podría clasificar por **valor** (unidades × costo), que es la forma
   clásica. Decidir cuál se documenta (cambiarlo en el código es poco).

### Historias de usuario y backlog
7. **HU7: "Actualización de precios" → "Actualización de costos".** La
   historia, sus criterios y el sistema hablan del **costo unitario de
   compra**, no de un precio de venta (el sistema no tiene ventas POS).
   Proponer renombrarla. Implementación: campo `costo_unitario` y tabla
   nueva `historial_costos` (fecha, usuario, costo anterior y nuevo); solo
   el Administrador lo cambia. Además: un costo cargado no se puede borrar,
   solo reemplazar, y una herramienta con historial de costos no se elimina
   (409). Agregar la tabla al diccionario.

8. **HU8, CA3.** Dice "un proveedor con pedidos asociados no puede
   eliminarse", pero el sistema no registra pedidos. Se implementa como
   "un proveedor con **herramientas** asociadas no puede eliminarse; solo
   desactivarse". El tiempo de entrega (HU16) sigue en la herramienta.
   Otras decisiones de HU8 a documentar (se tomó la opción conservadora):
   - **quién escribe**: la HU dice "como administrador" y la tabla 9 lista
     Administrador y Supervisor para todo el módulo. Se aplicó **solo el
     Administrador** registra, edita, desactiva o elimina; Supervisor y
     Empleado consultan. Si el Supervisor también debe gestionar
     proveedores, es un cambio de una línea;
   - **datos**: nombre y teléfono obligatorios, correo opcional (CA1 nombra
     los tres; muchos proveedores solo dan teléfono). Nombre único sin
     distinguir mayúsculas. No se agregaron otros campos (dirección, NIT,
     persona de contacto) porque el criterio no los pide;
   - un proveedor **inactivo** no se puede asignar a herramientas nuevas;
     las que ya lo tenían lo conservan;
   - cada herramienta tiene **un** proveedor (opcional), no varios.

9. **HU15 está completa.** Cumple sus tres criterios (S y H por
   herramienta, no negativos, "datos faltantes" si no están). El "falta un
   registro detallado de gastos (flete, aduana)" del backlog no es un
   criterio. Marcarla como Hecha, o agregar un CA4 si se quiere el desglose.

10. **Cuentas de usuario (HU3/HU4/HU5, tabla 8).** Comportamiento a
    documentar:
    - las cuentas **no se eliminan**, se **desactivan** (quedan
      referenciadas por movimientos, transferencias y el historial); una
      cuenta desactivada no puede iniciar sesión;
    - nadie puede desactivarse ni quitarse el rol de Administrador a sí
      mismo, y siempre queda al menos un Administrador activo;
    - política de contraseñas: mínimo 8 caracteres, no comunes, no solo
      números, no parecida al usuario; se aplica al crear, editar y
      restablecer;
    - el nombre de usuario es único sin distinguir mayúsculas.

11. **Zona horaria.** El sistema trabaja en hora de La Paz (UTC-4): "hoy"
    para el cierre diario y los días sin venta se cuentan en esa zona.
    Mencionarlo en los supuestos o en el diseño.

12. **HU14, cierre diario.** CA2 pide "cada salida y el total del día";
    el sistema muestra **todos** los movimientos del día (entradas,
    salidas, transferencias y ajustes) con totales por tipo, y destaca las
    salidas y su total. Ajustar la redacción del criterio o de la tabla 11.
    Permisos (opción conservadora, tabla 11): Administrador cualquier
    sucursal, **Supervisor solo la suya**, Empleado no lo ve. Vive en el
    módulo `indicadores` (ver punto 2).

13. **HU13, historial de modificaciones.** La HU dice "como administrador,
    quiero un registro **oculto**" y CA4 "solo lectura en el panel de
    administración"; la tabla 11 lista Administrador y Supervisor. Ahora
    hay una pantalla propia (`/historial`, solo lectura) para
    **Administrador y Supervisor**, con filtros por fechas, usuario, tabla
    y acción, y el detalle de qué cambió. Actualizar CA4 ("solo lectura,
    visible para Administrador y Supervisor") y quitar "oculto" o aclarar
    que es oculto para el Empleado. Además, el historial ahora también
    registra **proveedores**, que no estaban en CA1.

14. **Módulo `auditoria` con cuatro capas.** Ya no está vacío: tiene
    entidades, repositorio de solo lectura, caso de uso y API. Los signals
    (infraestructura) siguen siendo los únicos que escriben el historial.

15. **Foto del producto (fase 1 de diseño).** Nueva columna
    `herramientas.imagen_herramienta` (ruta del archivo; los archivos
    viven en `backend/media/productos/`, fuera del repo). Toda herramienta
    nueva **debe** tener foto (JPG, PNG o WebP, máx. 5 MB, recortada 1:1
    en el formulario); las ya cargadas quedan sin foto y la pantalla
    muestra "Sin foto". No estaba en ninguna HU: agregarla al criterio de
    HU6 ("registrar herramienta con su foto") y al diccionario de datos.
    El alta de herramientas ahora se envía como `multipart/form-data`.
    El historial de modificaciones guarda la ruta de la foto, no el
    archivo.

16. **Rediseño visual del frontend.** Modo claro y oscuro, barra lateral
    con grupos (Inventario, Análisis, Compras, Administración) y catálogo
    en tarjetas con foto. Las reglas están en `docs/DISENO.md`. Si el
    informe trae capturas de pantalla, hay que rehacerlas.

### Sprint 4
17. **HU21, actualizar la demanda anual.** Nueva acción
    `POST /api/indicadores/eoq/<id>/actualizar-demanda/`. **Base de datos:**
    no cambia el esquema; escribe `herramientas.demanda_anual_herramienta`
    (= salidas reales de los últimos 12 meses, sin ajustes ni
    transferencias) y el cambio queda en `historial_modificaciones`.
    Decisiones: solo Administrador y Supervisor (los que editan el
    catálogo); sin ventas en el período no se actualiza (409, D = 0
    dejaría el EOQ en 0); se toma el total de 12 meses sin anualizar. Si
    el criterio de la HU pide recalcular automáticamente, documentar que
    es una acción explícita del usuario.
