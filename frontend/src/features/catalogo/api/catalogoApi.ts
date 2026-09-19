import { httpClient } from '../../../shared/api/httpClient'

// Espeja el serializer de HerramientaViewSet
// (backend/apps/catalogo/interfaces/api/serializers.py).
export interface Herramienta {
  id: number
  codigo: string
  nombre: string
  modelo: string
  unidades_por_caja: number
}

export async function listarHerramientas(): Promise<Herramienta[]> {
  const { data } = await httpClient.get<Herramienta[]>('/catalogo/herramientas/')
  return data
}
