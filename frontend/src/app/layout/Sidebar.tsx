import { useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { ChevronRight, LogOut, Moon, Sun } from 'lucide-react'
import { IconButton, cx } from '../../components/ui'
import { TRANSICION } from '../../components/ui/movimiento'
import { useLogout } from '../../features/auth/hooks/useLogout'
import type { SessionClaims } from '../../features/auth/session'
import { ROL_LABEL } from '../../features/usuarios/roles'
import { usePreferencia } from '../../shared/hooks/usePreferencia'
import { useTema } from '../providers/tema'
import { PANEL, estaActiva, gruposVisibles, type ItemNav } from './navegacion'

// Barra lateral flotante de vidrio (264 px, radio 28). Grupos
// desplegables: el de la página actual se abre solo y lo que el usuario
// abre o cierra se recuerda en este navegador. Abajo, quién está
// conectado, el interruptor de tema y cerrar sesión.

function Enlace({ item }: { item: ItemNav }) {
  const Icono = item.icono
  return (
    <NavLink
      to={item.ruta}
      end={item.ruta === '/'}
      className={({ isActive }) =>
        cx(
          'transicion flex h-9 items-center gap-3 rounded-chip px-3 text-sm',
          isActive ? 'bg-soft font-semibold text-softink' : 'font-medium text-ink hover:bg-surf2',
        )
      }
    >
      <Icono size={18} aria-hidden className="shrink-0" />
      {item.texto}
    </NavLink>
  )
}

function iniciales(sesion: SessionClaims): string {
  const letras = `${sesion.first_name.charAt(0)}${sesion.last_name.charAt(0)}`.trim()
  return (letras || sesion.username.slice(0, 2)).toUpperCase()
}

export function Sidebar({ sesion }: { sesion: SessionClaims }) {
  const { pathname } = useLocation()
  const { tema, alternar } = useTema()
  const logout = useLogout()
  const reducido = useReducedMotion()
  const grupos = gruposVisibles(sesion.rol)
  const [abiertos, setAbiertos] = usePreferencia<string[]>('nav-grupos-abiertos', [])

  // El grupo de la página actual se abre solo (y queda recordado).
  const grupoActual = grupos.find((g) => g.items.some((i) => estaActiva(i.ruta, pathname)))?.id
  useEffect(() => {
    if (grupoActual && !abiertos.includes(grupoActual)) setAbiertos([...abiertos, grupoActual])
  }, [grupoActual, abiertos, setAbiertos])

  function alternarGrupo(id: string) {
    setAbiertos(abiertos.includes(id) ? abiertos.filter((g) => g !== id) : [...abiertos, id])
  }

  const nombre = `${sesion.first_name} ${sesion.last_name}`.trim() || sesion.username

  return (
    <aside className="vidrio fixed bottom-3.5 left-3.5 top-3.5 z-30 flex w-[264px] flex-col rounded-panel">
      <div className="flex items-center gap-2.5 px-5 pb-4 pt-6">
        <span aria-hidden className="flex h-8 w-8 items-center justify-center rounded-chip bg-acc text-sm font-bold text-on-acc">
          W
        </span>
        <span className="text-[15px] font-bold tracking-[-0.02em] text-ink">Walle-Importaciones</span>
      </div>

      <nav aria-label="Principal" className="min-h-0 flex-1 space-y-1 overflow-y-auto px-3 pb-3">
        <Enlace item={PANEL} />
        {grupos.map((grupo) => {
          const abierto = abiertos.includes(grupo.id)
          const idLista = `nav-${grupo.id}`
          return (
            <div key={grupo.id} className="pt-2">
              <button
                type="button"
                onClick={() => alternarGrupo(grupo.id)}
                aria-expanded={abierto}
                aria-controls={idLista}
                className="transicion flex h-8 w-full items-center justify-between rounded-chip px-3 text-xs font-semibold text-muted hover:text-ink"
              >
                {grupo.texto}
                <ChevronRight size={14} aria-hidden className={cx('transicion', abierto && 'rotate-90')} />
              </button>
              <AnimatePresence initial={false}>
                {abierto && (
                  <motion.ul
                    id={idLista}
                    className="space-y-0.5 overflow-hidden"
                    initial={reducido ? false : { height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={reducido ? { opacity: 0 } : { height: 0, opacity: 0 }}
                    transition={TRANSICION}
                  >
                    {grupo.items.map((item) => (
                      <li key={item.ruta}>
                        <Enlace item={item} />
                      </li>
                    ))}
                  </motion.ul>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </nav>

      <div className="m-3 flex items-center gap-3 rounded-card bg-surf p-3 shadow-sh">
        <span aria-hidden className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-acc text-xs font-bold text-on-acc">
          {iniciales(sesion)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-ink">{nombre}</p>
          <p className="truncate text-xs text-muted">
            {ROL_LABEL[sesion.rol]}
            {sesion.sucursal_nombre && ` · ${sesion.sucursal_nombre}`}
          </p>
        </div>
        <IconButton tamano="sm" etiqueta={tema === 'oscuro' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'} onClick={alternar}>
          {tema === 'oscuro' ? <Sun size={16} aria-hidden /> : <Moon size={16} aria-hidden />}
        </IconButton>
        <IconButton tamano="sm" etiqueta="Cerrar sesión" onClick={logout}>
          <LogOut size={16} aria-hidden />
        </IconButton>
      </div>
    </aside>
  )
}
