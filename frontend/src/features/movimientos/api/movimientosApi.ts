import { httpClient } from '../../../shared/api/httpClient'

// Espeja los serializers de movimientos
// (backend/apps/movimientos/interfaces/api/serializers.py).
export type TipoMovimiento = 'ENTRADA' | 'SALIDA'
export type TipoUnidad = 'UNIDAD' | 'CAJA'

export interface Movimiento {
  id: number
  herramienta: number
  sucursal: number
  usuario: number
  usuario_username: string
  tipo_movimiento: TipoMovimiento
  tipo_unidad: TipoUnidad
  cantidad: number
  // Equivalente en unidades sueltas fijado al registrar (lo que cuenta
  // para el stock).
  cantidad_unidades: number
  creado_en: string
}

export interface RegistrarMovimientoPayload {
  herramienta: number
  sucursal: number
  tipo_movimiento: TipoMovimiento
  tipo_unidad: TipoUnidad
  cantidad: number
}

export interface StockEnSucursal {
  herramienta_id: number
  sucursal_id: number
  sucursal_nombre: string
  unidades: number
  cajas_completas: number
  unidades_sueltas: number
}

const URL = '/movimientos/'

export async function listarMovimientos(filtros: { herramienta?: number; sucursal?: number } = {}): Promise<Movimiento[]> {
  const { data } = await httpClient.get<Movimiento[]>(URL, { params: filtros })
  return data
}

// Solo alta: los movimientos no se editan ni se borran (el backend
// responde 405). Un error se corrige con un movimiento nuevo.
export async function registrarMovimiento(payload: RegistrarMovimientoPayload): Promise<Movimiento> {
  const { data } = await httpClient.post<Movimiento>(URL, payload)
  return data
}

export async function consultarStock(herramienta: number): Promise<StockEnSucursal[]> {
  const { data } = await httpClient.get<StockEnSucursal[]>(`${URL}stock/`, { params: { herramienta } })
  return data
}
