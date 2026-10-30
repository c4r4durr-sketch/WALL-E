import { useState, type FormEvent } from 'react'
import { ChevronRight, Minus, Plus, Wrench } from 'lucide-react'
import { Aviso, Button, Card, CardHeader, Field, Input, SegmentedControl, Select, Textarea } from '../../../components/ui'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoUnidad } from '../api/movimientosApi'
import { useRegistrarAjuste, useStock } from '../hooks/useMovimientos'
import { desgloseCajas } from '../formato'
import { erroresDelBackend } from '../errores'

// Ajuste de inventario: CORRECCIÓN de stock, no una operación normal del
// mostrador. Por eso vive en una sección aparte (ámbar, cerrada por
// defecto) y solo la ve Administrador/Supervisor. Los movimientos no se
// editan ni se borran: un error se corrige con un ajuste que queda en el
// historial con su motivo. No cuenta como demanda para EOQ/ABC.

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
}

type Sentido = 'POSITIVO' | 'NEGATIVO'

export function AjusteForm({ herramienta, sucursales }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [sentido, setSentido] = useState<Sentido>('NEGATIVO')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const [cantidad, setCantidad] = useState('')
  const [sucursal, setSucursal] = useState('')
  const [motivo, setMotivo] = useState('')
  const { data: stock } = useStock(herramienta.id)
  const { mutate, isPending, error, isSuccess, reset } = useRegistrarAjuste()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidades = unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockSucursal = stock?.find((s) => String(s.sucursal_id) === sucursal)
  const stockResultante = (stockSucursal?.unidades ?? 0) + (sentido === 'POSITIVO' ? unidades : -unidades)
  const noAlcanza = Boolean(stockSucursal) && cantidadNumero >= 1 && stockResultante < 0
  const listo = sucursal !== '' && cantidadNumero >= 1 && motivo.trim() !== ''

  function limpiarAvisos() {
    if (error || isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate(
      {
        herramienta: herramienta.id,
        sucursal: Number(sucursal),
        sentido,
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
        motivo: motivo.trim(),
      },
      { onSuccess: () => { setCantidad(''); setMotivo('') } },
    )
  }

  if (!abierto) {
    return (
      <Card interactiva sinPadding>
        <button
          type="button"
          onClick={() => setAbierto(true)}
          aria-expanded={false}
          className="flex w-full items-center gap-4 rounded-[26px] p-5 text-left"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-warn-b text-warn">
            <Wrench size={18} aria-hidden />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-semibold text-ink">Registrar un ajuste de inventario</span>
            <span className="block text-xs text-muted">
              Solo para corregir errores de conteo, roturas o pérdidas. No es una entrada ni una salida normal.
            </span>
          </span>
          <ChevronRight size={18} aria-hidden className="text-muted" />
        </button>
      </Card>
    )
  }

  let ayudaSucursal: string | undefined
  if (stockSucursal) {
    ayudaSucursal = `Stock actual: ${stockSucursal.unidades} unidades`
    if (herramienta.unidades_por_caja > 1) {
      ayudaSucursal += ` (${desgloseCajas(stockSucursal.cajas_completas, stockSucursal.unidades_sueltas)})`
    }
    if (cantidadNumero >= 1 && stockResultante >= 0) ayudaSucursal += ` → quedaría en ${stockResultante}`
  }
  const errorSucursal =
    errores.sucursal ?? (noAlcanza ? `No alcanza: no se pueden restar ${unidades} unidades si hay ${stockSucursal?.unidades}.` : undefined)

  return (
    <Card className="ring-2 ring-warn">
      <CardHeader
        titulo="Ajuste de inventario (corrección)"
        descripcion="Queda en el historial con tu usuario y el motivo. No cuenta como venta para los indicadores."
        acciones={<Button variante="ghost" tamano="sm" onClick={() => { setAbierto(false); reset() }}>Cerrar</Button>}
      />
      <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
        <SegmentedControl<Sentido>
          etiqueta="Sentido del ajuste"
          valor={sentido}
          onCambiar={(s) => { setSentido(s); limpiarAvisos() }}
          className="w-full [&>button]:flex-1"
          opciones={[
            { valor: 'POSITIVO', texto: <><Plus size={15} aria-hidden />Sumar al stock</> },
            { valor: 'NEGATIVO', texto: <><Minus size={15} aria-hidden />Restar del stock</> },
          ]}
        />

        <Field etiqueta="Sucursal" ayuda={ayudaSucursal} error={errorSucursal}>
          <Select value={sucursal} onChange={(event) => { setSucursal(event.target.value); limpiarAvisos() }}>
            <option value="" disabled>Selecciona una sucursal</option>
            {sucursales.map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </Select>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field etiqueta="Cantidad" error={errores.cantidad}>
            <Input
              type="number"
              min={1}
              step={1}
              value={cantidad}
              onChange={(event) => { setCantidad(event.target.value); limpiarAvisos() }}
            />
          </Field>
          <div>
            <span className="mb-1.5 block text-xs font-semibold text-muted">Unidad</span>
            <SegmentedControl<TipoUnidad>
              etiqueta="Unidad del ajuste"
              valor={unidad}
              onCambiar={(u) => { setUnidad(u); limpiarAvisos() }}
              className="w-full [&>button]:flex-1"
              opciones={[
                { valor: 'UNIDAD', texto: 'Unidades' },
                { valor: 'CAJA', texto: `Cajas ×${herramienta.unidades_por_caja}` },
              ]}
            />
          </div>
        </div>

        <Field etiqueta="Motivo" error={errores.motivo}>
          <Textarea
            rows={2}
            maxLength={255}
            value={motivo}
            placeholder="Ej.: conteo físico del 20/09 encontró 3 unidades menos"
            onChange={(event) => { setMotivo(event.target.value); limpiarAvisos() }}
          />
        </Field>

        {errores.detail && <Aviso tono="error">{errores.detail}</Aviso>}
        {error && Object.keys(errores).length === 0 && (
          <Aviso tono="error">No se pudo registrar el ajuste. Intenta de nuevo.</Aviso>
        )}
        {isSuccess && <Aviso tono="exito">Ajuste registrado.</Aviso>}

        {/* Secundario: la acción naranja de la pantalla es el movimiento normal. */}
        <Button type="submit" className="w-full" cargando={isPending} disabled={!listo}>
          {sentido === 'POSITIVO' ? 'Registrar ajuste (sumar)' : 'Registrar ajuste (restar)'}
        </Button>
      </form>
    </Card>
  )
}
