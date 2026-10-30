import { Rol } from '../../shared/types/roles'

// Espejo de la regla del backend (gestionar_proveedores.py): todos
// consultan; solo el Administrador registra, edita o elimina. Acá solo
// sirve para ocultar botones; el backend responde 403 de todos modos.
export function puedeGestionarProveedores(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR
}
