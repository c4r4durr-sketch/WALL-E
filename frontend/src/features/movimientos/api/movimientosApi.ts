import { httpClient } from '../../../shared/api/httpClient'

// Espeja el serializer de MovimientoViewSet
// (backend/apps/movimientos/interfaces/api/serializers.py).
export type TipoMovimiento = 'ENTRADA' | 'SALIDA'
export type TipoUnidad = 'UNIDAD' | 'CAJA'

export interface Movimiento {
  id: number
  herramienta: number
  sucursal: number
  tipo_movimiento: TipoMovimiento
  tipo_unidad: TipoUnidad
  cantidad: number
  creado_en: string
}

export async function listarMovimientos(): Promise<Movimiento[]> {
  const { data } = await httpClient.get<Movimiento[]>('/movimientos/')
  return data
}
