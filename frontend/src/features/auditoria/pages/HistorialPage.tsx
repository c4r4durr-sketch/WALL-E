import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, FilterX } from 'lucide-react'
import { mensajeDeError } from '../../../shared/api/errores'
import { fechaHora, hoyEnLaPaz } from '../../../shared/formato'
import { DetalleCambio } from '../components/DetalleCambio'
import { useHistorial, useOpcionesHistorial } from '../hooks/useHistorial'
import type { AccionAuditoria, FiltroHistorial, RegistroHistorial } from '../api/auditoriaApi'

// Historial de modificaciones (HU13), solo lectura: quién dio de alta,
// editó o dio de baja cada registro, y cuándo (hora de La Paz). Lo ven el
// Administrador y el Supervisor; la ruta tiene RequireRol y el backend
// responde 403 al Empleado.

const ACCION: Record<AccionAuditoria, { texto: string; clase: string }> = {
  INSERT: { texto: 'Alta', clase: 'bg-green-50 text-green-700' },
  UPDATE: { texto: 'Edición', clase: 'bg-blue-50 text-blue-700' },
  DELETE: { texto: 'Baja', clase: 'bg-red-50 text-red-700' },
}

const FILTRO_VACIO: FiltroHistorial = { desde: '', hasta: '', usuario: '', tabla: '', accion: '', pagina: 1 }

function resumen(r: RegistroHistorial): string {
  if (r.accion === 'INSERT') return 'Alta del registro'
  if (r.accion === 'DELETE') return 'Baja del registro'
  return r.campos_cambiados.length > 0 ? r.campos_cambiados.join(', ') : 'Sin cambios visibles'
}

const COLUMNAS = 7

