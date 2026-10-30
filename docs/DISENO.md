# DISENO.md · Reglas visuales de Walle-Importaciones

Estilo: sobrio, tipo Apple. Una sola acción primaria naranja por pantalla. Todo lo demás, neutro.
Solo escritorio. Iconos lucide-react (trazo 1.8). Sin emojis. Una sola tipografía: Inter.

## Colores (variables CSS; modo claro y oscuro)
| Token        | Claro                     | Oscuro                    |
|--------------|---------------------------|---------------------------|
| --acc        | #C2410C                   | #F2692F                   |
| --soft       | #FFEDE0                   | rgba(242,105,47,.18)      |
| --softink    | #9A3412                   | #FFB690                   |
| --ink        | #1D1D1F                   | #F5F5F7                   |
| --muted      | #6E6E73                   | #A1A1A6                   |
| --bg         | #F2F2F5                   | #0B0B0D                   |
| --surf       | #FFFFFF                   | #1C1C1E                   |
| --surf2      | #F2F2F5                   | #2C2C2E                   |
| --line       | rgba(0,0,0,.08)           | rgba(255,255,255,.10)     |
| --glass      | rgba(255,255,255,.62)     | rgba(40,40,44,.58)        |
| --ok  (c/b)  | #1E7A35 / rgba(34,160,70,.14)  | #4CD263 / rgba(76,210,99,.16)  |
| --warn (c/b) | #9A5B00 / rgba(245,158,11,.16) | #FFC24D / rgba(255,159,10,.18) |
| --danger (c/b)| #C62828 / rgba(220,38,38,.11) | #FF6B63 / rgba(255,69,58,.18)  |

Sombras (capas, no bordes):
- --sh claro:  0 1px 2px rgba(0,0,0,.04), 0 4px 12px rgba(0,0,0,.05), 0 16px 32px -8px rgba(0,0,0,.08)
- --shh claro: 0 2px 4px rgba(0,0,0,.05), 0 10px 24px rgba(0,0,0,.08), 0 28px 48px -12px rgba(0,0,0,.14)
- oscuro: mismas capas con negro .4 / .35 / .55 y .45 / .45 / .7

## Modo claro / oscuro
- Se activa con la clase `dark` en <html>. Valor inicial: preferencia guardada en localStorage; si no hay, `prefers-color-scheme`.
- Interruptor en la barra lateral (icono luna/sol). Transición de color de 200 ms.
- Ningún color escrito a mano en componentes: solo variables.

## Forma
- Radios: 12 (campos, chips pequeños), 20 (tarjetas internas, imagen), 26-28 (tarjetas grandes, paneles), 999 (botones, chips, buscador).
- Botón primario: píldora naranja, texto blanco, sombra `0 6px 18px -6px var(--acc)`. Secundario: fondo --surf2.
- Campos: fondo --surf2, radio 14, sin borde; foco con anillo de 2px en --acc.
- Tablas: sin líneas verticales, filas de 56 px, hover suave en --surf2, cabecera en --muted 12 px.
- Estados (badges): píldora con fondo y color --ok / --warn / --danger.
- Estados vacíos: icono lucide grande en círculo --soft, título, una línea de ayuda y una acción.
- Carga: skeletons (bloques --surf2 con pulso suave). Prohibido el texto "Cargando...".

## Tipografía (Inter)
- Título de página 36/700, espaciado -0.035em. Subtítulo/migas 13/500 --muted.
- Números grandes 22-32/700, espaciado -0.03em, `font-variant-numeric: tabular-nums` en TODA cifra de stock o dinero.
- Etiquetas 12/600 --muted. Texto base 14/400-500.

## Vidrio (Liquid Glass sobrio)
- SOLO en: barra lateral, barra superior de página, paneles laterales y modales.
- `background: var(--glass); backdrop-filter: blur(28px) saturate(180%); border: 1px solid var(--line); box-shadow: var(--sh)`.
- Detrás va el fondo --bg con dos manchas radiales suaves (naranja y azul, baja opacidad). Tablas y formularios NUNCA llevan vidrio.

## Movimiento
- Todo lo interactivo: 200 ms, curva `cubic-bezier(.2,.8,.2,1)`.
- Tarjetas: hover sube 3 px y pasa de --sh a --shh.
- Paneles y modales: entran con escala 0.96 -> 1 y opacidad, con la librería `motion`.
- Listas: aparición escalonada de 30 ms por elemento (máx. 12).
- Respetar `prefers-reduced-motion`: sin animaciones de entrada.

## Navegación (barra lateral flotante de vidrio, 264 px, radio 28)
Panel (suelto)
Inventario > Catálogo, Movimientos, Transferencias
Análisis > Indicadores, Reposición EOQ, Clasificación ABC
Compras > Proveedores, Órdenes de compra (solo si existe la pantalla)
Administración > Cuentas, Auditoría
- Grupos desplegables (flecha que gira 90°); el grupo de la página activa abre solo; el estado se recuerda.
- Ítem activo: fondo --soft, texto --softink, peso 600. Los grupos o ítems que el rol no puede ver no se muestran.
- Abajo: tarjeta de usuario (iniciales en círculo --acc, nombre, rol) + interruptor de tema.

## Imágenes de producto
- Cada producto DEBE tener foto al crearse (obligatoria en el formulario de alta).
- Zona de arrastrar y soltar con vista previa y recorte cuadrado 1:1. JPG, PNG o WebP, máx. 5 MB.
- En tarjetas y listas: contenedor 1:1 con radio 18-20, `object-fit: cover`, degradado --surf2 -> --bg de fondo.
- Sin foto (datos antiguos): ilustración de respaldo neutra con icono lucide `package` + texto "Sin foto".

## Prohibido
Bordes de 1 px como separador principal en tarjetas, sombras duras, colores fuera de la tabla, emojis, más de un botón naranja por pantalla, texto "Cargando...", tablas con líneas verticales, vidrio en tablas o formularios.
