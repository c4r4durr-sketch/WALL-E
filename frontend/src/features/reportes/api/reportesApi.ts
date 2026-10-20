import { httpClient } from '../../../shared/api/httpClient'
import type { TipoMovimiento, TipoUnidad } from '../../movimientos/api/movimientosApi'

// Espeja CierreDiarioSerializer
// (backend/apps/indicadores/interfaces/api/serializers.py).
export interface LineaCierre {
  movimiento_id: number
  fecha_hora: string
  herramienta_id: number
  codigo: string
  nombre: string
  tipo_movimiento: TipoMovimiento
  tipo_unidad: TipoUnidad
  cantidad: number
  cantidad_unidades: number
  usuario: string
  motivo: string
}

export interface TotalPorTipo {
  tipo_movimiento: TipoMovimiento
  movimientos: number
  unidades: number
}

export interface CierreDiario {
  fecha: string
  sucursal_id: number
  sucursal_nombre: string
  lineas: LineaCierre[]
  totales: TotalPorTipo[]
  total_salidas_unidades: number
  cantidad_salidas: number
}

// HU14. `sucursal` es obligatoria para el Administrador; el Supervisor
// puede omitirla (el backend usa la suya).
export async function obtenerCierreDiario(filtro: { sucursal?: number; fecha: string }): Promise<CierreDiario> {
  const { data } = await httpClient.get<CierreDiario>('/indicadores/cierre-diario/', { params: filtro })
  return data
}
