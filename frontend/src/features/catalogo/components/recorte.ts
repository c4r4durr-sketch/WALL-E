// Cálculos del recorte cuadrado de la foto (sin React, para que el
// componente quede simple). La imagen se muestra "cubriendo" el visor
// cuadrado; el usuario la mueve y la amplía, y se exporta lo que queda
// dentro del visor.

export const TIPOS_ACEPTADOS = ['image/jpeg', 'image/png', 'image/webp']
export const TAMANO_MAXIMO = 5 * 1024 * 1024
// Lado de la foto que se sube: suficiente para tarjetas grandes y liviano.
const LADO_SALIDA = 1024

export interface Encuadre {
  zoom: number // 1 = la imagen justo cubre el visor
  x: number // desplazamiento en px del visor (≤ 0)
  y: number
}

export function validarArchivo(archivo: File): string | null {
  if (!TIPOS_ACEPTADOS.includes(archivo.type)) return 'La foto debe ser JPG, PNG o WebP.'
  if (archivo.size > TAMANO_MAXIMO) return 'La foto no puede pesar más de 5 MB.'
  return null
}

// Escala con la que la imagen cubre el visor con el zoom dado.
export function escala(ancho: number, alto: number, lado: number, zoom: number): number {
  return (lado / Math.min(ancho, alto)) * zoom
}

// Mantiene la imagen cubriendo todo el visor (sin bordes vacíos).
export function limitar(e: Encuadre, ancho: number, alto: number, lado: number): Encuadre {
  const s = escala(ancho, alto, lado, e.zoom)
  const minX = lado - ancho * s
  const minY = lado - alto * s
  return { zoom: e.zoom, x: Math.min(0, Math.max(minX, e.x)), y: Math.min(0, Math.max(minY, e.y)) }
}

// Encuadre inicial: centrado, sin zoom.
export function centrado(ancho: number, alto: number, lado: number): Encuadre {
  const s = escala(ancho, alto, lado, 1)
  return { zoom: 1, x: (lado - ancho * s) / 2, y: (lado - alto * s) / 2 }
}

// Cambia el zoom manteniendo fijo el centro del visor.
export function conZoom(e: Encuadre, zoom: number, ancho: number, alto: number, lado: number): Encuadre {
  const antes = escala(ancho, alto, lado, e.zoom)
  const despues = escala(ancho, alto, lado, zoom)
  const centroX = (lado / 2 - e.x) / antes
  const centroY = (lado / 2 - e.y) / antes
  return limitar({ zoom, x: lado / 2 - centroX * despues, y: lado / 2 - centroY * despues }, ancho, alto, lado)
}

// Dibuja el recorte en un canvas cuadrado y lo devuelve como JPEG.
export async function exportarRecorte(imagen: HTMLImageElement, e: Encuadre, lado: number): Promise<Blob> {
  const s = escala(imagen.naturalWidth, imagen.naturalHeight, lado, e.zoom)
  const canvas = document.createElement('canvas')
  canvas.width = LADO_SALIDA
  canvas.height = LADO_SALIDA
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('El navegador no permite recortar la imagen.')
  // Fondo blanco: un PNG con transparencia no queda negro al pasar a JPEG.
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, LADO_SALIDA, LADO_SALIDA)
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(imagen, -e.x / s, -e.y / s, lado / s, lado / s, 0, 0, LADO_SALIDA, LADO_SALIDA)
  return new Promise((resolver, rechazar) =>
    canvas.toBlob((blob) => (blob ? resolver(blob) : rechazar(new Error('No se pudo recortar la imagen.'))), 'image/jpeg', 0.9),
  )
}
