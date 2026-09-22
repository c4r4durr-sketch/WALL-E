import type { TokenPair } from './api/authApi'
import type { Rol } from '../../shared/types/roles'
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '../../shared/api/tokenStorage'

// Claims que el backend agrega al token (ver
// CustomTokenObtainPairSerializer.get_token en el backend). Decodificar el
// JWT en el cliente evita un segundo request "/me" solo para mostrar la
// pantalla de bienvenida. Los trae tanto el access como el refresh token.
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

function decodeClaims(token: string): SessionClaims {
  return JSON.parse(base64UrlDecode(token.split('.')[1]))
}

// Claims del token si es válido y no venció; null en cualquier otro caso.
function claimsVigentes(token: string | null): SessionClaims | null {
  if (!token) return null
  try {
    const claims = decodeClaims(token)
    return claims.exp * 1000 > Date.now() ? claims : null
  } catch {
    return null
  }
}

export function saveSession(tokens: TokenPair): void {
  saveTokens(tokens.access, tokens.refresh)
}

export function clearSession(): void {
  clearTokens()
}

// Devuelve los claims de la sesión activa, o null si ya no hay sesión (y en
// ese caso limpia el storage de una vez).
//
// Que el access token haya vencido (30 min) NO cierra la sesión: mientras
// el refresh token siga vigente (1 día), httpClient renueva el access en la
// próxima petición a la API. Por eso se cae al refresh para leer los claims.
export function getSession(): SessionClaims | null {
  const claims = claimsVigentes(getAccessToken()) ?? claimsVigentes(getRefreshToken())
  if (!claims) {
    clearTokens()
    return null
  }
  return claims
}
