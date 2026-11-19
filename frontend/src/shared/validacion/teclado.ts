import type { KeyboardEvent } from 'react'

// Los <input type="number"> aceptan "e", "+", "-" y decimales aunque el
// campo sea de enteros. Estos props los bloquean desde el teclado (lo que
// llegue pegado igual lo rechazan las reglas de reglas.ts).

const BLOQUEADAS_ENTERO = new Set(['e', 'E', '+', '-', '.', ','])
const BLOQUEADAS_MONTO = new Set(['e', 'E', '+', '-', ','])

function bloquear(teclas: Set<string>) {
  return (event: KeyboardEvent<HTMLInputElement>) => {
    if (teclas.has(event.key)) event.preventDefault()
  }
}

// Cantidades: enteros mayores que 0 (o desde `min`).
export function propsEntero(min = 1, max?: number) {
  return { type: 'number', inputMode: 'numeric', min, max, step: 1, onKeyDown: bloquear(BLOQUEADAS_ENTERO) } as const
}

// Costos y montos: mayor que 0 con hasta 2 decimales.
export function propsMonto() {
  return { type: 'number', inputMode: 'decimal', min: 0.01, step: 0.01, onKeyDown: bloquear(BLOQUEADAS_MONTO) } as const
}
