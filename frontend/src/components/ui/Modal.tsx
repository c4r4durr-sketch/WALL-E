import { forwardRef, type ReactNode } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { X } from 'lucide-react'
import { IconButton } from './IconButton'
import { TRANSICION } from './movimiento'
import { cx } from './cx'

// Ventanas sobre la página (vidrio): Modal centrado (confirmaciones) y
// SidePanel a la derecha (formularios, detalles). Radix se ocupa de la
// accesibilidad (foco atrapado, Escape, aria-modal, devolver el foco);
// motion, de la entrada: escala 0.96 -> 1 con opacidad.

interface PropsBase {
  abierto: boolean
  onCerrar: () => void
  titulo: ReactNode
  descripcion?: ReactNode
  children: ReactNode
  // Botones de abajo (Cancelar / Confirmar).
  pie?: ReactNode
}

// forwardRef: Dialog.Portal envuelve a cada hijo en un Presence que le pasa
// un ref; sin esto React avisa "Function components cannot be given refs".
const Fondo = forwardRef<HTMLDivElement>(function Fondo(_, ref) {
  return (
    <Dialog.Overlay ref={ref} asChild forceMount>
      <motion.div
        className="fixed inset-0 z-40 bg-velo"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={TRANSICION}
      />
    </Dialog.Overlay>
  )
})

function Encabezado({ titulo, descripcion, onCerrar }: Pick<PropsBase, 'titulo' | 'descripcion' | 'onCerrar'>) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <Dialog.Title className="text-xl font-bold tracking-[-0.02em] text-ink">{titulo}</Dialog.Title>
        {descripcion ? (
          <Dialog.Description className="mt-1 text-[13px] text-muted">{descripcion}</Dialog.Description>
        ) : (
          <Dialog.Description className="sr-only">{titulo}</Dialog.Description>
        )}
      </div>
      <Dialog.Close asChild>
        <IconButton etiqueta="Cerrar" onClick={onCerrar}>
          <X size={18} aria-hidden />
        </IconButton>
      </Dialog.Close>
    </div>
  )
}

export function Modal({ abierto, onCerrar, titulo, descripcion, children, pie }: PropsBase) {
  const reducido = useReducedMotion()
  return (
    <Dialog.Root open={abierto} onOpenChange={(abrir) => !abrir && onCerrar()}>
      <AnimatePresence>
        {abierto && (
          <Dialog.Portal forceMount>
            <Fondo />
            <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-6">
              <Dialog.Content asChild forceMount>
                <motion.div
                  className="vidrio pointer-events-auto w-full max-w-md space-y-5 rounded-panel p-6"
                  initial={reducido ? false : { opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={reducido ? { opacity: 0 } : { opacity: 0, scale: 0.96 }}
                  transition={TRANSICION}
                >
                  <Encabezado titulo={titulo} descripcion={descripcion} onCerrar={onCerrar} />
                  <div className="text-sm text-ink">{children}</div>
                  {pie && <div className="flex justify-end gap-2">{pie}</div>}
                </motion.div>
              </Dialog.Content>
            </div>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  )
}

export function SidePanel({ abierto, onCerrar, titulo, descripcion, children, pie, ancho = 'md' }: PropsBase & { ancho?: 'md' | 'lg' }) {
  const reducido = useReducedMotion()
  return (
    <Dialog.Root open={abierto} onOpenChange={(abrir) => !abrir && onCerrar()}>
      <AnimatePresence>
        {abierto && (
          <Dialog.Portal forceMount>
            <Fondo />
            <Dialog.Content asChild forceMount>
              <motion.aside
                className={cx(
                  'vidrio fixed bottom-3.5 right-3.5 top-3.5 z-50 flex w-full flex-col rounded-panel',
                  ancho === 'md' ? 'max-w-[460px]' : 'max-w-[620px]',
                )}
                style={{ transformOrigin: 'right center' }}
                initial={reducido ? false : { opacity: 0, scale: 0.96, x: 24 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={reducido ? { opacity: 0 } : { opacity: 0, scale: 0.96, x: 24 }}
                transition={TRANSICION}
              >
                <div className="px-6 pb-4 pt-6">
                  <Encabezado titulo={titulo} descripcion={descripcion} onCerrar={onCerrar} />
                </div>
                <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6">{children}</div>
                {pie && <div className="flex justify-end gap-2 border-t border-line px-6 py-4">{pie}</div>}
              </motion.aside>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  )
}
