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

// --- Antigüedad del stock (HU22): GET /api/indicadores/antiguedad/ ---
// Espeja ReporteAntiguedadSerializer. Los montos llegan como texto
// (DecimalField de DRF), igual que el costo unitario del catálogo.

export interface LineaAntiguedad {
  herramienta_id: number
  codigo: string
  nombre: string
  sucursal_id: number
  sucursal_nombre: string
  stock: number
  ultima_venta: string | null
  dias_sin_venta: number
  nunca_vendida: boolean
  tramo: string
  estancada: boolean
  costo_unitario: string | null
  valor_inmovilizado: string | null
}

export interface TotalTramo {
  tramo: string
  lineas: number
  unidades: number
}

export interface ReporteAntiguedad {
  fecha: string
  sucursal_id: number | null
  dias_minimos: number
  dias_para_estancamiento: number
  lineas: LineaAntiguedad[]
  tramos: TotalTramo[]
  total_unidades: number
  total_estancadas: number
  valor_inmovilizado_estancado: string
  lineas_sin_costo: number
}

// Sin `sucursal`: el Administrador ve todas; el Supervisor, la suya.
export interface FiltroAntiguedad {
  sucursal?: number
  dias_minimos: number
}

export async function obtenerAntiguedad(filtro: FiltroAntiguedad): Promise<ReporteAntiguedad> {
  const { data } = await httpClient.get<ReporteAntiguedad>('/indicadores/antiguedad/', { params: filtro })
  return data
}
