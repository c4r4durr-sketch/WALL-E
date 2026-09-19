import { RouterProvider } from 'react-router-dom'
import { QueryProvider } from './app/providers/QueryProvider'
import { router } from './app/router'

// Composición raíz de la app: envuelve el router con los providers
// globales. Cuando exista un contexto de sesión/rol, también se agrega acá
// (por encima del router, ya que las rutas lo van a necesitar).
export default function App() {
  return (
    <QueryProvider>
      <RouterProvider router={router} />
    </QueryProvider>
  )
}
