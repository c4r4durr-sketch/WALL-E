import { cx } from './cx'

// Clases de los botones en píldora (docs/DISENO.md). `primary` es la ÚNICA
// acción naranja de la pantalla; todo lo demás es `secondary` (fondo
// --surf2) o `ghost`. `peligro` tiñe de rojo un secundario o ghost. Va
// aparte de Button.tsx para usarlas también en un <Link> con forma de botón.
// El color del texto va aparte de la variante: cx solo concatena, y con
// `text-ink` y `text-danger` juntas ganaba la que Tailwind escribe después.

export type VarianteBoton = 'primary' | 'secondary' | 'ghost'
export type TamanoBoton = 'md' | 'sm'

const VARIANTE: Record<VarianteBoton, string> = {
  primary: 'bg-acc text-on-acc shadow-acc hover:brightness-110',
  secondary: 'bg-surf2 hover:brightness-95 dark:hover:brightness-125',
  ghost: 'hover:bg-surf2',
}

// Texto de secondary y ghost: normal o de peligro (rojo, con el fondo
// rojo suave de --danger-b al pasar el mouse en el ghost).
const TEXTO = {
  normal: 'text-ink',
  peligro: 'text-danger',
}

const TAMANO: Record<TamanoBoton, string> = {
  md: 'h-10 px-5 text-sm gap-2',
  sm: 'h-8 px-3.5 text-[13px] gap-1.5',
}

export function clasesBoton({
  variante = 'secondary',
  tamano = 'md',
  peligro = false,
}: { variante?: VarianteBoton; tamano?: TamanoBoton; peligro?: boolean } = {}): string {
  return cx(
    'transicion inline-flex shrink-0 select-none items-center justify-center rounded-full font-semibold whitespace-nowrap',
    'active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50',
    VARIANTE[variante],
    TAMANO[tamano],
    variante !== 'primary' && (peligro ? TEXTO.peligro : TEXTO.normal),
    variante === 'ghost' && peligro && 'hover:bg-danger-b',
  )
}
