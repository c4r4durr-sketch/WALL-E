import { Link } from 'react-router-dom'
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
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link to="/" className="text-sm text-slate-500 hover:underline">← Volver</Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Transferencias entre sucursales</h1>
        </div>
        {herramientas && sucursales && (
          <>
            <SolicitudForm herramientas={herramientas} sucursales={sucursales} origenFijo={origenFijo} />
            <TablaTransferencias herramientas={herramientas} sucursales={sucursales} puedeResolver={puedeResolver} />
          </>
        )}
      </div>
    </div>
  )
}
