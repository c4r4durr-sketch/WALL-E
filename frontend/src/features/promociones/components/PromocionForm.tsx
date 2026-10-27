import { useState, type FormEvent } from 'react'
import { Tag } from 'lucide-react'
import { Aviso, Button, Field, Input } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { hoyEnLaPaz, sumarDias } from '../../../shared/formato'
import { useCrearPromocion } from '../hooks/usePromociones'

// Alta de una promoción (HU23) sobre una herramienta estancada en una
// sucursal, dentro de un modal. Empieza hoy; se elige el descuento y hasta
// cuándo dura. Las mismas reglas que el backend se revisan antes de
// enviar; si el backend la rechaza (ya no está estancada, ya hay una
// vigente) se muestra su mensaje.

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

type Errores = Partial<Record<'descuento_porcentaje' | 'fecha_fin', string>>

function validar(form: FormState, hoy: string): Errores {
  const errores: Errores = {}
  const descuento = Number(form.descuento)
  if (!Number.isInteger(descuento) || descuento < 1 || descuento > 90) {
    errores.descuento_porcentaje = 'Un número entero entre 1 y 90.'
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(form.fechaFin) || form.fechaFin < hoy) {
    errores.fecha_fin = 'Hoy o una fecha posterior.'
  }
  return errores
}

export function PromocionForm({ linea, onTerminar }: { linea: Promocionable; onTerminar: () => void }) {
  const hoy = hoyEnLaPaz()
  const crear = useCrearPromocion()
  const [form, setForm] = useState<FormState>({ descuento: '20', fechaFin: sumarDias(hoy, 15), motivo: '' })
  const [errores, setErrores] = useState<Errores>({})
  const erroresServidor = erroresPorCampo(crear.error) as Errores
  const visibles: Errores = { ...erroresServidor, ...errores }
  const errorGeneral =
    crear.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(crear.error, 'No se pudo crear la promoción. Intenta de nuevo.')
      : null

  function setCampo(campo: keyof FormState, valor: string) {
    setForm((prev) => ({ ...prev, [campo]: valor }))
    setErrores({})
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nuevos = validar(form, hoy)
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) return
    crear.mutate(
      {
        herramienta_id: linea.herramienta_id,
        sucursal_id: linea.sucursal_id,
        descuento_porcentaje: Number(form.descuento),
        fecha_fin: form.fechaFin,
        motivo: form.motivo.trim(),
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
        <Field etiqueta="Descuento (%)" error={visibles.descuento_porcentaje}>
          <Input
            type="number"
            min={1}
            max={90}
            inputMode="numeric"
            value={form.descuento}
            onChange={(e) => setCampo('descuento', e.target.value)}
            autoFocus
          />
        </Field>
        <Field etiqueta="Hasta (inclusive)" error={visibles.fecha_fin}>
          <Input type="date" min={hoy} value={form.fechaFin} onChange={(e) => setCampo('fechaFin', e.target.value)} />
        </Field>
      </div>
      <Field etiqueta="Motivo" opcional>
        <Input value={form.motivo} maxLength={255} onChange={(e) => setCampo('motivo', e.target.value)} />
      </Field>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button type="submit" variante="primary" cargando={crear.isPending} icono={<Tag size={16} aria-hidden />}>
          Crear promoción
        </Button>
      </div>
    </form>
  )
}
