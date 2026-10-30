import { useState } from 'react'
import { BarChart3, ChevronRight } from 'lucide-react'
import { Card, CardHeader, EmptyState, SegmentedControl, Table, THead, Td, Th, Tr, cx } from '../../../components/ui'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import { useFotos } from '../../catalogo/hooks/useFotos'
import type { ClasificacionABC } from '../api/indicadoresApi'

// Clasificación ABC (tabla, no gráfico: lo que se busca es qué herramienta
// está en qué clase). La clase se muestra con su letra, nunca solo con
// color. Clic (o Enter) en una fila = ver su EOQ y punto de reorden.

type Clase = ClasificacionABC['clase']

const CLASE: Record<Clase, { clase: string; descripcion: string }> = {
  A: { clase: 'bg-acc text-on-acc', descripcion: 'Alta rotación: hasta el 80 % de lo vendido' },
  B: { clase: 'bg-soft text-softink', descripcion: 'Rotación media: hasta el 95 %' },
  C: { clase: 'bg-surf2 text-muted', descripcion: 'Baja rotación o sin ventas' },
}

function Letra({ clase, grande = false }: { clase: Clase; grande?: boolean }) {
  return (
    <span
      className={cx(
        'inline-flex items-center justify-center rounded-chip font-bold',
        grande ? 'h-7 w-7 text-sm' : 'h-6 w-6 text-xs',
        CLASE[clase].clase,
      )}
    >
      {clase}
    </span>
  )
}

interface Props {
  filas: ClasificacionABC[]
  onSeleccionar: (herramientaId: number) => void
}

export function TablaABC({ filas, onSeleccionar }: Props) {
  const foto = useFotos()
  const [filtro, setFiltro] = useState<Clase | 'todas'>('todas')
  const conteo = (c: Clase) => filas.filter((f) => f.clase === c).length
  const visibles = filtro === 'todas' ? filas : filas.filter((f) => f.clase === filtro)

  return (
    <>
      <div className="grid grid-cols-3 gap-5">
        {(['A', 'B', 'C'] as const).map((c) => (
          <Card key={c} interactiva className="flex items-center gap-4">
            <Letra clase={c} grande />
            <div>
              <p className="text-[28px] font-bold leading-none tracking-[-0.03em] text-ink tabular-nums">{conteo(c)}</p>
              <p className="mt-1.5 text-xs text-muted">{CLASE[c].descripcion}</p>
            </div>
          </Card>
        ))}
      </div>

      <Card sinPadding className="overflow-hidden">
        <CardHeader
          className="px-6 pb-4 pt-6"
          titulo="Herramientas por clase"
          descripcion="Por unidades vendidas en los últimos 12 meses (solo salidas reales; ajustes y transferencias no cuentan)."
          acciones={
            <SegmentedControl<Clase | 'todas'>
              etiqueta="Filtrar por clase"
              valor={filtro}
              onCambiar={setFiltro}
              opciones={[
                { valor: 'todas', texto: 'Todas' },
                { valor: 'A', texto: 'A' },
                { valor: 'B', texto: 'B' },
                { valor: 'C', texto: 'C' },
              ]}
            />
          }
        />
        {visibles.length === 0 ? (
          <EmptyState
            compacto
            icono={BarChart3}
            className="border-t border-line"
            titulo={filas.length === 0 ? 'No hay herramientas en el catálogo' : `Ninguna herramienta en la clase ${filtro}`}
            ayuda={filas.length === 0 ? 'La clasificación aparece cuando haya herramientas y ventas.' : 'Prueba con otra clase.'}
          />
        ) : (
          <Table>
            <THead>
              <tr>
                <Th>Clase</Th>
                <Th>Herramienta</Th>
                <Th numerico>Unidades vendidas</Th>
                <Th numerico>% del total</Th>
                <Th numerico>% acumulado</Th>
                <Th><span className="sr-only">Ver indicadores</span></Th>
              </tr>
            </THead>
            <tbody>
              {visibles.map((f) => (
                <Tr
                  key={f.herramienta_id}
                  interactiva
                  tabIndex={0}
                  aria-label={`${f.codigo} ${f.nombre}, clase ${f.clase}. Ver EOQ y punto de reorden`}
                  onClick={() => onSeleccionar(f.herramienta_id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      onSeleccionar(f.herramienta_id)
                    }
                  }}
                >
                  <Td><Letra clase={f.clase} /></Td>
                  <Td><CeldaHerramienta codigo={f.codigo} nombre={f.nombre} imagen={foto(f.herramienta_id)} /></Td>
                  <Td numerico className="font-semibold">{f.unidades_vendidas}</Td>
                  <Td numerico>{f.porcentaje.toFixed(1)} %</Td>
                  <Td numerico>{f.porcentaje_acumulado.toFixed(1)} %</Td>
                  <Td className="w-10 text-muted"><ChevronRight size={16} aria-hidden /></Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  )
}
