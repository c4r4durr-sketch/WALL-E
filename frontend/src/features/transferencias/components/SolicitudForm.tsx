import { useState, type FormEvent } from 'react'
import { Send } from 'lucide-react'
import { Aviso, Button, Card, CardHeader, Field, Input, SegmentedControl, Select } from '../../../components/ui'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoUnidad } from '../../movimientos/api/movimientosApi'
import { useStock } from '../../movimientos/hooks/useMovimientos'
import { desgloseCajas } from '../../movimientos/formato'
import { erroresDelBackend } from '../../movimientos/errores'
import { useSolicitarTransferencia } from '../hooks/useTransferencias'

// Solicitud de transferencia (HU12). Queda PENDIENTE: el stock no se mueve
// hasta que un Administrador/Supervisor la completa. Muestra el stock en
// origen para no pedir más de lo que hay (el backend igual lo valida).

interface Props {
  herramientas: Herramienta[]
  sucursales: Sucursal[]
  // Empleado: el origen es siempre su sucursal.
  origenFijo: number | null
}

export function SolicitudForm({ herramientas, sucursales, origenFijo }: Props) {
  const [herramientaId, setHerramientaId] = useState('')
  const [origen, setOrigen] = useState(origenFijo ? String(origenFijo) : '')
  const [destino, setDestino] = useState('')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const [cantidad, setCantidad] = useState('')
  const herramienta = herramientas.find((h) => String(h.id) === herramientaId)
  const { data: stock } = useStock(herramienta?.id ?? null)
  const { mutate, isPending, error, isSuccess, reset } = useSolicitarTransferencia()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidades = herramienta && unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockOrigen = stock?.find((s) => String(s.sucursal_id) === origen)
  const listo = herramienta && origen && destino && origen !== destino && cantidadNumero >= 1

  function cambiar<T>(setter: (v: T) => void) {
    return (valor: T) => {
      setter(valor)
      if (error || isSuccess) reset()
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate(
      {
        herramienta: Number(herramientaId),
        sucursal_origen: Number(origen),
        sucursal_destino: Number(destino),
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
      },
      { onSuccess: () => setCantidad('') },
    )
  }

  const ayudaOrigen =
    herramienta && stockOrigen
      ? `Disponible: ${stockOrigen.unidades} unidades${
          herramienta.unidades_por_caja > 1 ? ` (${desgloseCajas(stockOrigen.cajas_completas, stockOrigen.unidades_sueltas)})` : ''
        }`
      : undefined

  return (
    <Card>
      <CardHeader titulo="Solicitar transferencia" descripcion="Queda pendiente hasta que un Administrador o Supervisor la complete." />
      <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
        <Field etiqueta="Herramienta">
          <Select value={herramientaId} onChange={(e) => cambiar(setHerramientaId)(e.target.value)}>
            <option value="">Selecciona una herramienta</option>
            {herramientas.map((h) => <option key={h.id} value={h.id}>{h.codigo} · {h.nombre}</option>)}
          </Select>
        </Field>

        <Field etiqueta="Desde (origen)" ayuda={ayudaOrigen} error={errores.sucursal_origen}>
          <Select value={origen} disabled={origenFijo !== null} onChange={(e) => cambiar(setOrigen)(e.target.value)}>
            <option value="" disabled>Selecciona</option>
            {sucursales.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </Select>
        </Field>
        <Field etiqueta="Hacia (destino)" error={errores.sucursal_destino}>
          <Select value={destino} onChange={(e) => cambiar(setDestino)(e.target.value)}>
            <option value="" disabled>Selecciona</option>
            {sucursales.filter((s) => String(s.id) !== origen).map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </Select>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field
            etiqueta="Cantidad"
            error={errores.cantidad}
            ayuda={herramienta && unidad === 'CAJA' && cantidadNumero > 0 ? `= ${unidades} unidades` : undefined}
          >
            <Input type="number" min={1} step={1} value={cantidad} onChange={(e) => cambiar(setCantidad)(e.target.value)} />
          </Field>
          <div>
            <span className="mb-1.5 block text-xs font-semibold text-muted">Unidad</span>
            <SegmentedControl<TipoUnidad>
              etiqueta="Unidad"
              valor={unidad}
              onCambiar={cambiar(setUnidad)}
              className="w-full [&>button]:flex-1"
              opciones={[
                { valor: 'UNIDAD', texto: 'Unidades' },
                { valor: 'CAJA', texto: herramienta ? `Cajas ×${herramienta.unidades_por_caja}` : 'Cajas' },
              ]}
            />
          </div>
        </div>

        {errores.detail && <Aviso tono="error">{errores.detail}</Aviso>}
        {error && Object.keys(errores).length === 0 && <Aviso tono="error">No se pudo solicitar la transferencia.</Aviso>}
        {isSuccess && <Aviso tono="exito">Transferencia solicitada: queda pendiente de aprobación.</Aviso>}

        <Button type="submit" variante="primary" className="w-full" cargando={isPending} disabled={!listo} icono={<Send size={16} aria-hidden />}>
          Solicitar transferencia
        </Button>
      </form>
    </Card>
  )
}
