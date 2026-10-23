import { useEffect, useId, useRef, useState, type DragEvent, type KeyboardEvent, type PointerEvent } from 'react'
import { ImagePlus, Move, RefreshCw } from 'lucide-react'
import { Button, ProductImage, cx } from '../../../components/ui'
import { centrado, conZoom, escala, exportarRecorte, limitar, validarArchivo, type Encuadre } from './recorte'

// Foto del producto (docs/DISENO.md): arrastrar y soltar o elegir un
// archivo (JPG, PNG o WebP, máx. 5 MB), vista previa y recorte cuadrado
// 1:1. El recorte se ajusta moviendo la imagen (mouse o flechas) y con el
// zoom; cada ajuste entrega el JPEG recortado al formulario (onCambiar).
// En la edición se ve la foto actual y se puede reemplazar, no quitar.

const LADO = 240 // px del visor

interface Props {
  // Foto que ya tiene la herramienta (edición); null en el alta.
  actual: string | null
  nombre: string
  onCambiar: (foto: Blob | null) => void
  error?: string | null
}

interface Cargada {
  url: string
  imagen: HTMLImageElement
}

export function FotoDropzone({ actual, nombre, onCambiar, error }: Props) {
  const idInput = useId()
  const idAyuda = `${idInput}-ayuda`
  const input = useRef<HTMLInputElement>(null)
  const [cargada, setCargada] = useState<Cargada | null>(null)
  const [encuadre, setEncuadre] = useState<Encuadre>({ zoom: 1, x: 0, y: 0 })
  const [arrastrandoArchivo, setArrastrandoArchivo] = useState(false)
  const [errorLocal, setErrorLocal] = useState<string | null>(null)
  const arrastre = useRef<{ x: number; y: number; desde: Encuadre } | null>(null)
  const espera = useRef<number | undefined>(undefined)

  // Libera la URL temporal de la imagen elegida.
  useEffect(() => () => {
    if (cargada) URL.revokeObjectURL(cargada.url)
  }, [cargada])
  useEffect(() => () => window.clearTimeout(espera.current), [])

  function entregar(imagen: HTMLImageElement, e: Encuadre, demora = 0) {
    window.clearTimeout(espera.current)
    espera.current = window.setTimeout(() => {
      exportarRecorte(imagen, e, LADO)
        .then(onCambiar)
        .catch((err: unknown) => setErrorLocal(err instanceof Error ? err.message : 'No se pudo recortar la imagen.'))
    }, demora)
  }

  function elegir(archivo: File | undefined) {
    if (!archivo) return
    const problema = validarArchivo(archivo)
    if (problema) {
      setErrorLocal(problema)
      return
    }
    const url = URL.createObjectURL(archivo)
    const imagen = new Image()
    imagen.onload = () => {
      const inicial = centrado(imagen.naturalWidth, imagen.naturalHeight, LADO)
      setErrorLocal(null)
      setCargada({ url, imagen })
      setEncuadre(inicial)
      entregar(imagen, inicial)
    }
    imagen.onerror = () => {
      URL.revokeObjectURL(url)
      setErrorLocal('No se pudo abrir la imagen. Prueba con otro archivo.')
    }
    imagen.src = url
  }

  function mover(nuevo: Encuadre, demora = 0) {
    if (!cargada) return
    const limitado = limitar(nuevo, cargada.imagen.naturalWidth, cargada.imagen.naturalHeight, LADO)
    setEncuadre(limitado)
    entregar(cargada.imagen, limitado, demora)
  }

  function alSoltar(event: DragEvent) {
    event.preventDefault()
    setArrastrandoArchivo(false)
    elegir(event.dataTransfer.files[0])
  }

  function alPresionar(event: PointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId)
    arrastre.current = { x: event.clientX, y: event.clientY, desde: encuadre }
  }

  function alArrastrar(event: PointerEvent<HTMLDivElement>) {
    if (!arrastre.current || !cargada) return
    const { x, y, desde } = arrastre.current
    // Mientras se arrastra solo se mueve la vista; se exporta al soltar.
    setEncuadre(limitar({ ...desde, x: desde.x + event.clientX - x, y: desde.y + event.clientY - y },
      cargada.imagen.naturalWidth, cargada.imagen.naturalHeight, LADO))
  }

  function alSoltarPuntero() {
    if (!arrastre.current) return
    arrastre.current = null
    mover(encuadre)
  }

  function alTeclear(event: KeyboardEvent) {
    const paso = event.shiftKey ? 40 : 10
    const delta: Record<string, [number, number]> = {
      ArrowLeft: [paso, 0], ArrowRight: [-paso, 0], ArrowUp: [0, paso], ArrowDown: [0, -paso],
    }
    const d = delta[event.key]
    if (!d) return
    event.preventDefault()
    mover({ ...encuadre, x: encuadre.x + d[0], y: encuadre.y + d[1] }, 250)
  }

  const mensaje = errorLocal ?? error
  const inputArchivo = (
    <input
      ref={input}
      id={idInput}
      type="file"
      accept="image/jpeg,image/png,image/webp"
      className="sr-only"
      tabIndex={-1}
      onChange={(e) => {
        elegir(e.target.files?.[0])
        e.target.value = ''
      }}
    />
  )

  if (cargada) {
    const s = escala(cargada.imagen.naturalWidth, cargada.imagen.naturalHeight, LADO, encuadre.zoom)
    return (
      <div className="space-y-3">
        <div className="flex items-start gap-5">
          <div
            role="img"
            aria-label={`Recorte de la foto de ${nombre || 'la herramienta'}. Arrástrala o usa las flechas para encuadrarla.`}
            tabIndex={0}
            onPointerDown={alPresionar}
            onPointerMove={alArrastrar}
            onPointerUp={alSoltarPuntero}
            onPointerCancel={alSoltarPuntero}
            onKeyDown={alTeclear}
            className="relative shrink-0 cursor-grab touch-none overflow-hidden rounded-card bg-surf2 active:cursor-grabbing"
            style={{ width: LADO, height: LADO }}
          >
            <img
              src={cargada.url}
              alt=""
              draggable={false}
              className="pointer-events-none absolute left-0 top-0 max-w-none select-none"
              style={{
                width: cargada.imagen.naturalWidth * s,
                height: cargada.imagen.naturalHeight * s,
                transform: `translate(${encuadre.x}px, ${encuadre.y}px)`,
              }}
            />
          </div>
          <div className="min-w-0 flex-1 space-y-4 pt-1">
            <p className="flex items-start gap-2 text-xs text-muted">
              <Move size={14} aria-hidden className="mt-px shrink-0" />
              Arrastra la imagen (o usa las flechas) para encuadrarla. Se guarda cuadrada.
            </p>
            <div>
              <label htmlFor={`${idInput}-zoom`} className="mb-1.5 block text-xs font-semibold text-muted">Zoom</label>
              <input
                id={`${idInput}-zoom`}
                type="range"
                min={1}
                max={3}
                step={0.01}
                value={encuadre.zoom}
                onChange={(e) =>
                  mover(conZoom(encuadre, Number(e.target.value), cargada.imagen.naturalWidth, cargada.imagen.naturalHeight, LADO), 250)
                }
                className="w-full accent-acc"
              />
            </div>
            <Button tamano="sm" icono={<RefreshCw size={14} aria-hidden />} onClick={() => input.current?.click()}>
              Elegir otra
            </Button>
            {inputArchivo}
          </div>
        </div>
        {mensaje && <p className="text-xs font-medium text-danger">{mensaje}</p>}
      </div>
    )
  }

  if (actual) {
    return (
      <div className="flex items-center gap-5">
        <div className="w-32">
          <ProductImage src={actual} alt={nombre} />
        </div>
        <div className="space-y-2">
          <Button tamano="sm" icono={<RefreshCw size={14} aria-hidden />} onClick={() => input.current?.click()}>
            Reemplazar foto
          </Button>
          <p className="text-xs text-muted">JPG, PNG o WebP, máx. 5 MB.</p>
          {mensaje && <p className="text-xs font-medium text-danger">{mensaje}</p>}
        </div>
        {inputArchivo}
      </div>
    )
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setArrastrandoArchivo(true)
        }}
        onDragLeave={() => setArrastrandoArchivo(false)}
        onDrop={alSoltar}
        className={cx(
          'transicion flex flex-col items-center justify-center rounded-card px-6 py-8 text-center',
          arrastrandoArchivo ? 'bg-soft ring-2 ring-acc' : 'bg-surf2',
          mensaje && !arrastrandoArchivo && 'ring-2 ring-danger',
        )}
      >
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-soft text-softink">
          <ImagePlus size={26} aria-hidden />
        </span>
        <p className="mt-3 text-sm font-semibold text-ink">Arrastra la foto aquí</p>
        <p id={idAyuda} className="mt-0.5 text-xs text-muted">JPG, PNG o WebP, máx. 5 MB. Se recorta cuadrada.</p>
        <Button tamano="sm" className="mt-4" aria-describedby={idAyuda} onClick={() => input.current?.click()}>
          Elegir archivo
        </Button>
        {inputArchivo}
      </div>
      {mensaje && <p className="mt-1.5 text-xs font-medium text-danger">{mensaje}</p>}
    </div>
  )
}
