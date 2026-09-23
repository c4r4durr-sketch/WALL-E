// Tarjeta de indicador: etiqueta, número y una nota opcional. El número va
// siempre en texto neutro; si el indicador es una alerta activa, se marca
// con ícono + texto ("Requiere atención"), nunca solo con color.

interface Props {
  etiqueta: string
  valor: number
  nota?: string
  alerta?: boolean
}

export function StatTile({ etiqueta, valor, nota, alerta = false }: Props) {
  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${alerta ? 'border-amber-300' : 'border-slate-200'}`}>
      <p className="text-sm text-slate-500">{etiqueta}</p>
      <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">{valor.toLocaleString('es')}</p>
      {alerta ? (
        <p className="mt-1 flex items-center gap-1 text-xs font-medium text-amber-800">
          <svg aria-hidden="true" viewBox="0 0 20 20" className="h-3.5 w-3.5 fill-current">
            <path d="M10 2 1 18h18L10 2Zm-1 6h2v5H9V8Zm0 6h2v2H9v-2Z" />
          </svg>
          Requiere atención
        </p>
      ) : (
        nota && <p className="mt-1 text-xs text-slate-500">{nota}</p>
      )}
    </div>
  )
}
