import { Fragment, useState } from 'react'
import { ChevronDown, ChevronLeft, ChevronRight, FilterX, SearchX, ShieldCheck } from 'lucide-react'
import {
  Aviso,
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  IconButton,
  Input,
  PageHeader,
  Select,
  SkeletonFilas,
  Table,
  THead,
  Td,
  Th,
  Tr,
  cx,
  type TonoBadge,
} from '../../../components/ui'
import { mensajeDeError } from '../../../shared/api/errores'
import { fechaHora, hoyEnLaPaz } from '../../../shared/formato'
import { DetalleCambio } from '../components/DetalleCambio'
import { useHistorial, useOpcionesHistorial } from '../hooks/useHistorial'
import type { AccionAuditoria, FiltroHistorial, RegistroHistorial } from '../api/auditoriaApi'

// Historial de modificaciones (HU13), solo lectura: quién dio de alta,
// editó o dio de baja cada registro, y cuándo (hora de La Paz). Lo ven el
// Administrador y el Supervisor; la ruta tiene RequireRol y el backend
// responde 403 al Empleado.

const ACCION: Record<AccionAuditoria, { texto: string; tono: TonoBadge }> = {
  INSERT: { texto: 'Alta', tono: 'ok' },
  UPDATE: { texto: 'Edición', tono: 'acc' },
  DELETE: { texto: 'Baja', tono: 'danger' },
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

  function limpiar() {
    setFiltro(FILTRO_VACIO)
    setAbiertoId(null)
  }

  const hayFiltros = Object.entries(filtro).some(([campo, v]) => campo !== 'pagina' && v)

  return (
    <>
      <PageHeader
        migas={['Administración', 'Auditoría']}
        titulo="Auditoría"
        subtitulo="Registro automático de altas, ediciones y bajas, con su autor. Solo lectura."
      />

      <Card className="grid grid-cols-[repeat(5,minmax(0,1fr))_auto] items-start gap-4">
        <Field etiqueta="Desde" error={rangoInvalido ? 'No puede ser posterior a "hasta".' : null}>
          <Input type="date" max={hoy} value={filtro.desde} onChange={(e) => cambiar('desde', e.target.value)} />
        </Field>
        <Field etiqueta="Hasta">
          <Input type="date" max={hoy} value={filtro.hasta} onChange={(e) => cambiar('hasta', e.target.value)} />
        </Field>
        <Field etiqueta="Usuario">
          <Select value={filtro.usuario} onChange={(e) => cambiar('usuario', e.target.value)}>
            <option value="">Todos</option>
            {opciones?.usuarios.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
          </Select>
        </Field>
        <Field etiqueta="Tabla">
          <Select value={filtro.tabla} onChange={(e) => cambiar('tabla', e.target.value)}>
            <option value="">Todas</option>
            {opciones?.tablas.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
          </Select>
        </Field>
        <Field etiqueta="Acción">
          <Select value={filtro.accion} onChange={(e) => cambiar('accion', e.target.value)}>
            <option value="">Todas</option>
            {opciones?.acciones.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
          </Select>
        </Field>
        <Button variante="ghost" className="mt-[22px]" onClick={limpiar} disabled={!hayFiltros} icono={<FilterX size={16} aria-hidden />}>
          Limpiar
        </Button>
      </Card>

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          {mensajeDeError(error, 'No se pudo cargar el historial.')}
        </Aviso>
      )}

      <Card sinPadding className={cx('transicion overflow-hidden', isFetching && !isLoading && 'opacity-70')}>
        {isLoading && !rangoInvalido && <SkeletonFilas filas={8} columnas={6} />}
        {pagina?.total === 0 &&
          (hayFiltros ? (
            <EmptyState
              icono={SearchX}
              titulo="Sin resultados"
              ayuda="Ningún registro coincide con los filtros."
              accion={<Button onClick={limpiar}>Limpiar filtros</Button>}
            />
          ) : (
            <EmptyState icono={ShieldCheck} titulo="Todavía no hay modificaciones" ayuda="Cada alta, edición o baja aparecerá acá con su autor." />
          ))}
        {pagina && pagina.total > 0 && (
          <Table>
            <THead>
              <tr>
                <Th>Fecha</Th>
                <Th>Usuario</Th>
                <Th>Tabla</Th>
                <Th numerico>Registro</Th>
                <Th>Acción</Th>
                <Th>Cambios</Th>
                <Th><span className="sr-only">Detalle</span></Th>
              </tr>
            </THead>
            <tbody>
              {pagina.resultados.map((r) => {
                const abierto = abiertoId === r.id
                return (
                  <Fragment key={r.id}>
                    <Tr seleccionada={abierto}>
                      <Td className="whitespace-nowrap tabular-nums">{fechaHora(r.fecha)}</Td>
                      <Td>{r.usuario || <span className="text-muted">Sistema</span>}</Td>
                      <Td>{r.tabla_nombre}</Td>
                      <Td numerico>#{r.registro_id}</Td>
                      <Td><Badge tono={ACCION[r.accion].tono}>{ACCION[r.accion].texto}</Badge></Td>
                      <Td className="max-w-xs truncate text-muted" title={resumen(r)}>{resumen(r)}</Td>
                      <Td className="w-12">
                        <IconButton
                          etiqueta={abierto ? 'Ocultar detalle' : 'Ver detalle'}
                          aria-expanded={abierto}
                          onClick={() => setAbiertoId(abierto ? null : r.id)}
                        >
                          <ChevronDown size={17} aria-hidden className={cx('transicion', abierto && 'rotate-180')} />
                        </IconButton>
                      </Td>
                    </Tr>
                    {abierto && (
                      <tr className="bg-surf2">
                        <td colSpan={COLUMNAS} className="px-6 pb-4 pt-2">
                          <DetalleCambio registro={r} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </Table>
        )}
      </Card>

      {pagina && pagina.total > 0 && (
        <div className="flex items-center justify-between text-[13px] font-medium text-muted">
          <span className="tabular-nums">
            Página {pagina.pagina} de {pagina.paginas} · {pagina.total.toLocaleString('es')}{' '}
            {pagina.total === 1 ? 'registro' : 'registros'}
          </span>
          <div className="flex gap-2">
            <Button tamano="sm" icono={<ChevronLeft size={16} aria-hidden />} disabled={pagina.pagina <= 1 || isFetching} onClick={() => irA(pagina.pagina - 1)}>
              Anterior
            </Button>
            <Button tamano="sm" disabled={pagina.pagina >= pagina.paginas || isFetching} onClick={() => irA(pagina.pagina + 1)}>
              Siguiente
              <ChevronRight size={16} aria-hidden />
            </Button>
          </div>
        </div>
      )}
    </>
  )
}
