import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ContextoDeTema, type Tema } from './tema'

// Modo claro / oscuro (docs/DISENO.md): la clase `dark` en <html> activa
// los valores oscuros de las variables de index.css. Valor inicial: lo que
// el usuario eligió (localStorage); si nunca eligió, la preferencia del
// sistema, y mientras no elija se sigue la del sistema si cambia. El
// script de index.html aplica lo mismo antes del primer pintado.

const CLAVE = 'tema'

function temaGuardado(): Tema | null {
  try {
    const valor = localStorage.getItem(CLAVE)
    return valor === 'claro' || valor === 'oscuro' ? valor : null
  } catch {
    return null
  }
}

const consultaOscuro = () => window.matchMedia('(prefers-color-scheme: dark)')

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [elegido, setElegido] = useState<Tema | null>(temaGuardado)
  const [delSistema, setDelSistema] = useState<Tema>(() => (consultaOscuro().matches ? 'oscuro' : 'claro'))
  const tema = elegido ?? delSistema

  useEffect(() => {
    const consulta = consultaOscuro()
    const alCambiar = (e: MediaQueryListEvent) => setDelSistema(e.matches ? 'oscuro' : 'claro')
    consulta.addEventListener('change', alCambiar)
    return () => consulta.removeEventListener('change', alCambiar)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', tema === 'oscuro')
  }, [tema])

  const alternar = useCallback(() => {
    const nuevo: Tema = tema === 'oscuro' ? 'claro' : 'oscuro'
    setElegido(nuevo)
    try {
      localStorage.setItem(CLAVE, nuevo)
    } catch {
      // Sin almacenamiento: el cambio dura hasta recargar.
    }
  }, [tema])

  const valor = useMemo(() => ({ tema, alternar }), [tema, alternar])
  return <ContextoDeTema.Provider value={valor}>{children}</ContextoDeTema.Provider>
}
