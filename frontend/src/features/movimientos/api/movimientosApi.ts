import { httpClient } from '../../../shared/api/httpClient'

// Espeja los serializers de movimientos
// (backend/apps/movimientos/interfaces/api/serializers.py).
// ENTRADA/SALIDA: operación normal del mostrador. AJUSTE_*: corrección de
// stock (solo Administrador/Supervisor, con motivo).
export type TipoOperacion = 'ENTRADA' | 'SALIDA'
export type TipoMovimiento = TipoOperacion | 'AJUSTE_POSITIVO' | 'AJUSTE_NEGATIVO'
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
  // Por qué se corrigió el stock (solo en ajustes; vacío en el resto).
  motivo: string
  creado_en: string
}

export interface RegistrarMovimientoPayload {
  herramienta: number
  sucursal: number
  tipo_movimiento: TipoOperacion
  tipo_unidad: TipoUnidad
  cantidad: number
}

export interface RegistrarAjustePayload {
  herramienta: number
  sucursal: number
  sentido: 'POSITIVO' | 'NEGATIVO'
  tipo_unidad: TipoUnidad
  cantidad: number
  motivo: string
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

// Endpoint aparte del de entradas/salidas: el backend responde 403 si
// quien lo llama no es Administrador ni Supervisor.
export async function registrarAjuste(payload: RegistrarAjustePayload): Promise<Movimiento> {
  const { data } = await httpClient.post<Movimiento>(`${URL}ajustes/`, payload)
  return data
}

export async function consultarStock(herramienta: number): Promise<StockEnSucursal[]> {
  const { data } = await httpClient.get<StockEnSucursal[]>(`${URL}stock/`, { params: { herramienta } })
  return data
}
