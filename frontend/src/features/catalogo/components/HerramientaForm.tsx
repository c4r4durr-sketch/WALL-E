import { useState, type FormEvent, type ReactNode } from 'react'
import { Save } from 'lucide-react'
import { Aviso, Button, Field, Input, Select } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { useCrearHerramienta } from '../hooks/useCrearHerramienta'
import { useActualizarHerramienta } from '../hooks/useActualizarHerramienta'
import { useProveedores } from '../../proveedores/hooks/useProveedores'
import { FotoDropzone } from './FotoDropzone'
import type { Herramienta, HerramientaPayload } from '../api/catalogoApi'

// Formulario de alta y edición de herramientas (HU6), incluidos los datos
// de entrada de EOQ/ROP (HU15/HU16). Esos cuatro son opcionales: un campo
// vacío se envía como null y el indicador correspondiente queda sin
// calcular hasta que se complete. Vive dentro del panel lateral del
// catálogo; las secciones van sobre superficie sólida (nunca vidrio).
//
// Con `herramienta` funciona en modo edición (precargado, PUT al guardar);
// sin ella, en modo alta. El padre lo monta con una `key` distinta cada
// vez que se abre, así el estado arranca limpio.
//
// Foto: obligatoria en el alta (el backend responde 400 sin ella); en la
// edición se puede reemplazar.
//
// HU7: el costo unitario solo lo cambia el Administrador; para el
// Supervisor el campo se ve deshabilitado y se reenvía sin cambios (el
// backend responde 403 si alguien fuerza un cambio).

const FORM_VACIO = {
  codigo: '',
  nombre: '',
  modelo: '',
  unidades_por_caja: '1',
  demanda_anual: '',
  costo_pedido: '',
  costo_almacenamiento_unitario: '',
  tiempo_entrega_dias: '',
  costo_unitario: '',
  proveedor: '',
}

type FormState = typeof FORM_VACIO
type CampoForm = keyof FormState

function aFormulario(herramienta: Herramienta): FormState {
  const texto = (valor: number | null) => (valor === null ? '' : String(valor))
  return {
    codigo: herramienta.codigo,
    nombre: herramienta.nombre,
    modelo: herramienta.modelo,
    unidades_por_caja: String(herramienta.unidades_por_caja),
    demanda_anual: texto(herramienta.demanda_anual),
    costo_pedido: texto(herramienta.costo_pedido),
    costo_almacenamiento_unitario: texto(herramienta.costo_almacenamiento_unitario),
    tiempo_entrega_dias: texto(herramienta.tiempo_entrega_dias),
    costo_unitario: texto(herramienta.costo_unitario),
    proveedor: texto(herramienta.proveedor),
  }
}

function numeroONull(valor: string): number | null {
  return valor.trim() === '' ? null : Number(valor)
}

function Seccion({ titulo, descripcion, children }: { titulo: string; descripcion?: string; children: ReactNode }) {
  return (
    <section className="rounded-card bg-surf p-5 shadow-sh">
      <h3 className="text-sm font-semibold text-ink">{titulo}</h3>
      {descripcion && <p className="mt-0.5 text-xs text-muted">{descripcion}</p>}
      <div className="mt-4">{children}</div>
    </section>
  )
}

interface Props {
  herramienta?: Herramienta | null
  onTerminar: () => void
  puedeCambiarCosto: boolean
}

