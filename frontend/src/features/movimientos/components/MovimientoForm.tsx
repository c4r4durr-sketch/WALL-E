import { useState, type FormEvent } from 'react'
import { ArrowDownToLine, ArrowUpFromLine } from 'lucide-react'
import { Aviso, Button, Card, CardHeader, Field, Input, SegmentedControl, Select } from '../../../components/ui'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoOperacion, TipoUnidad } from '../api/movimientosApi'
import { useRegistrarMovimiento, useStock } from '../hooks/useMovimientos'
import { desgloseCajas } from '../formato'
import { erroresDelBackend } from '../errores'
import { propsEntero, reglas, useFormulario } from '../../../shared/validacion'

// Formulario de entrada/salida (HU9) para la herramienta elegida en la
// página. Muestra el stock actual de la sucursal y, si se registra en
// cajas, su equivalente en unidades. La validación real (stock suficiente,
// sucursal del empleado) la hace el backend; acá se avisa al instante
// (cantidad entera mayor que 0, sucursal elegida, salida mayor que el stock).

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
  // Empleado: su sucursal viene fija (solo puede operar en su mostrador).
  sucursalFija: number | null
}

export function MovimientoForm({ herramienta, sucursales, sucursalFija }: Props) {
  const [tipo, setTipo] = useState<TipoOperacion>('ENTRADA')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const { data: stock } = useStock(herramienta.id)
  const { mutate, isPending, error, isSuccess, reset } = useRegistrarMovimiento()
  const errores = erroresDelBackend(error)
  const form = useFormulario({ sucursal: sucursalFija ? String(sucursalFija) : '', cantidad: '' }, (v) => ({
    sucursal: v.sucursal ? null : 'Selecciona una sucursal.',
    cantidad: reglas.entero(v.cantidad),
  }))
  const { sucursal, cantidad } = form.valores

  const cantidadNumero = Number(cantidad)
  const unidadesEquivalentes = unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockSucursal = stock?.find((s) => String(s.sucursal_id) === sucursal)
  const noAlcanza =
    tipo === 'SALIDA' && Boolean(stockSucursal) && !form.errores.cantidad && unidadesEquivalentes > (stockSucursal?.unidades ?? 0)
  const errorCantidad =
    form.error('cantidad', errores) ??
    (noAlcanza ? `No alcanza: hay ${stockSucursal?.unidades} unidades en esta sucursal.` : undefined)

  function limpiarAvisos() {
    if (error || isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.enviar() || noAlcanza) return
    mutate(
      {
        herramienta: herramienta.id,
        sucursal: Number(sucursal),
        tipo_movimiento: tipo,
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
      },
      { onSuccess: () => form.reiniciar({ sucursal, cantidad: '' }) },
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

        <Field etiqueta="Sucursal" obligatorio ayuda={ayudaSucursal} error={form.error('sucursal', errores)}>
          <Select
            value={sucursal}
            disabled={sucursalFija !== null}
            onChange={(event) => { form.cambiar('sucursal', event.target.value); limpiarAvisos() }}
            onBlur={() => form.tocar('sucursal')}
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
            obligatorio
            error={errorCantidad}
            ayuda={unidad === 'CAJA' && cantidadNumero > 0 ? `= ${unidadesEquivalentes} unidades` : undefined}
          >
            <Input
              {...propsEntero()}
              value={cantidad}
              onChange={(event) => { form.cambiar('cantidad', event.target.value); limpiarAvisos() }}
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
          disabled={!form.valido || noAlcanza}
        >
          {tipo === 'ENTRADA' ? 'Registrar entrada' : 'Registrar salida'}
        </Button>
      </form>
    </Card>
  )
}