export function HistorialPage() {
  const hoy = hoyEnLaPaz()
  const [filtro, setFiltro] = useState<FiltroHistorial>(FILTRO_VACIO)
  const [abiertoId, setAbiertoId] = useState<number | null>(null)
  const { data: opciones } = useOpcionesHistorial()

  const rangoInvalido = Boolean(filtro.desde && filtro.hasta && filtro.desde > filtro.hasta)
  const { data: pagina, isLoading, isError, error, isFetching, refetch } = useHistorial(filtro, !rangoInvalido)

  // Cambiar un filtro vuelve a la primera página.
  function cambiar(campo: Exclude<keyof FiltroHistorial, 'pagina'>, valor: string) {
    setFiltro((prev) => ({ ...prev, [campo]: valor, pagina: 1 }))
    setAbiertoId(null)
  }

  function irA(numero: number) {
    setFiltro((prev) => ({ ...prev, pagina: numero }))
    setAbiertoId(null)
  }

  const hayFiltros = Object.entries(filtro).some(([campo, v]) => campo !== 'pagina' && v)
  const selectClass = 'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm'

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:underline">
            <ArrowLeft size={14} aria-hidden />
            Volver
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Historial de modificaciones</h1>
          <p className="mt-1 text-sm text-slate-500">
            Registro automático de altas, ediciones y bajas, con su autor. Solo lectura.
          </p>
        </div>

        <div className="grid grid-cols-6 items-end gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div>
            <label htmlFor="desde" className="mb-1 block text-sm font-medium text-slate-700">Desde</label>
            <input id="desde" type="date" max={hoy} value={filtro.desde} onChange={(e) => cambiar('desde', e.target.value)} className={selectClass} />
          </div>
          <div>
            <label htmlFor="hasta" className="mb-1 block text-sm font-medium text-slate-700">Hasta</label>
            <input id="hasta" type="date" max={hoy} value={filtro.hasta} onChange={(e) => cambiar('hasta', e.target.value)} className={selectClass} />
          </div>
          <div>
            <label htmlFor="usuario" className="mb-1 block text-sm font-medium text-slate-700">Usuario</label>
            <select id="usuario" value={filtro.usuario} onChange={(e) => cambiar('usuario', e.target.value)} className={selectClass}>
              <option value="">Todos</option>
              {opciones?.usuarios.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="tabla" className="mb-1 block text-sm font-medium text-slate-700">Tabla</label>
            <select id="tabla" value={filtro.tabla} onChange={(e) => cambiar('tabla', e.target.value)} className={selectClass}>
              <option value="">Todas</option>
              {opciones?.tablas.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="accion" className="mb-1 block text-sm font-medium text-slate-700">Acción</label>
            <select id="accion" value={filtro.accion} onChange={(e) => cambiar('accion', e.target.value)} className={selectClass}>
              <option value="">Todas</option>
              {opciones?.acciones.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
            </select>
          </div>
          <div>
            <button
              type="button"
              onClick={() => {
                setFiltro(FILTRO_VACIO)
                setAbiertoId(null)
              }}
              disabled={!hayFiltros}
              className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            >
              <FilterX size={16} aria-hidden />
              Limpiar filtros
            </button>
          </div>
          {rangoInvalido && (
            <p className="col-span-6 text-xs text-red-600">La fecha "desde" no puede ser posterior a "hasta".</p>
          )}
        </div>

        {isError && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mensajeDeError(error, 'No se pudo cargar el historial.')}{' '}
            <button type="button" onClick={() => refetch()} className="font-medium underline">Reintentar</button>
          </p>
        )}

        <div className={`overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm ${isFetching ? 'opacity-70' : ''}`}>
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="px-3 py-2">Fecha</th>
                <th className="px-3 py-2">Usuario</th>
                <th className="px-3 py-2">Tabla</th>
                <th className="px-3 py-2 text-right">Registro</th>
                <th className="px-3 py-2">Acción</th>
                <th className="px-3 py-2">Cambios</th>
                <th className="px-3 py-2" aria-label="Detalle" />
              </tr>
            </thead>
            <tbody>
              {isLoading && !rangoInvalido && (
                <tr><td colSpan={COLUMNAS} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>
              )}
              {pagina?.total === 0 && (
                <tr>
                  <td colSpan={COLUMNAS} className="px-3 py-4 text-center text-slate-500">
                    {hayFiltros ? 'Ningún registro coincide con los filtros.' : 'Todavía no hay modificaciones registradas.'}
                  </td>
                </tr>
              )}
              {pagina?.resultados.map((r) => {
                const abierto = abiertoId === r.id
                return (
                  <Fragment key={r.id}>
                    <tr className={`border-t border-slate-100 ${abierto ? 'bg-slate-50' : ''}`}>
                      <td className="whitespace-nowrap px-3 py-2 tabular-nums">{fechaHora(r.fecha)}</td>
                      <td className="px-3 py-2">{r.usuario || <span className="text-slate-400">Sistema</span>}</td>
                      <td className="px-3 py-2">{r.tabla_nombre}</td>
                      <td className="px-3 py-2 text-right tabular-nums">#{r.registro_id}</td>
                      <td className="px-3 py-2">
                        <span className={`rounded px-2 py-0.5 text-xs font-medium ${ACCION[r.accion].clase}`}>
                          {ACCION[r.accion].texto}
                        </span>
                      </td>
                      <td className="max-w-xs truncate px-3 py-2 text-slate-600" title={resumen(r)}>{resumen(r)}</td>
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          onClick={() => setAbiertoId(abierto ? null : r.id)}
                          aria-expanded={abierto}
                          aria-label={abierto ? 'Ocultar detalle' : 'Ver detalle'}
                          title={abierto ? 'Ocultar detalle' : 'Ver detalle'}
                          className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100"
                        >
                          {abierto ? <ChevronUp size={16} aria-hidden /> : <ChevronDown size={16} aria-hidden />}
                        </button>
                      </td>
                    </tr>
                    {abierto && (
                      <tr className="bg-slate-50">
                        <td colSpan={COLUMNAS} className="px-6 pb-4 pt-1">
                          <DetalleCambio registro={r} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>

        {pagina && pagina.total > 0 && (
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>
              Página {pagina.pagina} de {pagina.paginas} · {pagina.total.toLocaleString('es')}{' '}
              {pagina.total === 1 ? 'registro' : 'registros'}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => irA(pagina.pagina - 1)}
                disabled={pagina.pagina <= 1 || isFetching}
                className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium hover:bg-slate-100 disabled:opacity-50"
              >
                <ChevronLeft size={16} aria-hidden />
                Anterior
              </button>
              <button
                type="button"
                onClick={() => irA(pagina.pagina + 1)}
                disabled={pagina.pagina >= pagina.paginas || isFetching}
                className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium hover:bg-slate-100 disabled:opacity-50"
              >
                Siguiente
                <ChevronRight size={16} aria-hidden />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
