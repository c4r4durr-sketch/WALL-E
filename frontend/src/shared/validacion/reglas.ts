// Reglas de formato de todos los formularios, en un solo lugar. Cada una
// devuelve el mensaje de error (en español) o null si el valor es válido.
// Son las mismas que aplica el backend en backend/apps/comun/reglas.py (y
// en los serializers): si cambia una, cambia la otra. El backend siempre
// vuelve a validar; acá es para avisar al instante.

export type ErrorCampo = string | null

export const LARGO_TEXTO = 255
export const NOMBRE_PERSONA = { min: 2, max: 50 }
export const USUARIO = { min: 3, max: 30 }
export const TELEFONO_DIGITOS = { min: 7, max: 15 }
export const CODIGO_MAX = 30
export const DESCUENTO = { min: 1, max: 90 }

// Quita los espacios del inicio y del final y deja uno solo entre
// palabras (igual que el backend antes de guardar).
export function limpiar(valor: string): string {
  return valor.trim().replace(/\s+/g, ' ')
}

export function obligatorio(valor: string, mensaje: string): ErrorCampo {
  return limpiar(valor) === '' ? mensaje : null
}

// Nombres y apellidos de personas: letras (con tildes y ñ) separadas por
// un espacio, un apóstrofo o un guion. "María José", "O'Brien".
const NOMBRE = /^\p{L}+(?:[ '’-]\p{L}+)*$/u

export function nombrePersona(valor: string, etiqueta = 'El nombre'): ErrorCampo {
  const v = limpiar(valor)
  if (!v) return `${etiqueta} es obligatorio.`
  if (v.length < NOMBRE_PERSONA.min || v.length > NOMBRE_PERSONA.max) {
    return `Debe tener de ${NOMBRE_PERSONA.min} a ${NOMBRE_PERSONA.max} caracteres.`
  }
  if (!NOMBRE.test(v)) return 'Solo letras, espacios, apóstrofo y guion (sin números ni símbolos).'
  return null
}

// Usuario: letras sin tildes, números, punto, guion y guion bajo. Que no
// esté repetido lo avisa el backend.
export function usuario(valor: string): ErrorCampo {
  const v = valor.trim()
  if (!v) return 'El usuario es obligatorio.'
  if (v.length < USUARIO.min || v.length > USUARIO.max) {
    return `Debe tener de ${USUARIO.min} a ${USUARIO.max} caracteres.`
  }
  if (!/^[A-Za-z0-9._-]+$/.test(v)) return 'Solo letras sin tildes, números, punto, guion y guion bajo (sin espacios).'
  return null
}

export function telefono(valor: string): ErrorCampo {
  const v = valor.trim()
  if (!v) return 'El teléfono es obligatorio.'
  const digitos = v.replace(/\D/g, '').length
  if (!/^\+?[\d -]+$/.test(v) || digitos < TELEFONO_DIGITOS.min || digitos > TELEFONO_DIGITOS.max) {
    return `De ${TELEFONO_DIGITOS.min} a ${TELEFONO_DIGITOS.max} dígitos; solo números, espacios, guiones y + al inicio.`
  }
  return null
}

export function email(valor: string, { requerido = false } = {}): ErrorCampo {
  const v = valor.trim()
  if (!v) return requerido ? 'El correo es obligatorio.' : null
  if (v.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Correo no válido.'
  return null
}

// El código va en mayúsculas (el campo las pone solo al escribir).
export function codigoHerramienta(valor: string): ErrorCampo {
  const v = valor.trim().toUpperCase()
  if (!v) return 'El código es obligatorio.'
  if (v.length > CODIGO_MAX) return `No puede tener más de ${CODIGO_MAX} caracteres.`
  if (!/^[A-Z0-9]+(?:-[A-Z0-9]+)*$/.test(v)) return 'Solo letras, números y guiones entre ellos (sin espacios).'
  return null
}

interface OpcionesEntero {
  min?: number
  max?: number
  requerido?: boolean
  // Mensaje si está vacío y es obligatorio.
  vacio?: string
}

// Enteros: sin decimales, sin signo y sin la "e" de la notación científica.
export function entero(valor: string, { min = 1, max, requerido = true, vacio = 'La cantidad es obligatoria.' }: OpcionesEntero = {}): ErrorCampo {
  const v = valor.trim()
  if (!v) return requerido ? vacio : null
  if (!/^\d+$/.test(v)) return 'Debe ser un número entero, sin decimales.'
  const n = Number(v)
  if (n < min) return min === 1 ? 'Debe ser mayor que 0.' : `Debe ser mayor o igual que ${min}.`
  if (max !== undefined && n > max) return `Debe ser menor o igual que ${max}.`
  return null
}

// Costos y montos: mayor que 0, con punto y hasta 2 decimales (el
// backend guarda hasta 12 dígitos en total).
export function monto(valor: string, { requerido = false, vacio = 'El monto es obligatorio.' } = {}): ErrorCampo {
  const v = valor.trim()
  if (!v) return requerido ? vacio : null
  if (!/^\d+(\.\d+)?$/.test(v)) return 'Debe ser un número (con punto para los decimales).'
  if (!/^\d+(\.\d{1,2})?$/.test(v)) return 'Hasta 2 decimales.'
  if (!(Number(v) > 0)) return 'Debe ser mayor que 0.'
  if (Number(v) >= 1e10) return 'El monto es demasiado grande.'
  return null
}

// Textos libres (motivos, observaciones, nombres de cosas).
export function texto(valor: string, { etiqueta = 'El motivo', requerido = false, max = LARGO_TEXTO, min = 0 } = {}): ErrorCampo {
  const v = limpiar(valor)
  if (!v) return requerido ? `${etiqueta} es obligatorio.` : null
  if (v.length < min) return `Debe tener al menos ${min} caracteres.`
  if (v.length > max) return `No puede tener más de ${max} caracteres.`
  return null
}

// Fechas AAAA-MM-DD (el formato de <input type="date">): se comparan
// como texto.
export function fechaNoFutura(fecha: string, hoy: string): ErrorCampo {
  return fecha && fecha > hoy ? 'No puede ser posterior a hoy.' : null
}

export function fechaDesde(fecha: string, minimo: string, mensaje: string): ErrorCampo {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) return 'Elige una fecha.'
  return fecha < minimo ? mensaje : null
}

export function rangoFechas(desde: string, hasta: string): ErrorCampo {
  return desde && hasta && hasta < desde ? '"Hasta" no puede ser anterior a "Desde".' : null
}
