import { useState } from 'react'
import { Package } from 'lucide-react'
import { cx } from './cx'

// Foto de producto (docs/DISENO.md): contenedor 1:1, object-fit cover y
// degradado --surf2 -> --bg de fondo. Sin foto (herramientas cargadas
// antes de que fuera obligatoria) o si la imagen no carga: ilustración
// neutra con el ícono `package` y "Sin foto".

interface Props {
  src: string | null
  alt: string
  // 'tarjeta' (cuadrícula, radio 20), 'mediana' (64 px, encabezados) o
  // 'miniatura' (filas de tabla, 44 px).
  tamano?: 'tarjeta' | 'mediana' | 'miniatura'
  className?: string
}

const TAMANO = {
  tarjeta: 'w-full rounded-card',
  mediana: 'h-16 w-16 rounded-chip',
  miniatura: 'h-11 w-11 rounded-chip',
}

export function ProductImage({ src, alt, tamano = 'tarjeta', className }: Props) {
  // Se guarda QUÉ URL falló: si cambia la foto, se vuelve a intentar.
  const [fallida, setFallida] = useState<string | null>(null)
  const miniatura = tamano !== 'tarjeta'
  const conFoto = src && src !== fallida

  return (
    <div
      className={cx(
        'relative aspect-square shrink-0 overflow-hidden bg-gradient-to-b from-surf2 to-canvas',
        TAMANO[tamano],
        className,
      )}
    >
      {conFoto ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          decoding="async"
          onError={() => setFallida(src)}
          className="h-full w-full object-cover"
        />
      ) : (
        <div role="img" aria-label={`${alt}: sin foto`} className="flex h-full w-full flex-col items-center justify-center gap-1.5 text-muted">
          <Package size={miniatura ? 18 : 40} aria-hidden />
          {!miniatura && <span className="text-xs font-semibold">Sin foto</span>}
        </div>
      )}
    </div>
  )
}
