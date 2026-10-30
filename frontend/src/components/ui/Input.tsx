import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'
import { clasesControl, useCampo } from './campo'
import { cx } from './cx'

// Controles de formulario (docs/DISENO.md: fondo --surf2, radio 14, sin
// borde, anillo de foco en el acento). Dentro de un Field toman su id y
// sus atributos de accesibilidad; `invalido` fuerza el estado de error.

export function Input({ invalido, className, id, ...props }: InputHTMLAttributes<HTMLInputElement> & { invalido?: boolean }) {
  const campo = useCampo()
  const conError = invalido ?? campo?.invalido ?? false
  return (
    <input
      id={id ?? campo?.id}
      aria-describedby={campo?.describedBy}
      aria-invalid={conError || undefined}
      className={cx(clasesControl(conError), 'h-10', props.type === 'number' && 'tabular-nums', className)}
      {...props}
    />
  )
}

export function Select({ invalido, className, id, children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { invalido?: boolean }) {
  const campo = useCampo()
  const conError = invalido ?? campo?.invalido ?? false
  return (
    <div className="relative">
      <select
        id={id ?? campo?.id}
        aria-describedby={campo?.describedBy}
        aria-invalid={conError || undefined}
        className={cx(clasesControl(conError), 'h-10 appearance-none pr-9', className)}
        {...props}
      >
        {children}
      </select>
      <ChevronDown size={16} aria-hidden className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted" />
    </div>
  )
}

export function Textarea({ invalido, className, id, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { invalido?: boolean }) {
  const campo = useCampo()
  const conError = invalido ?? campo?.invalido ?? false
  return (
    <textarea
      id={id ?? campo?.id}
      aria-describedby={campo?.describedBy}
      aria-invalid={conError || undefined}
      className={cx(clasesControl(conError), 'min-h-20 resize-y py-2.5', className)}
      {...props}
    />
  )
}
