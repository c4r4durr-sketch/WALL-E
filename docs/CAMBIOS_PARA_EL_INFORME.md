# Cambios para el informe

> Diferencias entre el código y `Informe_Walle_Importaciones.docx` /
> `Historias_Backlog_Sprint_Walle.docx`. Cada punto dice qué cambiar en el
> informe (o qué decidir) y por qué. Se agregan puntos a medida que avanzan
> las historias; se marcan como resueltos cuando el informe se actualiza.

## Pendientes de decidir

1. **Diccionario de datos de 16 tablas.** No está en el repo ni en el
   informe actual (los capítulos de diseño tienen marcadores "ACA PONES").
   `docs/DICCIONARIO_DE_DATOS.md` documenta las tablas **reales** (hoy 7).
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
