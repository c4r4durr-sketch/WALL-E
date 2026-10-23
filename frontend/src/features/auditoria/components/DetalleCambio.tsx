import type { DatosRegistro, RegistroHistorial } from '../api/auditoriaApi'

// Detalle de un registro del historial (HU13): en una edición, solo los
// campos que cambiaron (antes y después); en un alta, los datos nuevos; en
// una baja, los últimos datos que tenía. Los nombres de campo son los del
// sistema (los mismos de la API).

function valor(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—'
  if (typeof v === 'boolean') return v ? 'Sí' : 'No'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function campos(datos: DatosRegistro | null): string[] {
  return datos ? Object.keys(datos).sort() : []
}

export function DetalleCambio({ registro }: { registro: RegistroHistorial }) {
  const { accion, datos_anteriores: antes, datos_nuevos: despues } = registro
  const filas =
    accion === 'UPDATE' ? registro.campos_cambiados : accion === 'INSERT' ? campos(despues) : campos(antes)

  if (filas.length === 0) {
    return <p className="text-sm text-muted">Sin datos para mostrar.</p>
  }

  return (
    <table className="w-full text-left text-xs">
      <thead className="text-muted">
        <tr>
          <th className="w-56 py-2 pr-3 font-semibold">Campo</th>
          {accion !== 'INSERT' && <th className="py-2 pr-3 font-semibold">Antes</th>}
          {accion !== 'DELETE' && <th className="py-2 font-semibold">Después</th>}
        </tr>
      </thead>
      <tbody>
        {filas.map((campo) => (
          <tr key={campo} className="border-t border-line align-top">
            <td className="py-2 pr-3 font-mono text-muted">{campo}</td>
            {accion !== 'INSERT' && <td className="break-all py-2 pr-3 text-ink">{valor(antes?.[campo])}</td>}
            {accion !== 'DELETE' && <td className="break-all py-2 font-semibold text-ink">{valor(despues?.[campo])}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
