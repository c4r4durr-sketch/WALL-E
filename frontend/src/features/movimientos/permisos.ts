import { Rol } from '../../shared/types/roles'

// Espejo del use case registrar_ajuste del backend: los ajustes de stock
// son correcciones, solo para Administrador y Supervisor. Acá solo decide
// si se muestra la sección; el backend igual responde 403 a un Empleado.
export function puedeAjustarStock(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR || rol === Rol.SUPERVISOR
}
