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
