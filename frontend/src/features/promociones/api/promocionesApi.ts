import { httpClient } from '../../../shared/api/httpClient'

// Espeja PromocionSerializer
// (backend/apps/indicadores/interfaces/api/serializers.py). HU23:
//   GET  /api/indicadores/promociones/?vigentes=true   (todos los roles)
//   POST /api/indicadores/promociones/                 (Administrador; Supervisor en su sucursal)
//   POST /api/indicadores/promociones/<id>/terminar/   (quitarla; los mismos)

export type EstadoPromocion = 'VIGENTE' | 'VENCIDA' | 'TERMINADA'

export interface Promocion {
  id: number
  herramienta_id: number
  herramienta_codigo: string
  herramienta_nombre: string
  sucursal_id: number
  sucursal_nombre: string
  // Opcional: null es la etiqueta de promoción sin descuento.
  descuento_porcentaje: number | null
  fecha_inicio: string
  fecha_fin: string
  motivo: string
  usuario: string
  creado_en: string
  estado: EstadoPromocion
}

export interface NuevaPromocion {
  herramienta_id: number
  sucursal_id: number
  descuento_porcentaje: number | null
  fecha_fin: string
  motivo: string
}

export async function listarPromociones(vigentes: boolean): Promise<Promocion[]> {
  const { data } = await httpClient.get<Promocion[]>('/indicadores/promociones/', { params: { vigentes } })
  return data
}

export async function crearPromocion(promocion: NuevaPromocion): Promise<Promocion> {
  const { data } = await httpClient.post<Promocion>('/indicadores/promociones/', promocion)
  return data
}

export async function terminarPromocion(id: number): Promise<Promocion> {
  const { data } = await httpClient.post<Promocion>(`/indicadores/promociones/${id}/terminar/`)
  return data
}
