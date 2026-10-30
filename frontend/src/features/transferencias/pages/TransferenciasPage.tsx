import { Card, PageHeader, Skeleton, SkeletonFilas, Cargando } from '../../../components/ui'
import { getSession } from '../../auth/session'
import { useHerramientas } from '../../catalogo/hooks/useHerramientas'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { Rol } from '../../../shared/types/roles'
import { SolicitudForm } from '../components/SolicitudForm'
import { TablaTransferencias } from '../components/TablaTransferencias'
import { puedeResolverTransferencias } from '../permisos'

// Transferencias entre sucursales (HU12): cualquiera solicita (el Empleado
// solo desde su sucursal); Administrador/Supervisor completan o rechazan.
export function TransferenciasPage() {
  const session = getSession()
  const { data: herramientas } = useHerramientas()
  const { data: sucursales } = useSucursales()
  const origenFijo = session?.rol === Rol.EMPLEADO ? session.sucursal_id : null
  const puedeResolver = session ? puedeResolverTransferencias(session.rol) : false

  return (
    <>
      <PageHeader
        migas={['Inventario', 'Transferencias']}
        titulo="Transferencias"
        subtitulo="Mover stock entre sucursales: se solicita y luego se completa o se rechaza."
      />
      {herramientas && sucursales ? (
        <div className="grid grid-cols-[400px_minmax(0,1fr)] items-start gap-5">
          <SolicitudForm herramientas={herramientas} sucursales={sucursales} origenFijo={origenFijo} />
          <TablaTransferencias herramientas={herramientas} sucursales={sucursales} puedeResolver={puedeResolver} />
        </div>
      ) : (
        <div className="grid grid-cols-[400px_minmax(0,1fr)] items-start gap-5">
          <Cargando>
            <div className="space-y-4 rounded-[26px] bg-surf p-6 shadow-sh">
              <Skeleton className="h-4 w-1/2" />
              {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full rounded-campo" />)}
            </div>
          </Cargando>
          <Card sinPadding>
            <SkeletonFilas filas={4} columnas={5} />
          </Card>
        </div>
      )}
    </>
  )
}
