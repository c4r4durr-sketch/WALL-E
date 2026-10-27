import { useEffect, useState } from 'react'

// Preferencias de pantalla de este navegador (vista del catálogo, grupos
// abiertos de la barra lateral...). localStorage puede fallar (modo
// privado, almacenamiento bloqueado): en ese caso se usa el valor por
// defecto y la pantalla funciona igual, solo que no lo recuerda.

export function leerPreferencia<T>(clave: string, porDefecto: T): T {
  try {
    const guardado = localStorage.getItem(clave)
    return guardado === null ? porDefecto : (JSON.parse(guardado) as T)
  } catch {
    return porDefecto
  }
}

export function guardarPreferencia<T>(clave: string, valor: T): void {
  try {
    localStorage.setItem(clave, JSON.stringify(valor))
  } catch {
    // Sin almacenamiento: no se recuerda, nada más.
  }
}

export function usePreferencia<T>(clave: string, porDefecto: T): [T, (valor: T) => void] {
  const [valor, setValor] = useState<T>(() => leerPreferencia(clave, porDefecto))
  useEffect(() => guardarPreferencia(clave, valor), [clave, valor])
  return [valor, setValor]
}
