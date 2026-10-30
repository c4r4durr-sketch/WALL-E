import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { TRANSICION } from './movimiento'
import { cx } from './cx'

// Control segmentado: opciones excluyentes en una píldora --surf2 con la
// elegida resaltada en --surf. Es un grupo de radios para el lector de
// pantalla; con el teclado, las flechas cambian de opción.

export interface OpcionSegmento<T extends string> {
  valor: T
  texto: ReactNode
  // Texto accesible si `texto` es solo un ícono.
  etiqueta?: string
}

interface Props<T extends string> {
  opciones: OpcionSegmento<T>[]
  valor: T
  onCambiar: (valor: T) => void
  etiqueta: string
  tamano?: 'md' | 'sm'
  className?: string
}

export function SegmentedControl<T extends string>({ opciones, valor, onCambiar, etiqueta, tamano = 'md', className }: Props<T>) {
  const grupo = useId()
  const reducido = useReducedMotion()
  const botones = useRef<Array<HTMLButtonElement | null>>([])

  function alTeclear(event: KeyboardEvent, indice: number) {
    const paso = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? -1 : 0
    if (!paso) return
    event.preventDefault()
    const siguiente = (indice + paso + opciones.length) % opciones.length
    onCambiar(opciones[siguiente].valor)
    botones.current[siguiente]?.focus()
  }

  return (
    <div role="radiogroup" aria-label={etiqueta} className={cx('inline-flex rounded-full bg-surf2 p-1', className)}>
      {opciones.map((opcion, indice) => {
        const activa = opcion.valor === valor
        return (
          <button
            key={opcion.valor}
            ref={(el) => {
              botones.current[indice] = el
            }}
            type="button"
            role="radio"
            aria-checked={activa}
            aria-label={opcion.etiqueta}
            title={opcion.etiqueta}
            tabIndex={activa ? 0 : -1}
            onClick={() => onCambiar(opcion.valor)}
            onKeyDown={(e) => alTeclear(e, indice)}
            className={cx(
              'transicion relative inline-flex items-center justify-center gap-1.5 rounded-full font-semibold whitespace-nowrap',
              tamano === 'md' ? 'h-8 px-4 text-[13px]' : 'h-7 px-3 text-xs',
              activa ? 'text-ink' : 'text-muted hover:text-ink',
            )}
          >
            {activa && (
              <motion.span
                layoutId={`segmento-${grupo}`}
                className="absolute inset-0 rounded-full bg-surf shadow-sh"
                transition={reducido ? { duration: 0 } : TRANSICION}
              />
            )}
            <span className="relative inline-flex items-center gap-1.5">{opcion.texto}</span>
          </button>
        )
      })}
    </div>
  )
}
