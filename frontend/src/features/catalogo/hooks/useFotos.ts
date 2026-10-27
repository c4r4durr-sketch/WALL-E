import { useMemo } from 'react'
import { useHerramientas } from './useHerramientas'

// id de herramienta -> URL de su foto, para las tablas de otras pantallas
// cuyos endpoints no traen la foto (panel, ABC, cierre...). Reusa la
// consulta del catálogo (misma clave de caché), no hace otra petición.
export function useFotos(): (herramientaId: number) => string | null {
  const { data } = useHerramientas()
  return useMemo(() => {
    const fotos = new Map(data?.map((h) => [h.id, h.imagen]))
    return (id: number) => fotos.get(id) ?? null
  }, [data])
}
