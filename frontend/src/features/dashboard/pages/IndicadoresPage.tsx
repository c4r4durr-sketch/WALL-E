import { useSearchParams } from 'react-router-dom'
import { Gauge } from 'lucide-react'
import { Card, EmptyState, Field, PageHeader, ProductImage, Select, Skeleton } from '../../../components/ui'
import { useHerramientas } from '../../catalogo/hooks/useHerramientas'
import { DetalleEOQROP } from '../components/DetalleEOQROP'

// Indicadores de compra (HU17/HU18) de una herramienta: cuánto pedir (EOQ)
// y cuándo (ROP). La herramienta elegida va en la URL (?herramienta=id),
// así se llega directo desde la clasificación ABC.
export function IndicadoresPage() {
  const [params, setParams] = useSearchParams()
  const { data: herramientas, isLoading } = useHerramientas()
  const id = Number(params.get('herramienta')) || null
  const herramienta = herramientas?.find((h) => h.id === id) ?? null

  function elegir(valor: string) {
    setParams(valor ? { herramienta: valor } : {}, { replace: true })
  }

  return (
    <>
      <PageHeader
        migas={['Análisis', 'Indicadores']}
        titulo="Indicadores"
        subtitulo="Cuánto pedir (EOQ) y cuándo pedir (punto de reorden) de cada herramienta."
      />

      <Card className="flex items-center gap-5">
        {herramienta ? (
          <ProductImage key={herramienta.id} src={herramienta.imagen} alt={herramienta.nombre} tamano="mediana" />
        ) : (
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-chip bg-soft text-softink">
            <Gauge size={26} aria-hidden />
          </div>
        )}
        <Field etiqueta="Herramienta" className="max-w-xl flex-1">
          {isLoading ? (
            <Skeleton className="h-10 w-full rounded-campo" />
          ) : (
            <Select value={id ?? ''} onChange={(e) => elegir(e.target.value)}>
              <option value="">Selecciona una herramienta</option>
              {herramientas?.map((h) => (
                <option key={h.id} value={h.id}>{h.codigo} · {h.nombre}</option>
              ))}
            </Select>
          )}
        </Field>
      </Card>

      {id === null ? (
        <Card sinPadding>
          <EmptyState
            icono={Gauge}
            titulo="Elige una herramienta"
            ayuda="También puedes llegar desde la clasificación ABC o desde las alertas de reposición."
          />
        </Card>
      ) : (
        <DetalleEOQROP herramientaId={id} />
      )}
    </>
  )
}
