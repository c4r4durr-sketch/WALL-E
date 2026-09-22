import { isAxiosError } from 'axios'

// El backend responde 400 con { campo: ["mensaje", ...] } o 403 con
// { detail: "..." }: se devuelve campo -> mensaje para mostrar cada uno
// junto a su campo. Compartido por el formulario de movimientos y el de
// ajustes.
export function erroresDelBackend(error: unknown): Record<string, string> {
  if (!isAxiosError(error)) return {}
  const datos = error.response?.data as Record<string, string[] | string> | undefined
  if (!datos || (error.response?.status !== 400 && error.response?.status !== 403)) return {}
  return Object.fromEntries(
    Object.entries(datos).map(([campo, m]) => [campo, Array.isArray(m) ? m.join(' ') : String(m)]),
  )
}
