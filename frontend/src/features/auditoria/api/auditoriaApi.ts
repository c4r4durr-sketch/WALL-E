import { httpClient } from '../../../shared/api/httpClient'

export type AccionAuditoria = 'INSERT' | 'UPDATE' | 'DELETE'

// Valores de un registro auditado: lo que guardó el backend en JSON.
export type DatosRegistro = Record<string, unknown>

// Espeja PaginaHistorialSerializer
// (backend/apps/auditoria/interfaces/api/serializers.py).
export interface RegistroHistorial {
  id: number
  fecha: string
  tabla: string
  tabla_nombre: string
  registro_id: string
  accion: AccionAuditoria
  usuario_id: number | null
  usuario: string
  datos_anteriores: DatosRegistro | null
  datos_nuevos: DatosRegistro | null
  campos_cambiados: string[]
}

export interface PaginaHistorial {
  total: number
  pagina: number
  paginas: number
  tamano: number
  resultados: RegistroHistorial[]
}

export interface OpcionFiltro {
  valor: string
  texto: string
}

export interface OpcionesHistorial {
  tablas: OpcionFiltro[]
  usuarios: OpcionFiltro[]
  acciones: OpcionFiltro[]
  // USUARIOS (desde la aplicación) o COMANDOS (cargar_demo y otros, sin usuario).
  origenes: OpcionFiltro[]
}

export interface FiltroHistorial {
  desde?: string
  hasta?: string
  usuario?: string
  tabla?: string
  accion?: string
  origen?: string
  pagina: number
}

export async function consultarHistorial(filtro: FiltroHistorial): Promise<PaginaHistorial> {
  // Los filtros vacíos no se envían.
  const params = Object.fromEntries(Object.entries(filtro).filter(([, v]) => v !== '' && v !== undefined))
  const { data } = await httpClient.get<PaginaHistorial>('/auditoria/historial/', { params })
  return data
}

export async function obtenerOpcionesHistorial(): Promise<OpcionesHistorial> {
  const { data } = await httpClient.get<OpcionesHistorial>('/auditoria/historial/opciones/')
  return data
}
