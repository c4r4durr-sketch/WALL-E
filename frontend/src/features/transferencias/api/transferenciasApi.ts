import { httpClient } from '../../../shared/api/httpClient'
import type { TipoUnidad } from '../../movimientos/api/movimientosApi'

// Espeja los serializers de transferencias
// (backend/apps/transferencias/interfaces/api/serializers.py).
export type EstadoTransferencia = 'PENDIENTE' | 'COMPLETADA' | 'RECHAZADA'

export interface Transferencia {
  id: number
  herramienta: number
  sucursal_origen: number
  sucursal_destino: number
  usuario: number
  usuario_username: string
  cantidad: number
  tipo_unidad: TipoUnidad
  cantidad_unidades: number
  estado: EstadoTransferencia
  creado_en: string
  resuelto_por: number | null
  resuelto_por_username: string | null
  resuelto_en: string | null
  motivo_rechazo: string
  movimiento_salida: number | null
  movimiento_entrada: number | null
}

export interface SolicitarTransferenciaPayload {
  herramienta: number
  sucursal_origen: number
  sucursal_destino: number
  tipo_unidad: TipoUnidad
  cantidad: number
}

const URL = '/transferencias/'

export async function listarTransferencias(estado?: EstadoTransferencia): Promise<Transferencia[]> {
  const { data } = await httpClient.get<Transferencia[]>(URL, { params: estado ? { estado } : {} })
  return data
}

// Queda PENDIENTE: el stock no se mueve hasta que se completa.
export async function solicitarTransferencia(payload: SolicitarTransferenciaPayload): Promise<Transferencia> {
  const { data } = await httpClient.post<Transferencia>(URL, payload)
  return data
}

// Solo Administrador/Supervisor (el backend da 403 al resto).
export async function completarTransferencia(id: number): Promise<Transferencia> {
  const { data } = await httpClient.post<Transferencia>(`${URL}${id}/completar/`)
  return data
}

export async function rechazarTransferencia({ id, motivo }: { id: number; motivo: string }): Promise<Transferencia> {
  const { data } = await httpClient.post<Transferencia>(`${URL}${id}/rechazar/`, { motivo })
  return data
}
