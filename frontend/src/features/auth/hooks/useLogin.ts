import { useMutation } from '@tanstack/react-query'
import { login } from '../api/authApi'

// Hook de mutación para el login, consumido por LoginPage.
// Guardar el token (localStorage), redirigir según rol y manejar errores
// de credenciales es lógica de negocio de la feature, pendiente de
// implementar junto con el resto del módulo de auth.
export function useLogin() {
  return useMutation({ mutationFn: login })
}
