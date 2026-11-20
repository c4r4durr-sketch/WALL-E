import { useState, type InputHTMLAttributes } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { IconButton } from './IconButton'
import { Input } from './Input'

// Campo de contraseña con un botón para mostrarla u ocultarla. Dentro de
// un Field toma su id, su error y su aria-required como cualquier Input.

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & { invalido?: boolean }

export function PasswordInput({ className, ...props }: Props) {
  const [visible, setVisible] = useState(false)
  return (
    <div className="relative">
      <Input type={visible ? 'text' : 'password'} className={`pr-11 ${className ?? ''}`} {...props} />
      <IconButton
        etiqueta={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        tamano="sm"
        aria-pressed={visible}
        onClick={() => setVisible((v) => !v)}
        className="absolute right-1 top-1/2 -translate-y-1/2"
      >
        {visible ? <EyeOff size={16} aria-hidden /> : <Eye size={16} aria-hidden />}
      </IconButton>
    </div>
  )
}
