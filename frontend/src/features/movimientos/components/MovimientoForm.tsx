import { useState, type FormEvent } from 'react'
import { ArrowDownToLine, ArrowUpFromLine } from 'lucide-react'
import { Aviso, Button, Card, CardHeader, Field, Input, SegmentedControl, Select } from '../../../components/ui'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoOperacion, TipoUnidad } from '../api/movimientosApi'
import { useRegistrarMovimiento, useStock } from '../hooks/useMovimientos'
import { desgloseCajas } from '../formato'
import { erroresDelBackend } from '../errores'

// Formulario de entrada/salida (HU9) para la herramienta elegida en la
// página. Muestra el stock actual de la sucursal y, si se registra en
// cajas, su equivalente en unidades. La validación real (stock suficiente,
// sucursal del empleado) la hace el backend; acá solo se informa.

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
  // Empleado: su sucursal viene fija (solo puede operar en su mostrador).
  sucursalFija: number | null
}

export function MovimientoForm({ herramienta, sucursales, sucursalFija }: Props) {
  const [tipo, setTipo] = useState<TipoOperacion>('ENTRADA')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const [cantidad, setCantidad] = useState('')
  const [sucursal, setSucursal] = useState<string>(sucursalFija ? String(sucursalFija) : '')
  const { data: stock } = useStock(herramienta.id)
  const { mutate, isPending, error, isSuccess, reset } = useRegistrarMovimiento()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidadesEquivalentes = unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockSucursal = stock?.find((s) => String(s.sucursal_id) === sucursal)

  function limpiarAvisos() {
    if (error || isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate(
      {
        herramienta: herramienta.id,
        sucursal: Number(sucursal),
        tipo_movimiento: tipo,
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
      },
      { onSuccess: () => setCantidad('') },
    )
  }

  const ayudaSucursal = stockSucursal
    ? `Stock actual: ${stockSucursal.unidades} unidades${
        herramienta.unidades_por_caja > 1 ? ` (${desgloseCajas(stockSucursal.cajas_completas, stockSucursal.unidades_sueltas)})` : ''
      }`
    : undefined

  return (
    <Card>
      <CardHeader titulo="Registrar movimiento" descripcion="Entradas y salidas del mostrador. No se editan ni se borran." />
      <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
        <SegmentedControl<TipoOperacion>
          etiqueta="Tipo de movimiento"
          valor={tipo}
          onCambiar={(t) => { setTipo(t); limpiarAvisos() }}
          className="w-full [&>button]:flex-1"
          opciones={[
            { valor: 'ENTRADA', texto: <><ArrowDownToLine size={15} aria-hidden />Entrada</> },
            { valor: 'SALIDA', texto: <><ArrowUpFromLine size={15} aria-hidden />Salida</> },
          ]}
        />

        <Field etiqueta="Sucursal" ayuda={ayudaSucursal} error={errores.sucursal}>
          <Select
            value={sucursal}
            disabled={sucursalFija !== null}
            onChange={(event) => { setSucursal(event.target.value); limpiarAvisos() }}
          >
            <option value="" disabled>Selecciona una sucursal</option>
            {sucursales.map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </Select>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field
            etiqueta="Cantidad"
            error={errores.cantidad}
            ayuda={unidad === 'CAJA' && cantidadNumero > 0 ? `= ${unidadesEquivalentes} unidades` : undefined}
          >
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
              etiqueta="Unidad"
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

        {errores.detail && <Aviso tono="error">{errores.detail}</Aviso>}
        {error && Object.keys(errores).length === 0 && (
          <Aviso tono="error">No se pudo registrar el movimiento. Intenta de nuevo.</Aviso>
        )}
        {isSuccess && <Aviso tono="exito">Movimiento registrado.</Aviso>}

        <Button
          type="submit"
          variante="primary"
          className="w-full"
          cargando={isPending}
          disabled={!sucursal || !(cantidadNumero >= 1)}
        >
          {tipo === 'ENTRADA' ? 'Registrar entrada' : 'Registrar salida'}
        </Button>
      </form>
    </Card>
  )
}
