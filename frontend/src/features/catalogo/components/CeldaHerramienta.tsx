import { ProductImage } from '../../../components/ui'

// Miniatura + código + nombre: cómo se muestra una herramienta en una fila
// de cualquier tabla (panel, reposición, ABC, transferencias, cierre).
export function CeldaHerramienta({ codigo, nombre, imagen }: { codigo: string; nombre: string; imagen?: string | null }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <ProductImage src={imagen ?? null} alt={nombre} tamano="miniatura" />
      <div className="min-w-0">
        <p className="truncate font-semibold text-ink">{nombre}</p>
        <p className="truncate text-xs text-muted">{codigo}</p>
      </div>
    </div>
  )
}
