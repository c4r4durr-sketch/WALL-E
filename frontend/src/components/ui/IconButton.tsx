import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cx } from './cx'

// Botón redondo solo con ícono (acciones de una fila o una tarjeta). La
// etiqueta es obligatoria: es lo que lee el lector de pantalla y lo que
// muestra el navegador al pasar el mouse.

interface Props extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-label'> {
  etiqueta: string
  children: ReactNode
  peligro?: boolean
  tamano?: 'md' | 'sm'
}

export function IconButton({ etiqueta, children, peligro = false, tamano = 'md', className, type = 'button', ...props }: Props) {
  return (
    <button
      type={type}
      aria-label={etiqueta}
      title={etiqueta}
      className={cx(
        'transicion inline-flex shrink-0 items-center justify-center rounded-full',
        'hover:bg-surf2 active:scale-95 disabled:pointer-events-none disabled:opacity-40',
        tamano === 'md' ? 'h-9 w-9' : 'h-8 w-8',
        peligro ? 'text-danger' : 'text-muted hover:text-ink',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
