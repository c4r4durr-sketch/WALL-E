import type { FormEvent } from 'react'
import { Tag } from 'lucide-react'
import { Aviso, Button, Field, Input } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { hoyEnLaPaz, sumarDias } from '../../../shared/formato'
import { useCrearPromocion } from '../hooks/usePromociones'
import { DESCUENTO, LARGO_TEXTO, propsEntero, reglas, useFormulario, type Errores } from '../../../shared/validacion'

// Etiqueta de promoción (HU23) sobre una herramienta estancada en una
// sucursal, dentro de un modal. Empieza hoy; se elige hasta cuándo dura y,
// si se quiere, un descuento (entero de 1 a 90). Las mismas reglas que el
// backend (shared/validacion) se revisan al instante; si el backend la rechaza (ya no está estancada, ya hay
// una vigente) se muestra su mensaje.

export interface Promocionable {
  herramienta_id: number
  codigo: string
  nombre: string
  sucursal_id: number
  sucursal_nombre: string
  dias_sin_venta: number
}

interface FormState {
  descuento: string
  fechaFin: string
  motivo: string
}

function validador(hoy: string) {
  return (form: FormState): Errores<FormState> => ({
    descuento: reglas.entero(form.descuento, { ...DESCUENTO, requerido: false }),
    fechaFin: reglas.fechaDesde(form.fechaFin, hoy, 'Hoy o una fecha posterior.'),
    motivo: reglas.texto(form.motivo),
  })
}

export function PromocionForm({ linea, onTerminar }: { linea: Promocionable; onTerminar: () => void }) {
  const hoy = hoyEnLaPaz()
  const crear = useCrearPromocion()
  const formulario = useFormulario<FormState>({ descuento: '', fechaFin: sumarDias(hoy, 15), motivo: '' }, validador(hoy))
  const form = formulario.valores
  const erroresServidor = erroresPorCampo(crear.error)
  const errorGeneral =
    crear.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(crear.error, 'No se pudo crear la promoción. Intenta de nuevo.')
      : null

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!formulario.enviar()) return
    crear.mutate(
      {
        herramienta_id: linea.herramienta_id,
        sucursal_id: linea.sucursal_id,
        descuento_porcentaje: form.descuento.trim() === '' ? null : Number(form.descuento),
        fecha_fin: form.fechaFin,
        motivo: reglas.limpiar(form.motivo),
      },
      { onSuccess: onTerminar },
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="rounded-campo bg-surf2 px-4 py-3 text-sm">
        <p className="font-semibold text-ink">{linea.codigo} · {linea.nombre}</p>
        <p className="text-muted">
          {linea.sucursal_nombre} · <span className="tabular-nums">{linea.dias_sin_venta}</span> días sin venta
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field
          etiqueta="Descuento (%)"
          opcional
          ayuda="Entero de 1 a 90."
          error={formulario.error('descuento') ?? erroresServidor.descuento_porcentaje}
        >
          <Input
            {...propsEntero(DESCUENTO.min, DESCUENTO.max)}
            placeholder="Sin descuento"
            value={form.descuento}
            onChange={(e) => formulario.cambiar('descuento', e.target.value)}
            onBlur={() => formulario.tocar('descuento')}
            autoFocus
          />
        </Field>
        <Field etiqueta="Hasta (inclusive)" obligatorio error={formulario.error('fechaFin') ?? erroresServidor.fecha_fin}>
          <Input
            type="date"
            min={hoy}
            value={form.fechaFin}
            onChange={(e) => formulario.cambiar('fechaFin', e.target.value)}
            onBlur={() => formulario.tocar('fechaFin')}
          />
        </Field>
      </div>
      <Field etiqueta="Motivo" opcional error={formulario.error('motivo') ?? erroresServidor.motivo}>
        <Input
          value={form.motivo}
          maxLength={LARGO_TEXTO}
          onChange={(e) => formulario.cambiar('motivo', e.target.value)}
          onBlur={() => formulario.tocar('motivo')}
        />
      </Field>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button type="submit" variante="primary" cargando={crear.isPending} disabled={!formulario.valido} icono={<Tag size={16} aria-hidden />}>
          Poner en promoción
        </Button>
      </div>
    </form>
  )
}
