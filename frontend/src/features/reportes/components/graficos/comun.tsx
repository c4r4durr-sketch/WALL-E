import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { Button, Card, CardHeader, Cargando, EmptyState, cx } from '../../../../components/ui'
import { mensajeDeError } from '../../../../shared/api/errores'

// Piezas comunes de los gráficos de /reportes (los colores y ejes, en
// estilo.ts).

interface TarjetaProps {
  titulo: string
  descripcion: string
  cargando: boolean
  error?: unknown
  onReintentar?: () => void
  vacio: boolean
  iconoVacio: LucideIcon
  ayudaVacio: string
  leyenda?: ReactNode
  pie?: ReactNode
  alto?: number
  children: ReactNode
}

// Tarjeta de un gráfico: título, una línea que explica qué muestra y,
// según el estado, el skeleton, el error, el estado vacío o el gráfico.
export function TarjetaGrafico({
  titulo,
  descripcion,
  cargando,
  error,
  onReintentar,
  vacio,
  iconoVacio,
  ayudaVacio,
  leyenda,
  pie,
  alto = 280,
  children,
}: TarjetaProps) {
  return (
    <Card className="imprimir-bloque flex flex-col">
      <CardHeader titulo={titulo} descripcion={descripcion} />
      <div className="mt-5 flex-1">
        {cargando ? (
          <Cargando etiqueta={`Cargando ${titulo.toLowerCase()}`}>
            <div style={{ height: alto }} className="esqueleto rounded-card" aria-hidden />
          </Cargando>
        ) : error ? (
          <div className="flex flex-col items-center justify-center gap-3 text-center" style={{ height: alto }}>
            <p className="text-sm text-danger">{mensajeDeError(error, 'No se pudo cargar este gráfico.')}</p>
            {onReintentar && <Button tamano="sm" onClick={onReintentar}>Reintentar</Button>}
          </div>
        ) : vacio ? (
          <EmptyState compacto icono={iconoVacio} titulo="Sin datos en este periodo" ayuda={ayudaVacio} />
        ) : (
          <>
            {leyenda && <div className="mb-3">{leyenda}</div>}
            <div className="grafico" style={{ height: alto }}>{children}</div>
            {pie && <div className="mt-4">{pie}</div>}
          </>
        )}
      </div>
    </Card>
  )
}

export interface ItemLeyenda {
  color: string
  texto: string
  // Línea punteada (series de línea) en vez de un cuadrado.
  punteada?: boolean
  linea?: boolean
}

export function Leyenda({ items }: { items: ItemLeyenda[] }) {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-xs font-medium text-muted">
      {items.map((item) => (
        <li key={item.texto} className="flex items-center gap-2">
          {item.linea || item.punteada ? (
            <svg width="18" height="8" aria-hidden>
              <line x1="1" y1="4" x2="17" y2="4" stroke={item.color} strokeWidth="2.5" strokeDasharray={item.punteada ? '4 3' : undefined} strokeLinecap="round" />
            </svg>
          ) : (
            <span className="h-2.5 w-2.5 rounded-[3px]" style={{ background: item.color }} aria-hidden />
          )}
          {item.texto}
        </li>
      ))}
    </ul>
  )
}

export interface FilaTooltip {
  color?: string
  texto: string
  valor: string
}

// Contenido del tooltip: superficie --surf con sombra, título y filas
// "nombre ..... valor" con cifras tabulares.
export function CajaTooltip({ titulo, filas, className }: { titulo: ReactNode; filas: FilaTooltip[]; className?: string }) {
  return (
    <div className={cx('min-w-[180px] rounded-chip bg-surf px-3.5 py-2.5 text-xs shadow-shh', className)}>
      <p className="mb-1.5 font-semibold text-ink">{titulo}</p>
      <ul className="space-y-1">
        {filas.map((fila) => (
          <li key={fila.texto} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-muted">
              {fila.color && <span className="h-2 w-2 rounded-full" style={{ background: fila.color }} aria-hidden />}
              {fila.texto}
            </span>
            <span className="font-semibold text-ink tabular-nums">{fila.valor}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
