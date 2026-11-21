import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, UserPlus } from 'lucide-react'
import {
  Aviso,
  Button,
  Card,
  Field,
  Input,
  PageHeader,
  PasswordInput,
  PasswordStrength,
  Select,
  clasesBoton,
} from '../../../components/ui'
import { Rol } from '../../../shared/types/roles'
import { errorPassword, errorRepetir, reglas, useFormulario, type Errores } from '../../../shared/validacion'
import { useSucursales } from '../hooks/useSucursales'
import { useCrearUsuario } from '../hooks/useCrearUsuario'
import { ROL_LABEL } from '../roles'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'

// Alta de una cuenta (HU4), solo Administrador. El login es por nombre de
// usuario; la sucursal es obligatoria salvo para el Administrador. Las
// reglas de cada campo (shared/validacion) son las mismas del backend; el
// backend avisa además si el usuario ya existe o la contraseña es común.

type FormState = {
  username: string
  password: string
  repetir: string
  first_name: string
  last_name: string
  rol: Rol
  sucursal: string
}

const FORM_VACIO: FormState = {
  username: '',
  password: '',
  repetir: '',
  first_name: '',
  last_name: '',
  rol: Rol.EMPLEADO,
  sucursal: '',
}

// Datos con los que la contraseña no se puede parecer (como en Django).
function datosCuenta(form: FormState) {
  return { username: form.username, first_name: form.first_name, last_name: form.last_name }
}

function validar(form: FormState): Errores<FormState> {
  return {
    username: reglas.usuario(form.username),
    first_name: reglas.nombrePersona(form.first_name),
    last_name: reglas.nombrePersona(form.last_name, 'El apellido'),
    password: errorPassword(form.password, datosCuenta(form)),
    repetir: errorRepetir(form.password, form.repetir),
    sucursal: form.rol !== Rol.ADMINISTRADOR && !form.sucursal ? 'Selecciona una sucursal.' : null,
  }
}

export function CrearUsuarioPage() {
  const { data: sucursales } = useSucursales()
  const { mutate, isPending, error, isSuccess, reset } = useCrearUsuario()
  const form = useFormulario<FormState>(FORM_VACIO, validar)
  const { valores } = form
  const erroresServidor = erroresPorCampo(error)
  const errorGeneral =
    error && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(error, 'No se pudo crear la cuenta. Intenta de nuevo.')
      : null

  function setCampo<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    form.cambiar(campo, valor)
    if (isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.enviar()) return

    mutate({
      username: valores.username.trim(),
      password: valores.password,
      first_name: reglas.limpiar(valores.first_name),
      last_name: reglas.limpiar(valores.last_name),
      rol: valores.rol,
      sucursal: valores.rol === Rol.ADMINISTRADOR ? null : Number(valores.sucursal),
    }, {
      onSuccess: () => form.reiniciar({ ...FORM_VACIO, rol: valores.rol, sucursal: valores.sucursal }),
    })
  }

  return (
    <>
      <PageHeader
        migas={['Administración', 'Cuentas', 'Nueva cuenta']}
        titulo="Nueva cuenta"
        subtitulo="La persona entra con su nombre de usuario y esta contraseña."
        acciones={
          <Link to="/usuarios" className={clasesBoton({ variante: 'ghost' })}>
            <ArrowLeft size={16} aria-hidden />
            Volver a cuentas
          </Link>
        }
      />

      <Card className="max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="grid grid-cols-2 gap-4">
            <Field etiqueta="Nombre" obligatorio error={form.error('first_name', erroresServidor)}>
              <Input
                autoComplete="off"
                maxLength={50}
                value={valores.first_name}
                onChange={(e) => setCampo('first_name', e.target.value)}
                onBlur={() => form.tocar('first_name')}
              />
            </Field>
            <Field etiqueta="Apellido" obligatorio error={form.error('last_name', erroresServidor)}>
              <Input
                autoComplete="off"
                maxLength={50}
                value={valores.last_name}
                onChange={(e) => setCampo('last_name', e.target.value)}
                onBlur={() => form.tocar('last_name')}
              />
            </Field>
            <Field
              etiqueta="Usuario"
              obligatorio
              ayuda="De 3 a 30: letras sin tildes, números, punto, guion o guion bajo."
              error={form.error('username', erroresServidor)}
              className="col-span-2"
            >
              <Input
                autoComplete="off"
                maxLength={30}
                value={valores.username}
                onChange={(e) => setCampo('username', e.target.value)}
                onBlur={() => form.tocar('username')}
              />
            </Field>
            <Field etiqueta="Contraseña" obligatorio error={form.error('password', erroresServidor)}>
              <PasswordInput
                autoComplete="new-password"
                value={valores.password}
                onChange={(e) => setCampo('password', e.target.value)}
                onBlur={() => form.tocar('password')}
              />
            </Field>
            <Field etiqueta="Repetir contraseña" obligatorio error={form.error('repetir')}>
              <PasswordInput
                autoComplete="new-password"
                value={valores.repetir}
                onChange={(e) => setCampo('repetir', e.target.value)}
                onBlur={() => form.tocar('repetir')}
              />
            </Field>
            <div className="col-span-2 -mt-1">
              <PasswordStrength password={valores.password} cuenta={datosCuenta(valores)} />
            </div>
            <Field etiqueta="Rol" obligatorio>
              <Select
                value={valores.rol}
                onChange={(e) => {
                  const rol = e.target.value as Rol
                  // al pasar a Administrador, la sucursal ya no aplica
                  form.setValores((prev) => ({ ...prev, rol, sucursal: rol === Rol.ADMINISTRADOR ? '' : prev.sucursal }))
                  if (isSuccess) reset()
                }}
              >
                {Object.values(Rol).map((rol) => (
                  <option key={rol} value={rol}>{ROL_LABEL[rol]}</option>
                ))}
              </Select>
            </Field>
            {valores.rol !== Rol.ADMINISTRADOR && (
              <Field etiqueta="Sucursal" obligatorio error={form.error('sucursal', erroresServidor)}>
                <Select
                  value={valores.sucursal}
                  onChange={(e) => setCampo('sucursal', e.target.value)}
                  onBlur={() => form.tocar('sucursal')}
                >
                  <option value="" disabled>Selecciona una sucursal</option>
                  {sucursales?.map((sucursal) => (
                    <option key={sucursal.id} value={sucursal.id}>{sucursal.nombre}</option>
                  ))}
                </Select>
              </Field>
            )}
          </div>

          {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}
          {isSuccess && <Aviso tono="exito">Cuenta creada correctamente.</Aviso>}

          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              variante="primary"
              cargando={isPending}
              disabled={!form.valido}
              icono={<UserPlus size={16} aria-hidden />}
            >
              Crear cuenta
            </Button>
          </div>
        </form>
      </Card>
    </>
  )
}
