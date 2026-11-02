import { useEffect, useRef, useState, type InputHTMLAttributes } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { Input } from './Input'
import { cx } from './cx'

// Campo de contraseña con botón de ojo para verla. Cada campo recuerda lo
// suyo; vuelve a ocultarse al enviar su formulario y al desmontarse (los
// modales y paneles desmontan su contenido al cerrarse). autoComplete es
// obligatorio: current-password en el login, new-password al crear o
// restablecer.

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'autoComplete'> {
  autoComplete: 'current-password' | 'new-password'
  invalido?: boolean
}

export function PasswordInput({ className, ...props }: Props) {
  const [visible, setVisible] = useState(false)
  const contenedor = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const form = contenedor.current?.closest('form')
    if (!form) return
    const ocultar = () => setVisible(false)
    form.addEventListener('submit', ocultar)
    return () => form.removeEventListener('submit', ocultar)
  }, [])

  const etiqueta = visible ? 'Ocultar contraseña' : 'Mostrar contraseña'

  return (
    <div ref={contenedor} className="relative">
      <Input type={visible ? 'text' : 'password'} className={cx('pr-11', className)} {...props} />
      <button
        type="button"
        aria-label={etiqueta}
        aria-pressed={visible}
        title={etiqueta}
        onClick={() => setVisible((v) => !v)}
        disabled={props.disabled}
        className={cx(
          'transicion absolute right-1.5 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full',
          'text-muted hover:bg-surf hover:text-ink outline-none focus-visible:ring-2 focus-visible:ring-acc',
          'disabled:pointer-events-none disabled:opacity-40',
        )}
      >
        {visible ? <EyeOff size={17} aria-hidden /> : <Eye size={17} aria-hidden />}
      </button>
    </div>
  )
}
