import { cx } from './cx'

// Carga: bloques --surf2 con pulso suave (docs/DISENO.md prohíbe el texto
// "Cargando..."). El contenedor anuncia la carga al lector de pantalla.

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cx('esqueleto', className)} />
}

export function Cargando({ children, etiqueta = 'Cargando contenido' }: { children: React.ReactNode; etiqueta?: string }) {
  return (
    <div role="status" aria-live="polite" aria-label={etiqueta}>
      {children}
    </div>
  )
}

// Filas de una tabla mientras carga (dentro de una Card sin padding).
export function SkeletonFilas({ filas = 5, columnas = 4 }: { filas?: number; columnas?: number }) {
  return (
    <Cargando>
      <div className="divide-y divide-line">
        {Array.from({ length: filas }, (_, i) => (
          <div key={i} className="flex h-14 items-center gap-6 px-6">
            {Array.from({ length: columnas }, (_, j) => (
              <Skeleton key={j} className={cx('h-3.5', j === 0 ? 'w-1/4' : 'flex-1')} />
            ))}
          </div>
        ))}
      </div>
    </Cargando>
  )
}

// Tarjetas con foto mientras carga (cuadrícula del catálogo).
export function SkeletonTarjetas({ cantidad = 8 }: { cantidad?: number }) {
  return (
    <Cargando>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-5">
        {Array.from({ length: cantidad }, (_, i) => (
          <div key={i} className="rounded-[26px] bg-surf p-3 shadow-sh">
            <Skeleton className="aspect-square w-full rounded-card" />
            <div className="space-y-2 px-2 pb-2 pt-4">
              <Skeleton className="h-3 w-1/3" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    </Cargando>
  )
}

// Números grandes (tarjetas de indicadores) mientras cargan.
export function SkeletonIndicadores({ cantidad = 4 }: { cantidad?: number }) {
  return (
    <Cargando>
      <div className="grid grid-cols-4 gap-5">
        {Array.from({ length: cantidad }, (_, i) => (
          <div key={i} className="space-y-3 rounded-[26px] bg-surf p-6 shadow-sh">
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-8 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        ))}
      </div>
    </Cargando>
  )
}
