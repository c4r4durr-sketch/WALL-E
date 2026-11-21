// Política de contraseñas: la misma que AUTH_PASSWORD_VALIDATORS del
// backend (config/settings.py): mínimo 8 caracteres, una mayúscula, una
// minúscula, un número y un símbolo (validador propio
// ComplejidadPasswordValidator) y que no se parezca a los datos de la
// cuenta (UserAttributeSimilarityValidator). Lo único que no se revisa
// acá es la lista de contraseñas comunes de Django: si se usa una, el
// aviso llega del backend debajo del campo.

export const PASSWORD_LARGO_MINIMO = 8

// Datos de la cuenta contra los que se compara (los mismos que Django).
export interface DatosCuenta {
  username?: string
  first_name?: string
  last_name?: string
  email?: string
}

export interface Requisito {
  clave: 'largo' | 'mayuscula' | 'minuscula' | 'numero' | 'simbolo' | 'distinta'
  texto: string
  cumple: boolean
}

// SequenceMatcher.quick_ratio de Python: 2 × (caracteres en común,
// contando repeticiones) / (largo de a + largo de b).
function quickRatio(a: string, b: string): number {
  const cuenta = new Map<string, number>()
  for (const c of b) cuenta.set(c, (cuenta.get(c) ?? 0) + 1)
  let comunes = 0
  for (const c of a) {
    const n = cuenta.get(c) ?? 0
    if (n > 0) {
      comunes++
      cuenta.set(c, n - 1)
    }
  }
  const total = [...a].length + [...b].length
  return total ? (2 * comunes) / total : 1
}

const SIMILITUD_MAXIMA = 0.7

// Igual que UserAttributeSimilarityValidator de Django 5.1: compara con
// cada dato completo y con cada parte separada por símbolos.
export function pareceDatosDeCuenta(password: string, cuenta: DatosCuenta): boolean {
  const clave = password.toLowerCase()
  return Object.values(cuenta).some((valor) => {
    if (!valor) return false
    const minusculas = valor.toLowerCase()
    const partes = [...minusculas.split(/[^\p{L}\p{N}_]+/u), minusculas]
    return partes.some((parte) => {
      const muyDistintas = clave.length >= 10 * parte.length && parte.length < (SIMILITUD_MAXIMA / 2) * clave.length
      return !muyDistintas && quickRatio(clave, parte) >= SIMILITUD_MAXIMA
    })
  })
}

export function requisitosPassword(password: string, cuenta: DatosCuenta): Requisito[] {
  return [
    { clave: 'largo', texto: `Mínimo ${PASSWORD_LARGO_MINIMO} caracteres`, cumple: [...password].length >= PASSWORD_LARGO_MINIMO },
    { clave: 'mayuscula', texto: 'Una mayúscula', cumple: /\p{Lu}/u.test(password) },
    { clave: 'minuscula', texto: 'Una minúscula', cumple: /\p{Ll}/u.test(password) },
    { clave: 'numero', texto: 'Un número', cumple: /\p{N}/u.test(password) },
    { clave: 'simbolo', texto: 'Un símbolo', cumple: /[^\p{L}\p{N}\s]/u.test(password) },
    {
      clave: 'distinta',
      texto: 'Que no se parezca al usuario ni al nombre',
      cumple: password !== '' && !pareceDatosDeCuenta(password, cuenta),
    },
  ]
}

// 0: vacía; 1: Débil; 2: Regular; 3: Buena (ya cumple la política);
// 4: Fuerte (cumple la política y tiene 12 caracteres o más).
export type NivelPassword = 0 | 1 | 2 | 3 | 4

export function nivelPassword(password: string, requisitos: Requisito[]): NivelPassword {
  if (!password) return 0
  if (requisitos.every((r) => r.cumple)) return [...password].length >= 12 ? 4 : 3
  const parecida = requisitos.some((r) => r.clave === 'distinta' && !r.cumple)
  const cumplidos = requisitos.filter((r) => r.clave !== 'distinta' && r.cumple).length
  return !parecida && cumplidos >= 4 ? 2 : 1
}

export function errorPassword(password: string, cuenta: DatosCuenta): string | null {
  if (!password) return 'La contraseña es obligatoria.'
  return requisitosPassword(password, cuenta).every((r) => r.cumple) ? null : 'La contraseña no cumple todos los requisitos.'
}

export function errorRepetir(password: string, repetida: string): string | null {
  if (!repetida) return 'Repite la contraseña.'
  return password === repetida ? null : 'Las contraseñas no coinciden.'
}
