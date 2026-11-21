import { useState } from 'react'

// Estado de un formulario con validación al instante. `validar` recibe los
// valores y devuelve campo -> mensaje (o null). Cada error se muestra
// debajo de su campo desde que se escribe en él o se sale de él (no antes,
// para no llenar de rojo un formulario recién abierto), y el botón de
// guardar queda deshabilitado mientras haya algún error (`valido`).
//
// Los errores del backend (usuario repetido, contraseña común...) se
// pasan a `error(campo, delServidor)`: se muestran hasta que se vuelve a
// editar ese campo.

export type Errores<T> = Partial<Record<keyof T, string | null>>

type Marcas<T> = Partial<Record<keyof T, boolean>>

export function useFormulario<T extends { [K in keyof T]: string }>(inicial: T, validar: (valores: T) => Errores<T>) {
  const [valores, setValores] = useState<T>(inicial)
  const [tocados, setTocados] = useState<Marcas<T>>({})
  const [editados, setEditados] = useState<Marcas<T>>({})
  const errores = validar(valores)
  const valido = Object.values(errores).every((e) => !e)

  function cambiar<K extends keyof T>(campo: K, valor: T[K]) {
    setValores((prev) => ({ ...prev, [campo]: valor }))
    setTocados((prev) => (prev[campo] ? prev : { ...prev, [campo]: true }))
    setEditados((prev) => (prev[campo] ? prev : { ...prev, [campo]: true }))
  }

  function tocar(campo: keyof T) {
    setTocados((prev) => (prev[campo] ? prev : { ...prev, [campo]: true }))
  }

  // El mensaje para mostrar debajo del campo: el del formulario si ya se
  // tocó, si no el del backend si no se editó desde el último envío.
  function error(campo: keyof T, delServidor?: Partial<Record<string, string>>): string | undefined {
    const local = tocados[campo] ? errores[campo] : null
    if (local) return local
    return editados[campo] ? undefined : delServidor?.[campo as string]
  }

  // Al enviar: muestra todos los errores pendientes y vuelve a dar lugar a
  // los del backend. Devuelve si se puede enviar.
  function enviar(): boolean {
    setTocados(Object.fromEntries(Object.keys(valores).map((c) => [c, true])) as Marcas<T>)
    setEditados({})
    return valido
  }

  function reiniciar(nuevos: T = inicial) {
    setValores(nuevos)
    setTocados({})
    setEditados({})
  }

  return { valores, setValores, errores, valido, cambiar, tocar, error, enviar, reiniciar }
}
