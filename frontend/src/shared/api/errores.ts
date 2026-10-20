import { isAxiosError } from 'axios'

// Formato de errores de la API (igual en todos los módulos del backend):
//   400 -> { campo: ["mensaje", ...] }  (errores de validación por campo)
//   401/403/404/409 -> { detail: "mensaje" }
// Estas dos funciones lo traducen para mostrarlo en pantalla.

// campo -> mensaje, para mostrar cada error debajo de su campo.
export function erroresPorCampo(error: unknown): Record<string, string> {
  if (!isAxiosError(error) || error.response?.status !== 400) return {}
  const datos = error.response.data as Record<string, string[] | string> | undefined
  if (!datos || typeof datos !== 'object') return {}
  return Object.fromEntries(
    Object.entries(datos).map(([campo, mensajes]) => [
      campo,
      Array.isArray(mensajes) ? mensajes.join(' ') : String(mensajes),
    ]),
  )
}

// Mensaje general para un error que no es de un campo (403, 404, 409, red).
export function mensajeDeError(error: unknown, porDefecto: string): string {
  if (isAxiosError(error)) {
    const detalle = (error.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detalle === 'string') return detalle
    if (!error.response) return 'No hay conexión con el servidor. Intenta de nuevo.'
  }
  return porDefecto
}
