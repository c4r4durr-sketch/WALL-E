import type { ClasificacionABC } from '../api/indicadoresApi'

// Clasificación ABC (tabla, no gráfico: lo que se busca es qué herramienta
// está en qué clase). La clase se muestra con su letra, nunca solo con
// color. Clic en una fila = ver su EOQ y punto de reorden.

const CLASE: Record<ClasificacionABC['clase'], { clase: string; descripcion: string }> = {
  A: { clase: 'bg-slate-800 text-white', descripcion: 'Alta rotación: hasta el 80 % de lo vendido' },
  B: { clase: 'bg-slate-300 text-slate-900', descripcion: 'Rotación media: hasta el 95 %' },
  C: { clase: 'bg-slate-100 text-slate-600', descripcion: 'Baja rotación o sin ventas' },
}

interface Props {
  filas: ClasificacionABC[]
  seleccionada: number | null
  onSeleccionar: (herramientaId: number) => void
}

export function TablaABC({ filas, seleccionada, onSeleccionar }: Props) {
  const conteo = (c: ClasificacionABC['clase']) => filas.filter((f) => f.clase === c).length

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <h2 className="font-semibold text-slate-800">Clasificación ABC</h2>
        <p className="text-xs text-slate-500">
          Por unidades vendidas en los últimos 12 meses (solo salidas reales; ajustes y transferencias no cuentan).
        </p>
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
          {(['A', 'B', 'C'] as const).map((c) => (
            <span key={c} className="flex items-center gap-1.5">
              <span className={`inline-flex h-5 w-5 items-center justify-center rounded font-semibold ${CLASE[c].clase}`}>{c}</span>
              {conteo(c)} · {CLASE[c].descripcion}
            </span>
          ))}
        </div>
      </div>
      {filas.length === 0 ? (
        <p className="px-4 py-6 text-center text-sm text-slate-500">No hay herramientas en el catálogo.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2">Clase</th>
                <th className="px-4 py-2">Herramienta</th>
                <th className="px-4 py-2 text-right">Unidades vendidas</th>
                <th className="px-4 py-2 text-right">% del total</th>
                <th className="px-4 py-2 text-right">% acumulado</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <tr
                  key={f.herramienta_id}
                  onClick={() => onSeleccionar(f.herramienta_id)}
                  className={`cursor-pointer border-t border-slate-100 hover:bg-slate-50 ${seleccionada === f.herramienta_id ? 'bg-blue-50' : ''}`}
                >
                  <td className="px-4 py-2">
                    <span className={`inline-flex h-6 w-6 items-center justify-center rounded text-xs font-semibold ${CLASE[f.clase].clase}`}>
                      {f.clase}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <span className="font-medium text-slate-800">{f.codigo}</span>{' '}
                    <span className="text-slate-600">{f.nombre}</span>
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">{f.unidades_vendidas}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{f.porcentaje.toFixed(1)} %</td>
                  <td className="px-4 py-2 text-right tabular-nums">{f.porcentaje_acumulado.toFixed(1)} %</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
