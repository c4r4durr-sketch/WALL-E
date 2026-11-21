import { httpClient } from '../../../shared/api/httpClient'

// Reportes estadísticos: GET /api/indicadores/estadisticas/<reporte>/.
// Espeja backend/apps/indicadores/interfaces/api/serializers_estadisticas.py.
// Los montos llegan como texto (DecimalField de DRF) y los meses como
// "AAAA-MM".

export interface FiltroEstadisticas {
  desde: string
  hasta: string
  // Sin sucursal: todas (Administrador) o la propia (Supervisor).
  sucursal?: number
}

export interface Periodo {
  desde: string
  hasta: string
  sucursal_id: number | null
}

export interface MovimientosMes {
  mes: string
  entradas: number
  salidas: number
  ajustes_positivos: number
  ajustes_negativos: number
}

export interface VentaHerramienta {
  herramienta_id: number
  codigo: string
  nombre: string
  unidades: number
  monto: string | null
}

export interface StockSucursal {
  sucursal_id: number
  nombre: string
  unidades: number
  valor: string
  unidades_sin_costo: number
}

export type Clase = 'A' | 'B' | 'C'

export interface TotalClase {
  clase: Clase
  herramientas: number
  valor: string
  porcentaje_valor: number
}

export interface PuntoPareto {
  herramienta_id: number
  codigo: string
  nombre: string
  valor: string
  porcentaje: number
  porcentaje_acumulado: number
  clase: Clase
}

export interface TramoValor {
  tramo: string
  herramientas: number
  unidades: number
  valor: string
}

export type EstadoTransferencia = 'PENDIENTE' | 'COMPLETADA' | 'RECHAZADA'

export interface TransferenciasMes {
  mes: string
  pendientes: number
  completadas: number
  rechazadas: number
}

export interface Estadisticas {
  resumen: {
    periodo: Periodo
    total_movimientos: number
    unidades_vendidas: number
    valor_inventario: string
    alertas_reorden: number
    herramientas_estancadas: number
  }
  'movimientos-por-mes': { periodo: Periodo; meses: MovimientosMes[] }
  'top-herramientas': { periodo: Periodo; herramientas: VentaHerramienta[] }
  'stock-por-sucursal': { periodo: Periodo; sucursales: StockSucursal[]; total_unidades: number; total_valor: string }
  abc: { periodo: Periodo; clases: TotalClase[]; pareto: PuntoPareto[]; valor_total: string; herramientas_sin_costo: number }
  antiguedad: { periodo: Periodo; tramos: TramoValor[]; valor_total: string; lineas_sin_costo: number }
  transferencias: {
    periodo: Periodo
    por_estado: { estado: EstadoTransferencia; cantidad: number }[]
    por_mes: TransferenciasMes[]
    total: number
  }
}

export type Reporte = keyof Estadisticas

export async function obtenerEstadistica<R extends Reporte>(reporte: R, filtro: FiltroEstadisticas): Promise<Estadisticas[R]> {
  const { data } = await httpClient.get<Estadisticas[R]>(`/indicadores/estadisticas/${reporte}/`, { params: filtro })
  return data
}
