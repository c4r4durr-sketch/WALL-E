import { httpClient } from '../../../shared/api/httpClient'

// DTOs mínimos del endpoint de login (SimpleJWT: POST /api/token/).
// Se amplían cuando el backend agregue claims de rol/sucursal al token.
export interface LoginCredentials {
  username: string
  password: string
}

export interface TokenPair {
  access: string
  refresh: string
}

export async function login(credentials: LoginCredentials): Promise<TokenPair> {
  const { data } = await httpClient.post<TokenPair>('/token/', credentials)
  return data
}
