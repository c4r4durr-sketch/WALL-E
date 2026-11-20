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
import { propsEntero, reglas, useFormulario } from '../../../shared/validacion'

// Solicitud de transferencia (HU12). Queda PENDIENTE: el stock no se mueve
// hasta que un Administrador/Supervisor la completa. Muestra el stock en
// origen y avisa al instante si se pide más de lo que hay, si falta un
// dato o si la cantidad no es un entero mayor que 0 (el backend igual lo
// valida).

interface Props {
  herramientas: Herramienta[]
  sucursales: Sucursal[]
  // Empleado: el origen es siempre su sucursal.
  origenFijo: number | null
}

export function SolicitudForm({ herramientas, sucursales, origenFijo }: Props) {
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const form = useFormulario(
    { herramienta: '', origen: origenFijo ? String(origenFijo) : '', destino: '', cantidad: '' },
    (v) => ({
      herramienta: v.herramienta ? null : 'Selecciona una herramienta.',
      origen: v.origen ? null : 'Selecciona la sucursal de origen.',
      destino: !v.destino ? 'Selecciona la sucursal de destino.' : v.destino === v.origen ? 'Debe ser distinta del origen.' : null,
      cantidad: reglas.entero(v.cantidad),
    }),
  )
  const { herramienta: herramientaId, origen, destino, cantidad } = form.valores
  const herramienta = herramientas.find((h) => String(h.id) === herramientaId)
  const { data: stock } = useStock(herramienta?.id ?? null)
  const { mutate, isPending, error, isSuccess, reset } = useSolicitarTransferencia()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidades = herramienta && unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockOrigen = stock?.find((s) => String(s.sucursal_id) === origen)
  const noAlcanza = Boolean(stockOrigen) && !form.errores.cantidad && unidades > (stockOrigen?.unidades ?? 0)
  const errorCantidad =
    form.error('cantidad', errores) ?? (noAlcanza ? `No alcanza: hay ${stockOrigen?.unidades} unidades en el origen.` : undefined)

  function limpiarAvisos() {
    if (error || isSuccess) reset()
  }

  function cambiar(campo: 'herramienta' | 'origen' | 'destino' | 'cantidad', valor: string) {
    form.cambiar(campo, valor)
    limpiarAvisos()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.enviar() || noAlcanza) return
    mutate(
      {
        herramienta: Number(herramientaId),
        sucursal_origen: Number(origen),
        sucursal_destino: Number(destino),
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
      },
      { onSuccess: () => form.reiniciar({ ...form.valores, cantidad: '' }) },
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
        <Field etiqueta="Herramienta" obligatorio error={form.error('herramienta', errores)}>
          <Select value={herramientaId} onChange={(e) => cambiar('herramienta', e.target.value)} onBlur={() => form.tocar('herramienta')}>
            <option value="">Selecciona una herramienta</option>
            {herramientas.map((h) => <option key={h.id} value={h.id}>{h.codigo} · {h.nombre}</option>)}
          </Select>
        </Field>

        <Field etiqueta="Desde (origen)" obligatorio ayuda={ayudaOrigen} error={form.error('origen') ?? errores.sucursal_origen}>
          <Select value={origen} disabled={origenFijo !== null} onChange={(e) => cambiar('origen', e.target.value)} onBlur={() => form.tocar('origen')}>
            <option value="" disabled>Selecciona</option>
            {sucursales.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </Select>
        </Field>
        <Field etiqueta="Hacia (destino)" obligatorio error={form.error('destino') ?? errores.sucursal_destino}>
          <Select value={destino} onChange={(e) => cambiar('destino', e.target.value)} onBlur={() => form.tocar('destino')}>
            <option value="" disabled>Selecciona</option>
            {sucursales.filter((s) => String(s.id) !== origen).map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </Select>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field
            etiqueta="Cantidad"
            obligatorio
            error={errorCantidad}
            ayuda={herramienta && unidad === 'CAJA' && cantidadNumero > 0 ? `= ${unidades} unidades` : undefined}
          >
            <Input
              {...propsEntero()}
              value={cantidad}
              onChange={(e) => cambiar('cantidad', e.target.value)}
              onBlur={() => form.tocar('cantidad')}
            />
          </Field>
          <div>
            <span className="mb-1.5 block text-xs font-semibold text-muted">Unidad</span>
            <SegmentedControl<TipoUnidad>
              etiqueta="Unidad"
              valor={unidad}
              onCambiar={(u) => { setUnidad(u); limpiarAvisos() }}
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

        <Button type="submit" variante="primary" className="w-full" cargando={isPending} disabled={!form.valido || noAlcanza} icono={<Send size={16} aria-hidden />}>
          Solicitar transferencia
        </Button>
      </form>
    </Card>
  )
}
