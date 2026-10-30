import type { TonoBadge } from '../../components/ui'
import type { TipoMovimiento } from './api/movimientosApi'

// Textos de cantidades compartidos por el formulario y el historial.
export function cajas(n: number): string {
  return `${n} ${n === 1 ? 'caja' : 'cajas'}`
}

export function desgloseCajas(cajasCompletas: number, sueltas: number): string {
  return `${cajas(cajasCompletas)} + ${sueltas} ${sueltas === 1 ? 'suelta' : 'sueltas'}`
}

// Etiqueta de cada tipo. Los ajustes van en ámbar (advertencia) para
// distinguir una corrección de una operación normal del mostrador.
export const ETIQUETA: Record<TipoMovimiento, { texto: string; tono: TonoBadge }> = {
  ENTRADA: { texto: 'Entrada', tono: 'ok' },
  SALIDA: { texto: 'Salida', tono: 'neutral' },
  AJUSTE_POSITIVO: { texto: 'Ajuste +', tono: 'warn' },
  AJUSTE_NEGATIVO: { texto: 'Ajuste −', tono: 'warn' },
  TRANSFERENCIA_SALIDA: { texto: 'Transferencia enviada', tono: 'acc' },
  TRANSFERENCIA_ENTRADA: { texto: 'Transferencia recibida', tono: 'acc' },
}
