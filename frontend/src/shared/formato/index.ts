// Formatos de pantalla compartidos. Las fechas se muestran siempre en la
// hora de La Paz (la misma TIME_ZONE del backend), sin importar la zona de
// la computadora que abre el sistema.
const ZONA_DEL_NEGOCIO = 'America/La_Paz'

const fechaHoraFmt = new Intl.DateTimeFormat('es', {
  dateStyle: 'short',
  timeStyle: 'short',
  timeZone: ZONA_DEL_NEGOCIO,
})

const montoFmt = new Intl.NumberFormat('es', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function fechaHora(iso: string): string {
  return fechaHoraFmt.format(new Date(iso))
}

export function monto(valor: number): string {
  return montoFmt.format(valor)
}
