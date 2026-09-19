/**
 * Espejo del enum de roles definido en el backend
 * (backend/apps/usuarios/domain/value_objects.py).
 *
 * Se mantiene sincronizado a mano por ahora. Si el proyecto crece, se puede
 * generar este archivo automáticamente desde el schema de drf-spectacular.
 */
export const Rol = {
  ADMINISTRADOR: 'ADMINISTRADOR',
  SUPERVISOR: 'SUPERVISOR',
  EMPLEADO: 'EMPLEADO',
} as const

export type Rol = (typeof Rol)[keyof typeof Rol]
