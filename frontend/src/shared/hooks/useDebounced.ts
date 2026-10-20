import { useEffect, useState } from 'react'

// Devuelve `valor` recién cuando deja de cambiar por `ms` milisegundos.
// Para búsquedas mientras se escribe: una consulta por pausa, no por tecla.
export function useDebounced<T>(valor: T, ms = 300): T {
  const [demorado, setDemorado] = useState(valor)
  useEffect(() => {
    const id = window.setTimeout(() => setDemorado(valor), ms)
    return () => window.clearTimeout(id)
  }, [valor, ms])
  return demorado
}
