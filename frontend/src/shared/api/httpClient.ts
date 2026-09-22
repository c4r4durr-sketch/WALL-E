import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from './tokenStorage'

/**
 * Cliente HTTP centralizado.
 *
 * Todas las features llaman a la API a través de esta instancia en vez de
 * importar `axios` directamente, para tener un solo lugar donde configurar
 * baseURL, headers por defecto y el manejo de autenticación JWT.
 *
 * En dev, VITE_API_URL apunta a '/api' y Vite lo redirige al backend
 * (ver vite.config.ts) para no depender de CORS mientras se desarrolla.
 */
const baseURL = import.meta.env.VITE_API_URL ?? '/api'

export const httpClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor de request: adjunta el access token a cada petición saliente.
httpClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Endpoints de auth: un 401 acá significa credenciales o refresh inválidos,
// no un access vencido, así que nunca se intenta renovar sobre ellos.
const RUTAS_SIN_REFRESH = ['/token/', '/token/refresh/']

// Refresh en curso, compartido: si varias peticiones reciben 401 a la vez,
// todas esperan el MISMO refresh en vez de disparar uno cada una.
let refreshEnCurso: Promise<string> | null = null

async function renovarAccessToken(): Promise<string> {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('Sin refresh token')
  // axios "pelado" (no httpClient) para que esta llamada no pase por los
  // interceptores y no pueda entrar en un bucle de refresh.
  const { data } = await axios.post<{ access: string; refresh?: string }>(
    `${baseURL}/token/refresh/`,
    { refresh },
  )
  saveTokens(data.access, data.refresh)
  return data.access
}

type RequestReintentable = InternalAxiosRequestConfig & { _reintentado?: boolean }

// Interceptor de response: el access token dura 30 min. Ante un 401 se
// pide uno nuevo con el refresh token (dura 1 día) y se reintenta la
// petición original una sola vez. Si el refresh también falla, la sesión
// terminó de verdad: se limpian los tokens y se vuelve a /login.
httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RequestReintentable | undefined
    const esRutaDeAuth = RUTAS_SIN_REFRESH.includes(original?.url ?? '')

    if (error.response?.status !== 401 || !original || original._reintentado || esRutaDeAuth) {
      return Promise.reject(error)
    }
    original._reintentado = true

    try {
      refreshEnCurso ??= renovarAccessToken().finally(() => {
        refreshEnCurso = null
      })
      const nuevoAccess = await refreshEnCurso
      original.headers.Authorization = `Bearer ${nuevoAccess}`
      return httpClient(original)
    } catch {
      clearTokens()
      window.location.assign('/login')
      return Promise.reject(error)
    }
  },
)
