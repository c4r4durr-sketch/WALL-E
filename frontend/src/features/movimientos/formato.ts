import type { TipoMovimiento } from './api/movimientosApi'

// Textos de cantidades compartidos por el formulario y el historial.
export function cajas(n: number): string {
  return `${n} ${n === 1 ? 'caja' : 'cajas'}`
}

export function desgloseCajas(cajasCompletas: number, sueltas: number): string {
  return `${cajas(cajasCompletas)} + ${sueltas} ${sueltas === 1 ? 'suelta' : 'sueltas'}`
}

// Los ajustes llevan etiqueta propia (ámbar, igual que su formulario) para
// distinguir una corrección de una operación normal del mostrador.
export const ETIQUETA: Record<TipoMovimiento, { texto: string; clase: string }> = {
  ENTRADA: { texto: 'Entrada', clase: 'bg-green-50 text-green-700' },
  SALIDA: { texto: 'Salida', clase: 'bg-slate-100 text-slate-700' },
  AJUSTE_POSITIVO: { texto: 'Ajuste +', clase: 'bg-amber-100 text-amber-800' },
  AJUSTE_NEGATIVO: { texto: 'Ajuste −', clase: 'bg-amber-100 text-amber-800' },
  TRANSFERENCIA_SALIDA: { texto: 'Transferencia enviada', clase: 'bg-blue-50 text-blue-700' },
  TRANSFERENCIA_ENTRADA: { texto: 'Transferencia recibida', clase: 'bg-blue-50 text-blue-700' },
}
