import { httpClient } from '../../../shared/api/httpClient'

// Espejan los serializers de indicadores
// (backend/apps/indicadores/interfaces/api/serializers.py). Cada indicador
// tiene su propia ruta en el backend (indicadores/interfaces/api/urls.py):
//   GET /api/indicadores/eoq/<herramienta_id>/
//   GET /api/indicadores/rop/<herramienta_id>/
//   GET /api/indicadores/abc/

export interface ResultadoEOQ {
  herramienta_id: number
  demanda_anual: number
  costo_pedido: number
  costo_almacenamiento_unitario: number
  eoq: number
}

export interface ResultadoROP {
  herramienta_id: number
  demanda_diaria_promedio: number
  lead_time_dias: number
  punto_reorden: number
}

export interface ClasificacionABC {
  herramienta_id: number
  valor_consumo: number
  porcentaje_acumulado: number
  clase: 'A' | 'B' | 'C'
}

export async function obtenerEOQ(herramientaId: number): Promise<ResultadoEOQ> {
  const { data } = await httpClient.get<ResultadoEOQ>(`/indicadores/eoq/${herramientaId}/`)
  return data
}

export async function obtenerROP(herramientaId: number): Promise<ResultadoROP> {
  const { data } = await httpClient.get<ResultadoROP>(`/indicadores/rop/${herramientaId}/`)
  return data
}

export async function obtenerClasificacionABC(): Promise<ClasificacionABC[]> {
  const { data } = await httpClient.get<ClasificacionABC[]>('/indicadores/abc/')
  return data
}

// --- Panel principal (HU24): GET /api/indicadores/panel/ ---

export interface AlertaReorden {
  herramienta_id: number
  codigo: string
  nombre: string
  stock_total: number
  punto_reorden: number
  // EOQ redondeado a cajas cerradas; null si faltan costos para calcularlo.
  pedido_sugerido: number | null
  unidades_por_caja: number
}

export interface HerramientaEstancada {
  herramienta_id: number
  codigo: string
  nombre: string
  sucursal_id: number
  sucursal_nombre: string
  stock: number
  dias_sin_venta: number
  nunca_vendida: boolean
}

export interface PanelAuditoria {
  total_alertas_stock: number
  total_herramientas_estancadas: number
  total_herramientas: number
  total_sucursales_activas: number
  herramientas_sin_datos_rop: number
  dias_para_estancamiento: number
  alertas: AlertaReorden[]
  estancadas: HerramientaEstancada[]
}

export async function obtenerPanel(): Promise<PanelAuditoria> {
  const { data } = await httpClient.get<PanelAuditoria>('/indicadores/panel/')
  return data
}
