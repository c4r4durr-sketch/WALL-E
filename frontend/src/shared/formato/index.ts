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

const horaFmt = new Intl.DateTimeFormat('es', { timeStyle: 'short', timeZone: ZONA_DEL_NEGOCIO })

// en-CA da AAAA-MM-DD, el formato de <input type="date"> y de la API.
const fechaIsoFmt = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  timeZone: ZONA_DEL_NEGOCIO,
})

const fechaLargaFmt = new Intl.DateTimeFormat('es', { dateStyle: 'full', timeZone: 'UTC' })

export function hora(iso: string): string {
  return horaFmt.format(new Date(iso))
}

// "Hoy" en La Paz como AAAA-MM-DD (no el de la zona de la computadora).
export function hoyEnLaPaz(): string {
  return fechaIsoFmt.format(new Date())
}

// "AAAA-MM-DD" -> "martes, 20 de octubre de 2026". Se interpreta en UTC
// para que la fecha no se corra un día por la zona horaria.
export function fechaLarga(isoFecha: string): string {
  return fechaLargaFmt.format(new Date(`${isoFecha}T00:00:00Z`))
}

const fechaCortaFmt = new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeZone: 'UTC' })

// "AAAA-MM-DD" -> "27 oct 2026" (en UTC, por lo mismo que fechaLarga).
export function fechaCorta(isoFecha: string): string {
  return fechaCortaFmt.format(new Date(`${isoFecha}T00:00:00Z`))
}

// "AAAA-MM-DD" + n días -> "AAAA-MM-DD" (en UTC: sin saltos por horario).
export function sumarDias(isoFecha: string, dias: number): string {
  const fecha = new Date(`${isoFecha}T00:00:00Z`)
  fecha.setUTCDate(fecha.getUTCDate() + dias)
  return fecha.toISOString().slice(0, 10)
}

export function monto(valor: number): string {
  return montoFmt.format(valor)
}
