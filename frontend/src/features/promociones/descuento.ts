// HU23: el descuento de una promoción es opcional.
export function textoDescuento(descuento: number | null): string {
  return descuento === null ? 'Sin descuento' : `−${descuento} %`
}
