// Textos de cantidades compartidos por el formulario y el historial.
export function cajas(n: number): string {
  return `${n} ${n === 1 ? 'caja' : 'cajas'}`
}

export function desgloseCajas(cajasCompletas: number, sueltas: number): string {
  return `${cajas(cajasCompletas)} + ${sueltas} ${sueltas === 1 ? 'suelta' : 'sueltas'}`
}
