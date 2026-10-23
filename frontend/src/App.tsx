import { RouterProvider } from 'react-router-dom'
import { MotionConfig } from 'motion/react'
import { QueryProvider } from './app/providers/QueryProvider'
import { ThemeProvider } from './app/providers/ThemeProvider'
import { router } from './app/router'

// Composición raíz de la app: envuelve el router con los providers
// globales. MotionConfig respeta prefers-reduced-motion en todas las
// animaciones de motion.
export default function App() {
  return (
    <ThemeProvider>
      <MotionConfig reducedMotion="user">
        <QueryProvider>
          <RouterProvider router={router} />
        </QueryProvider>
      </MotionConfig>
    </ThemeProvider>
  )
}
