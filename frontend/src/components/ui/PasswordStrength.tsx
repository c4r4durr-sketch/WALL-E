import { Check, Circle } from 'lucide-react'
import { nivelPassword, requisitosPassword, type DatosCuenta } from '../../shared/validacion'
import { cx } from './cx'

// Barra de seguridad de la contraseña, para ir debajo de PasswordInput
// (Nueva cuenta y Restablecer contraseña; en el Login no). Cuatro
// segmentos que se llenan y cambian de color según la fuerza, y la lista
// de requisitos de la política (la misma del backend) que se va marcando
// mientras se escribe. Solo colores de DISENO.md: --danger, --acc
// (naranja), --warn y --ok, con su valor claro y oscuro.

const NIVELES = [
  null,
  { texto: 'Débil', barra: 'bg-danger', tinta: 'text-danger' },
  { texto: 'Regular', barra: 'bg-acc', tinta: 'text-acc' },
  { texto: 'Buena', barra: 'bg-warn', tinta: 'text-warn' },
  { texto: 'Fuerte', barra: 'bg-ok', tinta: 'text-ok' },
] as const

interface Props {
  password: string
  // Datos de la cuenta con los que no se debe parecer.
  cuenta: DatosCuenta
  id?: string
}

export function PasswordStrength({ password, cuenta, id }: Props) {
  const requisitos = requisitosPassword(password, cuenta)
  const nivel = nivelPassword(password, requisitos)
  const estilo = NIVELES[nivel]

  return (
    <div id={id} className="mt-2.5 space-y-2.5">
      <div className="flex items-center gap-3">
        <div className="flex flex-1 gap-1.5" aria-hidden>
          {[1, 2, 3, 4].map((segmento) => (
            <span
              key={segmento}
              className={cx('transicion h-1.5 flex-1 rounded-full', estilo && segmento <= nivel ? estilo.barra : 'bg-surf2')}
            />
          ))}
        </div>
        <span aria-live="polite" className={cx('w-14 text-right text-xs font-semibold', estilo ? estilo.tinta : 'text-muted')}>
          {estilo ? estilo.texto : ''}
          {estilo && <span className="sr-only"> (seguridad de la contraseña)</span>}
        </span>
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1">
        {requisitos.map((r) => (
          <li key={r.clave} className={cx('flex items-center gap-1.5 text-xs', r.cumple ? 'text-ok' : 'text-muted')}>
            {r.cumple ? <Check size={14} aria-hidden /> : <Circle size={12} aria-hidden className="mx-px" />}
            {r.texto}
            <span className="sr-only">{r.cumple ? ': cumple' : ': falta'}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
