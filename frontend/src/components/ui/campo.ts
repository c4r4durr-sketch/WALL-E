import { createContext, useContext } from 'react'

// Lo que Field les pasa a Input / Select / Textarea: el id que usa la
// etiqueta, a qué textos de ayuda o error apunta aria-describedby y si el
// campo tiene un error. Sin Field alrededor, cada control funciona solo.

export interface ContextoCampo {
  id: string
  describedBy?: string
  invalido: boolean
}

export const ContextoDeCampo = createContext<ContextoCampo | null>(null)

export function useCampo(): ContextoCampo | null {
  return useContext(ContextoDeCampo)
}

// Clases comunes de los controles: fondo --surf2, radio 14, sin borde; con
// foco, anillo de 2 px en el acento; con error, anillo en --danger.
export function clasesControl(invalido: boolean): string {
  return [
    'transicion w-full rounded-campo bg-surf2 px-3.5 text-sm text-ink placeholder:text-muted',
    'outline-none focus-visible:outline-none focus:ring-2 focus:ring-acc',
    'disabled:cursor-not-allowed disabled:opacity-60',
    invalido ? 'ring-2 ring-danger' : '',
  ].join(' ')
}
