import { Rol } from '../../shared/types/roles'

// Espejo del permiso del backend
// (LecturaParaTodosEscrituraAdministradorOSupervisor): el Empleado solo
// consulta el catálogo. Acá solo sirve para ocultar botones; la regla real
// la aplica el backend, que responde 403 aunque alguien fuerce la petición.
export function puedeEditarCatalogo(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR || rol === Rol.SUPERVISOR
}

// HU7: el costo unitario solo lo cambia el Administrador (el backend
// responde 403 a cualquier otro rol).
export function puedeCambiarCosto(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR
}