export function HerramientaForm({ herramienta, onTerminar, puedeCambiarCosto }: Props) {
  const editando = Boolean(herramienta)
  const [form, setForm] = useState<FormState>(herramienta ? aFormulario(herramienta) : FORM_VACIO)
  const [foto, setFoto] = useState<Blob | null>(null)
  const [erroresLocales, setErroresLocales] = useState<Partial<Record<CampoForm | 'imagen', string>>>({})
  // HU8: solo se ofrecen proveedores activos; si la herramienta ya tiene
  // uno que luego se desactivó, se muestra igual para no perderlo al guardar.
  const { data: proveedoresActivos } = useProveedores({ activos: true })
  const proveedorActualInactivo =
    herramienta?.proveedor != null && proveedoresActivos && !proveedoresActivos.some((p) => p.id === herramienta.proveedor)
  const crear = useCrearHerramienta()
  const actualizar = useActualizarHerramienta()
  const { isPending, error, reset } = editando ? actualizar : crear
  // Los del backend (400 por campo) y los del formulario, que tienen
  // prioridad mientras se corrigen.
  const erroresServidor = erroresPorCampo(error)
  const errores: Record<string, string | undefined> = { ...erroresServidor, ...erroresLocales }

  function cambiar(campo: CampoForm, valor: string) {
    setForm({ ...form, [campo]: valor })
    if (erroresLocales[campo]) setErroresLocales({ ...erroresLocales, [campo]: undefined })
    if (error) reset()
  }

  function cambiarFoto(nueva: Blob | null) {
    setFoto(nueva)
    if (erroresLocales.imagen) setErroresLocales({ ...erroresLocales, imagen: undefined })
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const locales: typeof erroresLocales = {}
    const costo = numeroONull(form.costo_unitario)
    if (costo !== null && !(costo > 0)) locales.costo_unitario = 'El costo unitario debe ser un número mayor que cero.'
    if (!editando && !foto) locales.imagen = 'La foto del producto es obligatoria.'
    if (Object.keys(locales).length > 0) {
      setErroresLocales(locales)
      return
    }
    const payload: HerramientaPayload = {
      codigo: form.codigo.trim(),
      nombre: form.nombre.trim(),
      modelo: form.modelo.trim(),
      unidades_por_caja: Number(form.unidades_por_caja),
      demanda_anual: numeroONull(form.demanda_anual),
      costo_pedido: numeroONull(form.costo_pedido),
      costo_almacenamiento_unitario: numeroONull(form.costo_almacenamiento_unitario),
      tiempo_entrega_dias: numeroONull(form.tiempo_entrega_dias),
      costo_unitario: costo,
      proveedor: numeroONull(form.proveedor),
    }
    if (herramienta) {
      actualizar.mutate({ id: herramienta.id, ...payload, imagen: foto }, { onSuccess: onTerminar })
    } else if (foto) {
      crear.mutate({ ...payload, imagen: foto }, { onSuccess: onTerminar })
    }
  }

  function campo(
    nombre: CampoForm,
    etiqueta: string,
    props: { type?: string; step?: string; ayuda?: string; disabled?: boolean; opcional?: boolean } = {},
  ) {
    return (
      <Field etiqueta={etiqueta} ayuda={props.ayuda} error={errores[nombre]} opcional={props.opcional}>
        <Input
          type={props.type ?? 'text'}
          step={props.step}
          min={props.type === 'number' ? 0 : undefined}
          value={form[nombre]}
          disabled={props.disabled}
          onChange={(event) => cambiar(nombre, event.target.value)}
        />
      </Field>
    )
  }

  const errorGeneral =
    error && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(error, 'No se pudo guardar la herramienta. Intenta de nuevo.')
      : null

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <Seccion titulo="Foto del producto" descripcion={editando ? undefined : 'Obligatoria para dar de alta la herramienta.'}>
        <FotoDropzone
          actual={herramienta?.imagen ?? null}
          nombre={form.nombre}
          onCambiar={cambiarFoto}
          error={errores.imagen}
        />
      </Seccion>

      <Seccion titulo="Datos de la herramienta">
        <div className="grid grid-cols-2 gap-4">
          {campo('codigo', 'Código')}
          {campo('nombre', 'Nombre')}
          {campo('modelo', 'Modelo', { opcional: true })}
          {campo('unidades_por_caja', 'Unidades por caja', { type: 'number', step: '1' })}
          {campo('costo_unitario', 'Costo unitario de compra', {
            type: 'number',
            step: '0.01',
            opcional: true,
            disabled: !puedeCambiarCosto,
            ayuda: puedeCambiarCosto
              ? 'Cada cambio queda en el historial de costos.'
              : 'Solo el Administrador puede cambiarlo.',
          })}
          <Field etiqueta="Proveedor" error={errores.proveedor} opcional>
            <Select value={form.proveedor} onChange={(event) => cambiar('proveedor', event.target.value)}>
              <option value="">Sin proveedor</option>
              {proveedorActualInactivo && herramienta && (
                <option value={String(herramienta.proveedor)}>{herramienta.proveedor_nombre} (inactivo)</option>
              )}
              {proveedoresActivos?.map((p) => (
                <option key={p.id} value={String(p.id)}>{p.nombre}</option>
              ))}
            </Select>
          </Field>
        </div>
      </Seccion>

      <Seccion titulo="Datos para EOQ y punto de reorden" descripcion="Opcionales: sin ellos el indicador queda sin calcular.">
        <div className="grid grid-cols-2 gap-4">
          {campo('demanda_anual', 'Demanda anual (unidades)', { type: 'number', step: '1', ayuda: 'D en la fórmula EOQ.' })}
          {campo('costo_pedido', 'Costo por pedido', { type: 'number', step: '0.01', ayuda: 'S: costo fijo de cada pedido.' })}
          {campo('costo_almacenamiento_unitario', 'Costo de almacenar 1 unidad al año', { type: 'number', step: '0.01', ayuda: 'H en la fórmula EOQ.' })}
          {campo('tiempo_entrega_dias', 'Tiempo de entrega (días)', { type: 'number', step: '1', ayuda: 'Para el punto de reorden.' })}
        </div>
      </Seccion>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button type="submit" variante="primary" cargando={isPending} icono={<Save size={16} aria-hidden />}>
          {editando ? 'Guardar cambios' : 'Guardar herramienta'}
        </Button>
      </div>
    </form>
  )
}
