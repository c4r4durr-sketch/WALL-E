// Validación de formularios: reglas por tipo de campo, política de
// contraseñas, estado del formulario y props para los campos numéricos.
export * as reglas from './reglas'
export { LARGO_TEXTO, DESCUENTO } from './reglas'
export {
  errorPassword,
  errorRepetir,
  nivelPassword,
  requisitosPassword,
  type DatosCuenta,
  type NivelPassword,
  type Requisito,
} from './password'
export { useFormulario, type Errores } from './useFormulario'
export { propsEntero, propsMonto } from './teclado'
