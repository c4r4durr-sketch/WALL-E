import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { editarUsuario, listarUsuarios, restablecerPassword } from '../api/usuariosApi'

export function useUsuarios() {
  return useQuery({ queryKey: ['usuarios'], queryFn: listarUsuarios })
}

export function useEditarUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: editarUsuario,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  })
}

export function useRestablecerPassword() {
  return useMutation({ mutationFn: restablecerPassword })
}
