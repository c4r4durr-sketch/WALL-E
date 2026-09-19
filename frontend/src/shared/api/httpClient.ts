import axios from 'axios'

/**
 * Cliente HTTP centralizado.
 *
 * Todas las features llaman a la API a través de esta instancia en vez de
 * importar `axios` directamente, para tener un solo lugar donde configurar
 * baseURL, headers por defecto y el interceptor de autenticación.
 *
 * En dev, VITE_API_URL apunta a '/api' y Vite lo redirige al backend
 * (ver vite.config.ts) para no depender de CORS mientras se desarrolla.
 */
export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor de request: adjunta el access token guardado por el módulo de
// auth a cada petición saliente. El refresh automático ante un 401 se
// implementará junto con el resto de la lógica de la feature auth.
httpClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token')
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})
