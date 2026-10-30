import { useState } from 'react'
import { FileSpreadsheet } from 'lucide-react'
import { Button } from '../../../components/ui'
import { descargarArchivo } from '../../../shared/api/descargar'
import { mensajeDeError } from '../../../shared/api/errores'

// HU25: descarga el reporte que se está viendo como .xlsx, con los mismos
// filtros (el backend aplica los mismos permisos). Botón secundario: la
// acción naranja queda para la pantalla. CA3: si el reporte está vacío se
// avisa y no se genera archivo (el backend también responde 409).

interface Props {
  url: string
  params?: object
  nombre: string
  deshabilitado?: boolean
  vacio?: boolean
}

const AVISO_VACIO = 'El reporte está vacío: no hay nada que exportar.'

export function ExportarExcel({ url, params = {}, nombre, deshabilitado = false, vacio = false }: Props) {
  const [descargando, setDescargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function exportar() {
    if (vacio) {
      setError(AVISO_VACIO)
      return
    }
    setDescargando(true)
    setError(null)
    try {
      await descargarArchivo(url, params, `${nombre}.xlsx`)
    } catch (e) {
      setError(mensajeDeError(e, 'No se pudo generar el Excel. Intenta de nuevo.'))
    } finally {
      setDescargando(false)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        onClick={exportar}
        cargando={descargando}
        disabled={deshabilitado}
        icono={<FileSpreadsheet size={16} aria-hidden />}
      >
        Exportar a Excel
      </Button>
      {error && <p role="alert" className="text-xs font-medium text-danger">{error}</p>}
    </div>
  )
}
