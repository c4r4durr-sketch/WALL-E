import type { ReactNode } from 'react'
import { ChevronRight } from 'lucide-react'

// Encabezado de página: migas (13/500 --muted), título 36/700 y, a la
// derecha, las acciones (como mucho una primaria naranja por pantalla).

interface Props {
  migas?: string[]
  titulo: ReactNode
  subtitulo?: ReactNode
  acciones?: ReactNode
}

export function PageHeader({ migas, titulo, subtitulo, acciones }: Props) {
  return (
    <header className="flex items-end justify-between gap-6 pb-2">
      <div className="min-w-0">
        {migas && migas.length > 0 && (
          <nav aria-label="Ubicación" className="mb-1.5">
            <ol className="flex items-center gap-1 text-[13px] font-medium text-muted">
              {migas.map((miga, i) => (
                <li key={miga} className="flex items-center gap-1">
                  {i > 0 && <ChevronRight size={14} aria-hidden />}
                  {miga}
                </li>
              ))}
            </ol>
          </nav>
        )}
        <h1 className="text-[36px] font-bold leading-tight tracking-[-0.035em] text-ink">{titulo}</h1>
        {subtitulo && <p className="mt-1 text-[13px] font-medium text-muted">{subtitulo}</p>}
      </div>
      {acciones && <div className="flex shrink-0 items-center gap-2">{acciones}</div>}
    </header>
  )
}
