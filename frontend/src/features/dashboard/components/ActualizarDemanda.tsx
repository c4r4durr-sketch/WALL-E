import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { Aviso, Button, Modal } from '../../../components/ui'
import { getSession } from '../../auth/session'
import { puedeEditarCatalogo } from '../../catalogo/permisos'
import { mensajeDeError } from '../../../shared/api/errores'
import { useActualizarDemanda } from '../hooks/useIndicadores'
import type { ResultadoEOQ } from '../api/indicadoresApi'

// HU21: si lo vendido en los últimos 12 meses no coincide con la demanda
// anual estimada, el Administrador o el Supervisor pueden pasarla al
// catálogo; el EOQ y el punto de reorden se recalculan con ella. Sin ventas
// no se ofrece (el backend responde 409).

const num = (v: number | null) => (v === null ? 'sin cargar' : `${v.toLocaleString('es')} unidades`)

export function ActualizarDemanda({ eoq }: { eoq: ResultadoEOQ }) {
  const session = getSession()
  const [abierto, setAbierto] = useState(false)
  const [actualizada, setActualizada] = useState(false)
  const mutacion = useActualizarDemanda()

  if (!session || !puedeEditarCatalogo(session.rol)) return null
  if (actualizada && eoq.demanda_anual === eoq.demanda_observada) {
    return <Aviso tono="exito" className="mt-4">La demanda anual ahora es lo vendido en los últimos 12 meses.</Aviso>
  }
  if (eoq.demanda_observada <= 0 || eoq.demanda_anual === eoq.demanda_observada) return null

  const cerrar = () => {
    setAbierto(false)
    mutacion.reset()
  }
  const confirmar = () =>
    mutacion.mutate(eoq.herramienta_id, {
      onSuccess: () => {
        setAbierto(false)
        setActualizada(true)
      },
    })

  return (
    <>
      <div className="mt-4 flex items-center justify-between gap-4 rounded-campo bg-surf2 px-4 py-3">
        <p className="text-[13px] text-muted">Lo vendido no coincide con la demanda estimada.</p>
        <Button tamano="sm" icono={<RefreshCw size={14} aria-hidden />} onClick={() => setAbierto(true)}>
          Usar lo vendido
        </Button>
      </div>
      <Modal
        abierto={abierto}
        onCerrar={cerrar}
        titulo="Actualizar la demanda anual"
        descripcion="Se guarda en el catálogo y queda en el historial de modificaciones."
        pie={
          <>
            <Button variante="ghost" onClick={cerrar}>Cancelar</Button>
            <Button onClick={confirmar} cargando={mutacion.isPending}>Actualizar</Button>
          </>
        }
      >
        <div className="space-y-4 text-sm">
          <dl className="divide-y divide-line">
            <div className="flex h-10 items-center justify-between">
              <dt className="text-muted">Demanda anual estimada</dt>
              <dd className="font-semibold text-ink tabular-nums">{num(eoq.demanda_anual)}</dd>
            </div>
            <div className="flex h-10 items-center justify-between">
              <dt className="text-muted">Vendido en los últimos 12 meses</dt>
              <dd className="font-semibold text-ink tabular-nums">{num(eoq.demanda_observada)}</dd>
            </div>
          </dl>
          <p className="text-muted">
            El EOQ y el punto de reorden se recalculan con lo vendido. Si la herramienta tiene menos de un año de
            ventas, la cifra puede quedar por debajo de la demanda real.
          </p>
          {mutacion.isError && <Aviso tono="error">{mensajeDeError(mutacion.error, 'No se pudo actualizar la demanda.')}</Aviso>}
        </div>
      </Modal>
    </>
  )
}
