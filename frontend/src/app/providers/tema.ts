import { createContext, useContext } from 'react'

// Contexto del tema (lo provee ThemeProvider). Va en su propio archivo
// para que ThemeProvider.tsx solo exporte el componente (fast refresh).

export type Tema = 'claro' | 'oscuro'

export interface ContextoTema {
  tema: Tema
  alternar: () => void
}

export const ContextoDeTema = createContext<ContextoTema | null>(null)

export function useTema(): ContextoTema {
  const contexto = useContext(ContextoDeTema)
  if (!contexto) throw new Error('useTema debe usarse dentro de ThemeProvider')
  return contexto
}
