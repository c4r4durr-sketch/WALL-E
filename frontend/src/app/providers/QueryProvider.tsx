import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// Instancia única de QueryClient para toda la app. Vive en su propio
// provider (en vez de crearse directo en main.tsx) para poder ajustar acá
// las opciones globales de cache/retry de TanStack Query sin tocar el
// bootstrap de la app.
const queryClient = new QueryClient()

export function QueryProvider({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
