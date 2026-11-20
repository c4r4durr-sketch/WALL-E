import { useState } from 'react'
import { Printer } from 'lucide-react'
import {
  Aviso,
  Button,
  Card,
  Cargando,
  Field,
  Input,
  PageHeader,
  SegmentedControl,
  Select,
  Skeleton,
  StatCard,
  type OpcionSegmento,
} from '../../../components/ui'
import { getSession } from '../../auth/session'
import { Rol } from '../../../shared/types/roles'
import { bs, fechaCorta, hoyEnLaPaz, miles, sumarDias } from '../../../shared/formato'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { ExportarExcel } from '../components/ExportarExcel'
import { GraficoAntiguedad } from '../components/graficos/GraficoAntiguedad'
import { GraficoMovimientos } from '../components/graficos/GraficoMovimientos'
import { GraficoPareto } from '../components/graficos/GraficoPareto'
import { GraficoStockSucursal } from '../components/graficos/GraficoStockSucursal'
import { GraficoTopHerramientas } from '../components/graficos/GraficoTopHerramientas'
import { GraficoTransferencias } from '../components/graficos/GraficoTransferencias'
import { mensajeDeError } from '../../../shared/api/errores'
import { reglas } from '../../../shared/validacion'
import { useEstadistica } from '../hooks/useEstadistica'
import type { FiltroEstadisticas } from '../api/estadisticasApi'

// Reportes estadísticos: KPI y seis gráficos del periodo y la sucursal
// elegidos, con los datos reales del sistema. Administrador: todas las
// sucursales o una; Supervisor: la suya (el backend responde 403 a otra).
// Se carga aparte (router.tsx), así Recharts no pesa en el resto.

type Atajo = '30d' | 'anio' | '12m' | 'otro'

const ATAJOS: OpcionSegmento<Atajo>[] = [
  { valor: '30d', texto: 'Últimos 30 días' },
  { valor: 'anio', texto: 'Este año' },
  { valor: '12m', texto: '12 meses' },
  { valor: 'otro', texto: 'Otro' },
]

// Mismo rango que el backend usa por defecto: 12 meses calendario
// incluido el actual.
function inicioDe12Meses(hoy: string): string {
  const [anio, mes] = hoy.split('-').map(Number)
  const indice = anio * 12 + mes - 1 - 11
  return `${Math.floor(indice / 12)}-${String((indice % 12) + 1).padStart(2, '0')}-01`
}

function rangoDe(atajo: Exclude<Atajo, 'otro'>, hoy: string): { desde: string; hasta: string } {
  if (atajo === '30d') return { desde: sumarDias(hoy, -29), hasta: hoy }
  if (atajo === 'anio') return { desde: `${hoy.slice(0, 4)}-01-01`, hasta: hoy }
  return { desde: inicioDe12Meses(hoy), hasta: hoy }
}

// Las mismas reglas de fechas que el resto del sistema (shared/validacion)
// y que el backend: obligatorias, sin fechas futuras y "hasta" no
// anterior a "desde". Con un error no se consulta.
function erroresDeRango(desde: string, hasta: string, hoy: string) {
  return {
    desde: reglas.obligatorio(desde, 'Elige una fecha.') ?? reglas.fechaNoFutura(desde, hoy),
    hasta: reglas.obligatorio(hasta, 'Elige una fecha.') ?? reglas.fechaNoFutura(hasta, hoy) ?? reglas.rangoFechas(desde, hasta),
  }
}

