import { httpClient } from '../../../shared/api/httpClient'

// Espeja el serializer de TransferenciaViewSet
// (backend/apps/transferencias/interfaces/api/serializers.py).
export type TipoUnidad = 'UNIDAD' | 'CAJA'
export type EstadoTransferencia = 'PENDIENTE' | 'COMPLETADA' | 'RECHAZADA'

export interface Transferencia {
  id: number
  herramienta: number
  sucursal_origen: number
  sucursal_destino: number
  cantidad: number
  tipo_unidad: TipoUnidad
  estado: EstadoTransferencia
  creado_en: string
}

export async function listarTransferencias(): Promise<Transferencia[]> {
  const { data } = await httpClient.get<Transferencia[]>('/transferencias/')
  return data
}
