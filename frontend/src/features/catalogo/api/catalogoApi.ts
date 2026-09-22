import { httpClient } from '../../../shared/api/httpClient'

// Espeja el serializer de HerramientaViewSet
// (backend/apps/catalogo/interfaces/api/serializers.py).
export interface Herramienta {
  id: number
  codigo: string
  nombre: string
  modelo: string
  unidades_por_caja: number
  // Datos de entrada para EOQ/ROP: opcionales (null si no se cargaron).
  demanda_anual: number | null
  costo_pedido: number | null
  costo_almacenamiento_unitario: number | null
  tiempo_entrega_dias: number | null
}

export type HerramientaPayload = Omit<Herramienta, 'id'>

export async function listarHerramientas(): Promise<Herramienta[]> {
  const { data } = await httpClient.get<Herramienta[]>('/catalogo/herramientas/')
  return data
}

export async function crearHerramienta(payload: HerramientaPayload): Promise<Herramienta> {
  const { data } = await httpClient.post<Herramienta>('/catalogo/herramientas/', payload)
  return data
}
