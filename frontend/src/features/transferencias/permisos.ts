import { Rol } from '../../shared/types/roles'

// Espejo del use case del backend: completar o rechazar una transferencia
// es para Administrador y Supervisor. Solo decide qué botones se muestran;
// el backend igual responde 403.
export function puedeResolverTransferencias(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR || rol === Rol.SUPERVISOR
}
