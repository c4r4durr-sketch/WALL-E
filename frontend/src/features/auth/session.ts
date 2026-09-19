import type { TokenPair } from './api/authApi'
import type { Rol } from '../../shared/types/roles'

const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

// Claims que el backend agrega al access token (ver
// CustomTokenObtainPairSerializer.get_token en el backend). Decodificar el
// JWT en el cliente evita un segundo request "/me" solo para mostrar la
// pantalla de bienvenida.
export interface SessionClaims {
  user_id: string
  username: string
  first_name: string
  last_name: string
  rol: Rol
  sucursal_id: number | null
  sucursal_nombre: string | null
  exp: number
}

function base64UrlDecode(value: string): string {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/')
  const binary = atob(base64)
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0))
  return new TextDecoder().decode(bytes)
}

function decodeClaims(accessToken: string): SessionClaims {
  return JSON.parse(base64UrlDecode(accessToken.split('.')[1]))
}

export function saveSession(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_KEY, tokens.access)
  localStorage.setItem(REFRESH_KEY, tokens.refresh)
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

// Devuelve los claims de la sesión activa, o null si no hay token, está
// corrupto o ya expiró (y en ese caso limpia el storage de una vez).
export function getSession(): SessionClaims | null {
  const token = localStorage.getItem(ACCESS_KEY)
  if (!token) return null
  try {
    const claims = decodeClaims(token)
    if (claims.exp * 1000 < Date.now()) {
      clearSession()
      return null
    }
    return claims
  } catch {
    clearSession()
    return null
  }
}
