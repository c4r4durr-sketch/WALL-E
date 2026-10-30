import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { clasesBoton, type TamanoBoton, type VarianteBoton } from './botones'
import { cx } from './cx'

// Botón en píldora (ver botones.ts para las variantes).

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: VarianteBoton
  tamano?: TamanoBoton
  peligro?: boolean
  // Ícono a la izquierda del texto (un componente de lucide ya renderizado).
  icono?: ReactNode
  // Mientras se envía: deshabilitado y con un indicador girando en lugar
  // del ícono (nunca un texto tipo "Guardando...").
  cargando?: boolean
}

export function Button({
  variante,
  tamano,
  peligro,
  icono,
  cargando = false,
  disabled,
  className,
  children,
  type = 'button',
  ...props
}: Props) {
  return (
    <button
      type={type}
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      className={cx(clasesBoton({ variante, tamano, peligro }), className)}
      {...props}
    >
      {cargando ? <Loader2 size={16} aria-hidden className="animate-spin" /> : icono}
      {children}
    </button>
  )
}
