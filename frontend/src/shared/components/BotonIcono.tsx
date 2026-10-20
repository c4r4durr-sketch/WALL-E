import type { ReactNode } from 'react'

interface Props {
  titulo: string
  onClick: () => void
  children: ReactNode
  peligro?: boolean
  disabled?: boolean
}

// Botón solo con icono (acciones de una fila de tabla): `title` muestra el
// texto al pasar el mouse y `aria-label` lo lee el lector de pantalla.
export function BotonIcono({ titulo, onClick, children, peligro = false, disabled = false }: Props) {
  return (
    <button
      type="button"
      title={titulo}
      aria-label={titulo}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-md p-1.5 hover:bg-slate-100 disabled:opacity-50 ${peligro ? 'text-red-600' : 'text-slate-600'}`}
    >
      {children}
    </button>
  )
}
