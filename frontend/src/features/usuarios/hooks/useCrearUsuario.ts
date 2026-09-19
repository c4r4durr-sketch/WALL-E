import { useMutation } from '@tanstack/react-query'
import { crearUsuario } from '../api/usuariosApi'

export function useCrearUsuario() {
  return useMutation({ mutationFn: crearUsuario })
}
