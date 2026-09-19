import { useMutation } from '@tanstack/react-query'
import { login } from '../api/authApi'
import { saveSession } from '../session'

// Hook de mutación para el login, consumido por LoginPage. Guarda el
// access/refresh token apenas el backend responde 200; LoginPage decide
// hacia dónde navegar en su propio onSuccess.
export function useLogin() {
  return useMutation({
    mutationFn: login,
    onSuccess: saveSession,
  })
}
