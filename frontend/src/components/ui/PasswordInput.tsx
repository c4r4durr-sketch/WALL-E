import { useEffect, useRef, useState, type InputHTMLAttributes } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { IconButton } from './IconButton'
import { Input } from './Input'

// Campo de contraseña con un botón para mostrarla u ocultarla. Dentro de
// un Field toma su id, su error y su aria-required como cualquier Input.
// Vuelve a ocultarse al enviar su formulario y al desmontarse (los modales
// y paneles desmontan su contenido al cerrarse). autoComplete es
// obligatorio: current-password en el login, new-password al crear o
// restablecer.

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'autoComplete'> & {
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

  return (
    <div ref={contenedor} className="relative">
      <Input type={visible ? 'text' : 'password'} className={`pr-11 ${className ?? ''}`} {...props} />
      <IconButton
        etiqueta={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        tamano="sm"
        aria-pressed={visible}
        onClick={() => setVisible((v) => !v)}
        disabled={props.disabled}
        className="absolute right-1 top-1/2 -translate-y-1/2"
      >
        {visible ? <EyeOff size={16} aria-hidden /> : <Eye size={16} aria-hidden />}
      </IconButton>
    </div>
  )
}
