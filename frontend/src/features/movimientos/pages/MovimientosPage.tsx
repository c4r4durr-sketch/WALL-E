import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeftRight } from 'lucide-react'
import { Card, Cargando, EmptyState, Field, PageHeader, ProductImage, Select, Skeleton, StatCard, clasesBoton } from '../../../components/ui'
import { getSession } from '../../auth/session'
import { useHerramientas } from '../../catalogo/hooks/useHerramientas'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { Rol } from '../../../shared/types/roles'
import { MovimientoForm } from '../components/MovimientoForm'
import { HistorialMovimientos } from '../components/HistorialMovimientos'
import { AjusteForm } from '../components/AjusteForm'
import { useStock } from '../hooks/useMovimientos'
import { desgloseCajas } from '../formato'
import { puedeAjustarStock } from '../permisos'
import type { Herramienta } from '../../catalogo/api/catalogoApi'

// Entradas y salidas de inventario (HU9) + historial y stock por
// herramienta (HU11). Todos los roles registran entradas/salidas; nadie
// edita ni borra un movimiento: un error se corrige con un ajuste, en una
// sección aparte visible solo para Administrador/Supervisor.

function StockPorSucursal({ herramienta }: { herramienta: Herramienta }) {
  const { data: stock, isLoading } = useStock(herramienta.id)
  if (isLoading) {
    return (
      <Cargando etiqueta="Cargando stock">
        <div className="grid grid-cols-2 gap-5">
          {[0, 1].map((i) => <Skeleton key={i} className="h-[124px] rounded-[26px]" />)}
        </div>
      </Cargando>
    )
  }
  return (
    <div className="grid grid-cols-2 gap-5">
      {stock?.map((s) => (
        <StatCard
          key={s.sucursal_id}
          etiqueta={`Stock en ${s.sucursal_nombre}`}
          valor={s.unidades}
          unidad="unidades"
          nota={herramienta.unidades_por_caja > 1 ? desgloseCajas(s.cajas_completas, s.unidades_sueltas) : undefined}
        />
      ))}
    </div>
  )
}

export function MovimientosPage() {
  const session = getSession()
  const { data: herramientas, isLoading } = useHerramientas()
  const { data: sucursales } = useSucursales()
  const [herramientaId, setHerramientaId] = useState<number | null>(null)

  const herramienta = herramientas?.find((h) => h.id === herramientaId) ?? null
  const sucursalFija = session?.rol === Rol.EMPLEADO ? session.sucursal_id : null
  const puedeAjustar = session ? puedeAjustarStock(session.rol) : false

  return (
    <>
      <PageHeader
        migas={['Inventario', 'Movimientos']}
        titulo="Movimientos"
        subtitulo="Entradas y salidas por herramienta, con su stock en cada sucursal."
      />

      <Card className="flex items-center gap-5">
        {herramienta ? (
          <ProductImage src={herramienta.imagen} alt={herramienta.nombre} tamano="mediana" />
        ) : (
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-chip bg-soft text-softink">
            <ArrowLeftRight size={26} aria-hidden />
          </div>
        )}
        <Field etiqueta="Herramienta" className="max-w-xl flex-1">
          {isLoading ? (
            <Skeleton className="h-10 w-full rounded-campo" />
          ) : (
            <Select
              value={herramientaId ?? ''}
              onChange={(event) => setHerramientaId(event.target.value ? Number(event.target.value) : null)}
            >
              <option value="">Selecciona una herramienta</option>
              {herramientas?.map((h) => (
                <option key={h.id} value={h.id}>{h.codigo} · {h.nombre}</option>
              ))}
            </Select>
          )}
        </Field>
      </Card>

      {herramientas?.length === 0 && (
        <Card sinPadding>
          <EmptyState
            icono={ArrowLeftRight}
            titulo="No hay herramientas en el catálogo"
            ayuda="Para registrar movimientos, primero carga una herramienta."
            accion={<Link to="/catalogo" className={clasesBoton()}>Ir al catálogo</Link>}
          />
        </Card>
      )}

      {herramientas && herramientas.length > 0 && !herramienta && (
        <Card sinPadding>
          <EmptyState icono={ArrowLeftRight} titulo="Elige una herramienta" ayuda="Verás su stock por sucursal, su historial y el formulario para registrar." />
        </Card>
      )}

      {herramienta && sucursales && (
        <div className="grid grid-cols-[400px_minmax(0,1fr)] items-start gap-5">
          <div className="space-y-5">
            {/* key: al cambiar de herramienta el formulario arranca limpio */}
            <MovimientoForm key={herramienta.id} herramienta={herramienta} sucursales={sucursales} sucursalFija={sucursalFija} />
            {puedeAjustar && <AjusteForm key={`ajuste-${herramienta.id}`} herramienta={herramienta} sucursales={sucursales} />}
          </div>
          <div className="space-y-5">
            <StockPorSucursal herramienta={herramienta} />
            <HistorialMovimientos herramienta={herramienta} sucursales={sucursales} />
          </div>
        </div>
      )}
    </>
  )
}
