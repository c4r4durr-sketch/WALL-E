import { useState, type FormEvent, type ReactNode } from 'react'
import { Save } from 'lucide-react'
import { Aviso, Button, Field, Input, Select } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { propsEntero, propsMonto, reglas, useFormulario, type Errores } from '../../../shared/validacion'
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
// Validación al instante con las reglas de shared/validacion (las mismas
// del backend): código en mayúsculas, enteros sin decimales, montos
// mayores que 0 con hasta 2 decimales. Que el código no esté repetido lo
// avisa el backend.
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

// `codigoOriginal`: en la edición, un código cargado antes de la regla de
// formato se puede conservar (el backend tampoco lo revisa si no cambia).
function validador(codigoOriginal: string | null, puedeCambiarCosto: boolean) {
  return (form: FormState): Errores<FormState> => ({
    codigo: form.codigo === codigoOriginal ? null : reglas.codigoHerramienta(form.codigo),
    nombre: reglas.texto(form.nombre, { etiqueta: 'El nombre', requerido: true, max: 150 }),
    modelo: reglas.texto(form.modelo, { etiqueta: 'El modelo', max: 100 }),
    unidades_por_caja: reglas.entero(form.unidades_por_caja, { vacio: 'Las unidades por caja son obligatorias.' }),
    costo_unitario: puedeCambiarCosto ? reglas.monto(form.costo_unitario) : null,
    demanda_anual: reglas.entero(form.demanda_anual, { requerido: false }),
    costo_pedido: reglas.monto(form.costo_pedido),
    costo_almacenamiento_unitario: reglas.monto(form.costo_almacenamiento_unitario),
    tiempo_entrega_dias: reglas.entero(form.tiempo_entrega_dias, { min: 0, requerido: false }),
  })
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

type TipoCampo = 'texto' | 'entero' | 'entero0' | 'monto'

export function HerramientaForm({ herramienta, onTerminar, puedeCambiarCosto }: Props) {
  const editando = Boolean(herramienta)
  const form = useFormulario<FormState>(
    herramienta ? aFormulario(herramienta) : FORM_VACIO,
    validador(herramienta?.codigo ?? null, puedeCambiarCosto),
  )
  const [foto, setFoto] = useState<Blob | null>(null)
  const [fotoTocada, setFotoTocada] = useState(false)
  // HU8: solo se ofrecen proveedores activos; si la herramienta ya tiene
  // uno que luego se desactivó, se muestra igual para no perderlo al guardar.
  const { data: proveedoresActivos } = useProveedores({ activos: true })
  const proveedorActualInactivo =
    herramienta?.proveedor != null && proveedoresActivos && !proveedoresActivos.some((p) => p.id === herramienta.proveedor)
  const crear = useCrearHerramienta()
  const actualizar = useActualizarHerramienta()
  const { isPending, error } = editando ? actualizar : crear
  const erroresServidor = erroresPorCampo(error)
  const faltaFoto = !editando && !foto
  const errorFoto = (fotoTocada && faltaFoto ? 'La foto del producto es obligatoria.' : undefined) ?? erroresServidor.imagen

  function cambiarFoto(nueva: Blob | null) {
    setFoto(nueva)
    setFotoTocada(true)
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFotoTocada(true)
    if (!form.enviar() || faltaFoto) return
    const v = form.valores
    const payload: HerramientaPayload = {
      codigo: v.codigo.trim().toUpperCase(),
      nombre: reglas.limpiar(v.nombre),
      modelo: reglas.limpiar(v.modelo),
      unidades_por_caja: Number(v.unidades_por_caja),
      demanda_anual: numeroONull(v.demanda_anual),
      costo_pedido: numeroONull(v.costo_pedido),
      costo_almacenamiento_unitario: numeroONull(v.costo_almacenamiento_unitario),
      tiempo_entrega_dias: numeroONull(v.tiempo_entrega_dias),
      costo_unitario: numeroONull(v.costo_unitario),
      proveedor: numeroONull(v.proveedor),
    }
    if (herramienta) {
      actualizar.mutate({ id: herramienta.id, ...payload, imagen: foto }, { onSuccess: onTerminar })
    } else if (foto) {
      crear.mutate({ ...payload, imagen: foto }, { onSuccess: onTerminar })
    }
  }

  const PROPS_TIPO: Record<TipoCampo, object> = {
    texto: { type: 'text' },
    entero: propsEntero(1),
    entero0: propsEntero(0),
    monto: propsMonto(),
  }

  function campo(
    nombre: CampoForm,
    etiqueta: string,
    props: { tipo?: TipoCampo; ayuda?: string; disabled?: boolean; opcional?: boolean; maxLength?: number } = {},
  ) {
    return (
      <Field
        etiqueta={etiqueta}
        ayuda={props.ayuda}
        error={form.error(nombre, erroresServidor)}
        opcional={props.opcional}
        obligatorio={!props.opcional}
      >
        <Input
          {...PROPS_TIPO[props.tipo ?? 'texto']}
          maxLength={props.maxLength}
          value={form.valores[nombre]}
          disabled={props.disabled}
          onChange={(event) => form.cambiar(nombre, nombre === 'codigo' ? event.target.value.toUpperCase() : event.target.value)}
          onBlur={() => form.tocar(nombre)}
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
          nombre={form.valores.nombre}
          onCambiar={cambiarFoto}
          error={errorFoto}
        />
      </Seccion>

      <Seccion titulo="Datos de la herramienta">
        <div className="grid grid-cols-2 gap-4">
          {campo('codigo', 'Código', { maxLength: 30, ayuda: 'Mayúsculas, números y guiones. Ej.: TAL-18V' })}
          {campo('nombre', 'Nombre', { maxLength: 150 })}
          {campo('modelo', 'Modelo', { opcional: true, maxLength: 100 })}
          {campo('unidades_por_caja', 'Unidades por caja', { tipo: 'entero' })}
          {campo('costo_unitario', 'Costo unitario de compra', {
            tipo: 'monto',
            opcional: true,
            disabled: !puedeCambiarCosto,
            ayuda: puedeCambiarCosto
              ? 'Mayor que 0, hasta 2 decimales. Cada cambio queda en el historial de costos.'
              : 'Solo el Administrador puede cambiarlo.',
          })}
          <Field etiqueta="Proveedor" error={erroresServidor.proveedor} opcional>
            <Select value={form.valores.proveedor} onChange={(event) => form.cambiar('proveedor', event.target.value)}>
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
          {campo('demanda_anual', 'Demanda anual (unidades)', { tipo: 'entero', opcional: true, ayuda: 'D en la fórmula EOQ. Entero mayor que 0.' })}
          {campo('costo_pedido', 'Costo por pedido', { tipo: 'monto', opcional: true, ayuda: 'S: costo fijo de cada pedido. Mayor que 0.' })}
          {campo('costo_almacenamiento_unitario', 'Costo de almacenar 1 unidad al año', { tipo: 'monto', opcional: true, ayuda: 'H en la fórmula EOQ. Mayor que 0.' })}
          {campo('tiempo_entrega_dias', 'Tiempo de entrega (días)', { tipo: 'entero0', opcional: true, ayuda: 'Para el punto de reorden. Entero, 0 o más.' })}
        </div>
      </Seccion>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button
          type="submit"
          variante="primary"
          cargando={isPending}
          disabled={!form.valido || faltaFoto}
          icono={<Save size={16} aria-hidden />}
        >
          {editando ? 'Guardar cambios' : 'Guardar herramienta'}
        </Button>
      </div>
    </form>
  )
}
