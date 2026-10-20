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
  // HU7: costo de compra de una unidad. Solo el Administrador lo cambia.
  costo_unitario: number | null
  // HU8: proveedor al que se le compra (null = sin proveedor).
  proveedor: number | null
  proveedor_nombre: string | null
}

// HU7: un cambio del costo unitario (historial, solo lectura).
export interface CambioCosto {
  id: number
  costo_anterior: number | null
  costo_nuevo: number
  usuario: string
  fecha: string
}

export type HerramientaPayload = Omit<Herramienta, 'id' | 'proveedor_nombre'>

const URL = '/catalogo/herramientas/'

export async function listarHerramientas(): Promise<Herramienta[]> {
  const { data } = await httpClient.get<Herramienta[]>(URL)
  return data
}

export async function crearHerramienta(payload: HerramientaPayload): Promise<Herramienta> {
  const { data } = await httpClient.post<Herramienta>(URL, payload)
  return data
}

// PUT (no PATCH): el formulario de edición siempre manda todos los campos,
// así un dato de EOQ que se vacía en el formulario queda en null.
export async function actualizarHerramienta(
  { id, ...payload }: HerramientaPayload & { id: number },
): Promise<Herramienta> {
  const { data } = await httpClient.put<Herramienta>(`${URL}${id}/`, payload)
  return data
}

export async function listarHistorialCostos(id: number): Promise<CambioCosto[]> {
  const { data } = await httpClient.get<CambioCosto[]>(`${URL}${id}/historial-costos/`)
  return data
}

export async function eliminarHerramienta(id: number): Promise<void> {
  await httpClient.delete(`${URL}${id}/`)
}
