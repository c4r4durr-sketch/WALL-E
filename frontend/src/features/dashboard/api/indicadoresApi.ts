import { httpClient } from '../../../shared/api/httpClient'

// Espeja las respuestas de los endpoints de indicadores
// (backend/apps/indicadores/interfaces/api/serializers.py):
// EOQ, punto de reorden (ROP) y clasificación ABC.
export interface IndicadorHerramienta {
  herramienta: number
  eoq: number
  punto_reorden: number
  clasificacion_abc: 'A' | 'B' | 'C'
}

export async function listarIndicadores(): Promise<IndicadorHerramienta[]> {
  const { data } = await httpClient.get<IndicadorHerramienta[]>('/indicadores/')
  return data
}
