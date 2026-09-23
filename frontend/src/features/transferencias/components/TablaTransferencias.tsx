import { useState } from 'react'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import { cajas } from '../../movimientos/formato'
import { erroresDelBackend } from '../../movimientos/errores'
import type { EstadoTransferencia, Transferencia } from '../api/transferenciasApi'
import { useCompletarTransferencia, useRechazarTransferencia, useTransferencias } from '../hooks/useTransferencias'

// Listado de transferencias (pendientes o todas). Administrador/Supervisor
// resuelven las pendientes desde la misma fila: completar (mueve el stock)
// o rechazar (con motivo). Los errores del backend (ej. 409: ya no hay
// stock en origen) se muestran en la fila afectada.

const fechaHora = new Intl.DateTimeFormat('es', { dateStyle: 'short', timeStyle: 'short' })

const ESTADO: Record<EstadoTransferencia, { texto: string; clase: string }> = {
  PENDIENTE: { texto: 'Pendiente', clase: 'bg-amber-100 text-amber-800' },
  COMPLETADA: { texto: 'Completada', clase: 'bg-green-50 text-green-700' },
  RECHAZADA: { texto: 'Rechazada', clase: 'bg-slate-100 text-slate-600' },
}

interface Props {
  herramientas: Herramienta[]
  sucursales: Sucursal[]
  puedeResolver: boolean
}

function mensajeError(error: unknown): string | null {
  if (!error) return null
  const e = erroresDelBackend(error)
  return e.detail ?? e.motivo ?? 'No se pudo resolver la transferencia.'
}

function FilaAcciones({ t }: { t: Transferencia }) {
  const completar = useCompletarTransferencia()
  const rechazar = useRechazarTransferencia()
  const [rechazando, setRechazando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const ocupado = completar.isPending || rechazar.isPending
  const error = mensajeError(completar.error) ?? mensajeError(rechazar.error)

  return (
    <div className="space-y-1">
      {rechazando ? (
        <div className="flex flex-wrap items-center gap-2">
          <input
            aria-label="Motivo del rechazo"
            value={motivo}
            maxLength={255}
            placeholder="Motivo del rechazo"
            onChange={(e) => { setMotivo(e.target.value); rechazar.reset() }}
            className="min-w-40 flex-1 rounded-md border border-slate-300 px-2 py-1 text-xs"
          />
          <button type="button" disabled={ocupado || !motivo.trim()}
            onClick={() => rechazar.mutate({ id: t.id, motivo: motivo.trim() })}
            className="text-xs font-medium text-red-700 hover:underline disabled:opacity-50">
            Confirmar rechazo
          </button>
          <button type="button" onClick={() => { setRechazando(false); rechazar.reset() }}
            className="text-xs font-medium text-slate-600 hover:underline">
            Cancelar
          </button>
        </div>
      ) : (
        <div className="flex gap-3">
          <button type="button" disabled={ocupado} onClick={() => completar.mutate(t.id)}
            className="text-xs font-medium text-green-700 hover:underline disabled:opacity-50">
            {completar.isPending ? 'Completando...' : 'Completar'}
          </button>
          <button type="button" disabled={ocupado} onClick={() => { setRechazando(true); completar.reset() }}
            className="text-xs font-medium text-red-700 hover:underline disabled:opacity-50">
            Rechazar
          </button>
        </div>
      )}
      {error && <p role="alert" className="max-w-xs text-xs text-red-600">{error}</p>}
    </div>
  )
}

export function TablaTransferencias({ herramientas, sucursales, puedeResolver }: Props) {
  const [filtro, setFiltro] = useState<'PENDIENTE' | 'TODAS'>('PENDIENTE')
  const { data: transferencias, isLoading, isError } = useTransferencias(filtro === 'TODAS' ? undefined : filtro)
  const herramienta = (id: number) => herramientas.find((h) => h.id === id)
  const sucursal = (id: number) => sucursales.find((s) => s.id === id)?.nombre ?? `#${id}`
  const pestaña = (activa: boolean) =>
    `rounded-md px-3 py-1.5 text-sm font-medium ${activa ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-800">Transferencias</h2>
        <div className="flex gap-1" role="tablist" aria-label="Filtro de transferencias">
          <button role="tab" aria-selected={filtro === 'PENDIENTE'} className={pestaña(filtro === 'PENDIENTE')} onClick={() => setFiltro('PENDIENTE')}>
            Pendientes
          </button>
          <button role="tab" aria-selected={filtro === 'TODAS'} className={pestaña(filtro === 'TODAS')} onClick={() => setFiltro('TODAS')}>
            Todas
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2">Herramienta</th>
              <th className="px-3 py-2">Desde → hacia</th>
              <th className="px-3 py-2 text-right">Cantidad</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2">Solicitó / resolvió</th>
              {puedeResolver && <th className="px-3 py-2">Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={7} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>}
            {isError && <tr><td colSpan={7} className="px-3 py-4 text-center text-red-600">No se pudieron cargar las transferencias.</td></tr>}
            {transferencias?.length === 0 && (
              <tr><td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                {filtro === 'PENDIENTE' ? 'No hay transferencias pendientes.' : 'Todavía no hay transferencias.'}
              </td></tr>
            )}
            {transferencias?.map((t) => {
              const h = herramienta(t.herramienta)
              return (
                <tr key={t.id} className="border-t border-slate-100 align-top">
                  <td className="whitespace-nowrap px-3 py-2">{fechaHora.format(new Date(t.creado_en))}</td>
                  <td className="px-3 py-2">
                    <span className="font-medium text-slate-800">{h?.codigo ?? `#${t.herramienta}`}</span>{' '}
                    <span className="text-slate-600">{h?.nombre}</span>
                  </td>
                  <td className="px-3 py-2">{sucursal(t.sucursal_origen)} → {sucursal(t.sucursal_destino)}</td>
                  <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums">
                    {t.tipo_unidad === 'CAJA' ? `${cajas(t.cantidad)} (${t.cantidad_unidades} u.)` : `${t.cantidad} u.`}
                  </td>
                  <td className="px-3 py-2">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${ESTADO[t.estado].clase}`}>{ESTADO[t.estado].texto}</span>
                    {t.motivo_rechazo && <p className="mt-1 max-w-xs text-xs italic text-slate-500">{t.motivo_rechazo}</p>}
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    {t.usuario_username}
                    {t.resuelto_por_username && <span className="block">→ {t.resuelto_por_username}</span>}
                  </td>
                  {puedeResolver && (
                    <td className="px-3 py-2">{t.estado === 'PENDIENTE' ? <FilaAcciones t={t} /> : null}</td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
