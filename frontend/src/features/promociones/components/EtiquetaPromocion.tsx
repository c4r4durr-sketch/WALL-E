import { Tag } from 'lucide-react'
import { Badge } from '../../../components/ui'

// HU23: la etiqueta que se ve en las listas (catálogo, panel, antigüedad).
// El descuento es opcional: sin él, la etiqueta dice solo "Promoción".
// `sucursal` se agrega donde la lista no es de una sola sucursal.

export function EtiquetaPromocion({ descuento, sucursal }: { descuento: number | null; sucursal?: string }) {
  const texto = descuento === null ? 'Promoción' : `−${descuento} %`
  return (
    <Badge tono="acc" icono={<Tag size={12} aria-hidden />}>
      {sucursal ? `${sucursal} · ${texto}` : texto}
    </Badge>
  )
}
