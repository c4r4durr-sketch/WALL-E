import { useId, type ReactNode } from 'react'
import { ContextoDeCampo } from './campo'
import { cx } from './cx'

// Etiqueta + control + ayuda o error. Conecta todo para el lector de
// pantalla: la etiqueta apunta al control, y el control anuncia la ayuda
// o el error (aria-describedby) y si es inválido (aria-invalid).

interface Props {
  etiqueta: ReactNode
  children: ReactNode
  ayuda?: ReactNode
  error?: string | null
  // Para la etiqueta: "(opcional)" en gris, sin asteriscos.
  opcional?: boolean
  id?: string
  className?: string
}

export function Field({ etiqueta, children, ayuda, error, opcional = false, id, className }: Props) {
  const generado = useId()
  const idControl = id ?? generado
  const idAyuda = `${idControl}-ayuda`
  const idError = `${idControl}-error`
  const describedBy = error ? idError : ayuda ? idAyuda : undefined

  return (
    <ContextoDeCampo.Provider value={{ id: idControl, describedBy, invalido: Boolean(error) }}>
      <div className={cx('min-w-0', className)}>
        <label htmlFor={idControl} className="mb-1.5 block text-xs font-semibold text-muted">
          {etiqueta}
          {opcional && <span className="font-medium"> (opcional)</span>}
        </label>
        {children}
        {error ? (
          <p id={idError} className="mt-1.5 text-xs font-medium text-danger">{error}</p>
        ) : (
          ayuda && <p id={idAyuda} className="mt-1.5 text-xs text-muted">{ayuda}</p>
        )}
      </div>
    </ContextoDeCampo.Provider>
  )
}