export function ReportesPage() {
  const session = getSession()
  const esAdmin = session?.rol === Rol.ADMINISTRADOR
  const hoy = hoyEnLaPaz()
  const { data: sucursales } = useSucursales()
  const [atajo, setAtajo] = useState<Atajo>('12m')
  const [rango, setRango] = useState(() => rangoDe('12m', hoy))
  const [sucursal, setSucursal] = useState('')

  const errores = erroresDeRango(rango.desde, rango.hasta, hoy)
  const valido = !errores.desde && !errores.hasta
  const filtro: FiltroEstadisticas = {
    ...rango,
    sucursal: esAdmin && sucursal !== '' ? Number(sucursal) : undefined,
  }

  const resumen = useEstadistica('resumen', filtro, valido)
  const movimientos = useEstadistica('movimientos-por-mes', filtro, valido)
  const top = useEstadistica('top-herramientas', filtro, valido)
  const stock = useEstadistica('stock-por-sucursal', filtro, valido)
  const abc = useEstadistica('abc', filtro, valido)
  const antiguedad = useEstadistica('antiguedad', filtro, valido)
  const transferencias = useEstadistica('transferencias', filtro, valido)

  function elegirAtajo(nuevo: Atajo) {
    setAtajo(nuevo)
    if (nuevo !== 'otro') setRango(rangoDe(nuevo, hoy))
  }

  function cambiarFecha(campo: 'desde' | 'hasta', valor: string) {
    setRango((anterior) => ({ ...anterior, [campo]: valor }))
    setAtajo('otro')
  }

  const nombreSucursal = esAdmin
    ? (sucursales?.find((s) => String(s.id) === sucursal)?.nombre ?? 'Todas las sucursales')
    : session?.sucursal_nombre
  const r = resumen.data

  return (
    <>
      <PageHeader
        migas={['Análisis', 'Reportes']}
        titulo="Reportes estadísticos"
        subtitulo="Movimientos, ventas, stock y transferencias del periodo elegido."
        acciones={
          <div className="flex items-start gap-2 print:hidden">
            <Button icono={<Printer size={16} aria-hidden />} onClick={() => window.print()} disabled={!valido}>
              Imprimir / PDF
            </Button>
            <ExportarExcel url="/indicadores/estadisticas/excel/" params={filtro} nombre="reportes" deshabilitado={!valido} />
          </div>
        }
      />

      <p className="hidden text-sm text-muted print:block">
        {nombreSucursal} · del {fechaCorta(rango.desde)} al {fechaCorta(rango.hasta)}
      </p>

      <Card className="flex flex-wrap items-start gap-5 print:hidden">
        <div>
          <p className="mb-1.5 text-xs font-semibold text-muted">Periodo</p>
          <SegmentedControl etiqueta="Atajos de periodo" opciones={ATAJOS} valor={atajo} onCambiar={elegirAtajo} />
        </div>
        <Field etiqueta="Desde" obligatorio error={errores.desde} className="w-44">
          <Input type="date" max={hoy} value={rango.desde} onChange={(e) => cambiarFecha('desde', e.target.value)} />
        </Field>
        <Field etiqueta="Hasta" obligatorio error={errores.hasta} className="w-44">
          <Input type="date" max={hoy} value={rango.hasta} onChange={(e) => cambiarFecha('hasta', e.target.value)} />
        </Field>
        {esAdmin ? (
          <Field etiqueta="Sucursal" className="w-56">
            <Select value={sucursal} onChange={(e) => setSucursal(e.target.value)}>
              <option value="">Todas las sucursales</option>
              {sucursales?.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </Select>
          </Field>
        ) : (
          <div>
            <p className="mb-1.5 text-xs font-semibold text-muted">Sucursal</p>
            <p className="flex h-10 items-center text-sm font-semibold text-ink">{session?.sucursal_nombre}</p>
          </div>
        )}
      </Card>

      {resumen.isError && !r ? (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => resumen.refetch()}>Reintentar</Button>}>
          {mensajeDeError(resumen.error, 'No se pudieron cargar los indicadores.')}
        </Aviso>
      ) : !r ? (
        <Cargando etiqueta="Cargando indicadores">
          <div className="grid grid-cols-5 gap-5">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="space-y-3 rounded-[26px] bg-surf p-6 shadow-sh">
                <Skeleton className="h-3 w-2/3" />
                <Skeleton className="h-8 w-1/2" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            ))}
          </div>
        </Cargando>
      ) : (
        <div className="grid grid-cols-5 gap-5 print:grid-cols-3">
          <StatCard className="imprimir-bloque" etiqueta="Movimientos" valor={miles(r.total_movimientos)} nota="Registrados en el periodo" />
          <StatCard className="imprimir-bloque" etiqueta="Unidades vendidas" valor={miles(r.unidades_vendidas)} nota="Salidas del periodo" />
          <StatCard className="imprimir-bloque" etiqueta="Valor del inventario" valor={bs(Number(r.valor_inventario))} nota={`Al costo, al ${fechaCorta(r.periodo.hasta)}`} />
          <StatCard
            className="imprimir-bloque"
            etiqueta="Alertas de reorden"
            valor={miles(r.alertas_reorden)}
            nota="Hoy, stock de todas las sucursales"
            alerta={r.alertas_reorden > 0}
          />
          <StatCard
            className="imprimir-bloque"
            etiqueta="Estancadas"
            valor={miles(r.herramientas_estancadas)}
            nota="Más de 40 días sin venta"
            alerta={r.herramientas_estancadas > 0}
          />
        </div>
      )}

      <div className="grid grid-cols-2 gap-5 print:grid-cols-1">
        <GraficoMovimientos
          meses={movimientos.data?.meses}
          cargando={movimientos.isLoading}
          error={movimientos.error}
          onReintentar={() => movimientos.refetch()}
        />
        <GraficoTopHerramientas
          herramientas={top.data?.herramientas}
          cargando={top.isLoading}
          error={top.error}
          onReintentar={() => top.refetch()}
        />
        <GraficoStockSucursal
          sucursales={stock.data?.sucursales}
          hasta={rango.hasta || hoy}
          cargando={stock.isLoading}
          error={stock.error}
          onReintentar={() => stock.refetch()}
        />
        <GraficoPareto
          pareto={abc.data?.pareto}
          clases={abc.data?.clases}
          sinCosto={abc.data?.herramientas_sin_costo ?? 0}
          cargando={abc.isLoading}
          error={abc.error}
          onReintentar={() => abc.refetch()}
        />
        <GraficoAntiguedad
          tramos={antiguedad.data?.tramos}
          hasta={rango.hasta || hoy}
          sinCosto={antiguedad.data?.lineas_sin_costo ?? 0}
          cargando={antiguedad.isLoading}
          error={antiguedad.error}
          onReintentar={() => antiguedad.refetch()}
        />
        <GraficoTransferencias
          porEstado={transferencias.data?.por_estado}
          total={transferencias.data?.total ?? 0}
          cargando={transferencias.isLoading}
          error={transferencias.error}
          onReintentar={() => transferencias.refetch()}
        />
      </div>
    </>
  )
}
