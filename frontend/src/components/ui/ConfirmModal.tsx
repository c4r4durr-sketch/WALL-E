import type { ReactNode } from 'react'
import { Button } from './Button'
import { Modal } from './Modal'
import { Aviso } from './Aviso'

// Confirmación de una acción que no se deshace fácil (eliminar,
// desactivar). El botón de confirmar es secundario en rojo: la acción
// primaria naranja queda reservada para la pantalla.

interface Props {
  abierto: boolean
  onCerrar: () => void
  onConfirmar: () => void
  titulo: string
  children: ReactNode
  textoConfirmar: string
  cargando?: boolean
  error?: string | null
}

export function ConfirmModal({ abierto, onCerrar, onConfirmar, titulo, children, textoConfirmar, cargando = false, error }: Props) {
  return (
    <Modal
      abierto={abierto}
      onCerrar={onCerrar}
      titulo={titulo}
      pie={
        <>
          <Button variante="ghost" onClick={onCerrar}>Cancelar</Button>
          <Button peligro onClick={onConfirmar} cargando={cargando}>{textoConfirmar}</Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="text-muted">{children}</div>
        {error && <Aviso tono="error">{error}</Aviso>}
      </div>
    </Modal>
  )
}
