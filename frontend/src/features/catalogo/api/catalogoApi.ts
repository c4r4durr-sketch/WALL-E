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
  // URL absoluta de la foto; null en las herramientas anteriores a que la
  // foto fuera obligatoria.
  imagen: string | null
}

// HU7: un cambio del costo unitario (historial, solo lectura).
export interface CambioCosto {
  id: number
  costo_anterior: number | null
  costo_nuevo: number
  usuario: string
  fecha: string
}

export type HerramientaPayload = Omit<Herramienta, 'id' | 'proveedor_nombre' | 'imagen'>

const URL = '/catalogo/herramientas/'

// La foto viaja en multipart/form-data. Un null se manda vacío: el backend
// lo interpreta como null en los campos opcionales. El Content-Type
// explícito evita que axios convierta el FormData en JSON (httpClient
// tiene JSON por defecto); el navegador le agrega el boundary.
function aFormData(payload: HerramientaPayload, imagen: Blob): FormData {
  const datos = new FormData()
  for (const [campo, valor] of Object.entries(payload)) {
    datos.append(campo, valor === null ? '' : String(valor))
  }
  datos.append('imagen', imagen, 'foto.jpg')
  return datos
}

const MULTIPART = { headers: { 'Content-Type': 'multipart/form-data' } }

export async function listarHerramientas(): Promise<Herramienta[]> {
  const { data } = await httpClient.get<Herramienta[]>(URL)
  return data
}

// La foto es obligatoria en el alta (el backend responde 400 sin ella).
export async function crearHerramienta({ imagen, ...payload }: HerramientaPayload & { imagen: Blob }): Promise<Herramienta> {
  const { data } = await httpClient.post<Herramienta>(URL, aFormData(payload, imagen), MULTIPART)
  return data
}

// PUT (no PATCH): el formulario de edición siempre manda todos los campos,
// así un dato de EOQ que se vacía en el formulario queda en null. Sin foto
// nueva va en JSON y la foto no cambia; con foto nueva, en multipart.
export async function actualizarHerramienta(
  { id, imagen, ...payload }: HerramientaPayload & { id: number; imagen?: Blob | null },
): Promise<Herramienta> {
  const { data } = imagen
    ? await httpClient.put<Herramienta>(`${URL}${id}/`, aFormData(payload, imagen), MULTIPART)
    : await httpClient.put<Herramienta>(`${URL}${id}/`, payload)
  return data
}

export async function listarHistorialCostos(id: number): Promise<CambioCosto[]> {
  const { data } = await httpClient.get<CambioCosto[]>(`${URL}${id}/historial-costos/`)
  return data
}

export async function eliminarHerramienta(id: number): Promise<void> {
  await httpClient.delete(`${URL}${id}/`)
}
