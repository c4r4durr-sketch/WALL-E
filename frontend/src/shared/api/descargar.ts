import { isAxiosError } from 'axios'
import { httpClient } from './httpClient'

// Descarga un archivo de la API (HU25: reportes en Excel) con el token de
// la sesión, que un <a href> no mandaría. El nombre lo pone el backend en
// Content-Disposition. Si la API responde con error, el cuerpo llega como
// Blob: se convierte al JSON de siempre para que mensajeDeError lo lea.
export async function descargarArchivo(url: string, params: object, nombrePorDefecto: string): Promise<void> {
  try {
    const respuesta = await httpClient.get<Blob>(url, { params, responseType: 'blob' })
    const disposicion = String(respuesta.headers['content-disposition'] ?? '')
    const nombre = /filename="?([^"]+)"?/.exec(disposicion)?.[1] ?? nombrePorDefecto
    const enlace = document.createElement('a')
    enlace.href = URL.createObjectURL(respuesta.data)
    enlace.download = nombre
    enlace.click()
    // Se libera después: revocarlo en el mismo tick puede cortar la descarga.
    setTimeout(() => URL.revokeObjectURL(enlace.href), 0)
  } catch (error) {
    if (isAxiosError(error) && error.response?.data instanceof Blob) {
      try {
        error.response.data = JSON.parse(await error.response.data.text())
      } catch {
        // No era JSON: queda el mensaje por defecto.
      }
    }
    throw error
  }
}
