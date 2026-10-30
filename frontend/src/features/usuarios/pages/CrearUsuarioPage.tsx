import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, UserPlus } from 'lucide-react'
import { Aviso, Button, Card, Field, Input, PageHeader, Select, clasesBoton } from '../../../components/ui'
import { Rol } from '../../../shared/types/roles'
import { useSucursales } from '../hooks/useSucursales'
import { useCrearUsuario } from '../hooks/useCrearUsuario'
import { ROL_LABEL } from '../roles'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'

// Alta de una cuenta (HU4), solo Administrador. El login es por nombre de
// usuario; la sucursal es obligatoria salvo para el Administrador.

type FormState = {
  username: string
  password: string
  first_name: string
  last_name: string
  rol: Rol
  sucursal: string
}

type Errores = Partial<Record<keyof FormState, string>>

function validar(form: FormState): Errores {
  const errores: Errores = {}

  if (!form.username.trim()) {
    errores.username = 'El usuario es obligatorio.'
  } else if (form.username.trim().length < 3) {
    errores.username = 'Debe tener al menos 3 caracteres.'
  } else if (/\s/.test(form.username)) {
    errores.username = 'No puede contener espacios.'
  }

  if (!form.password) {
    errores.password = 'La contraseña es obligatoria.'
  } else if (form.password.length < 8) {
    errores.password = 'Debe tener al menos 8 caracteres.'
  }

  if (!form.first_name.trim()) errores.first_name = 'El nombre es obligatorio.'
  if (!form.last_name.trim()) errores.last_name = 'El apellido es obligatorio.'

  if (form.rol !== Rol.ADMINISTRADOR && !form.sucursal) {
    errores.sucursal = 'Selecciona una sucursal.'
  }

  return errores
}

export function CrearUsuarioPage() {
  const { data: sucursales } = useSucursales()
  const { mutate, isPending, error, isSuccess, reset } = useCrearUsuario()

  const [form, setForm] = useState<FormState>({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    rol: Rol.EMPLEADO,
    sucursal: '',
  })
  const [errores, setErrores] = useState<Errores>({})
  // Errores del backend (usuario repetido, contraseña débil...) junto a su
  // campo; los del formulario tienen prioridad mientras se corrigen.
  const erroresServidor = erroresPorCampo(error) as Errores
  const visibles: Errores = { ...erroresServidor, ...errores }
  const errorGeneral =
    error && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(error, 'No se pudo crear la cuenta. Intenta de nuevo.')
      : null

  // Actualiza un campo y limpia su error mientras el usuario escribe
  function setCampo<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (isSuccess) reset()
    if (errores[campo]) {
      setErrores((prev) => ({ ...prev, [campo]: undefined }))
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()

    const erroresNuevos = validar(form)
    setErrores(erroresNuevos)
    if (Object.keys(erroresNuevos).length > 0) return // no envía

    mutate({
      username: form.username.trim(),
      password: form.password,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      rol: form.rol,
      sucursal: form.rol === Rol.ADMINISTRADOR ? null : Number(form.sucursal),
    }, {
      onSuccess: () => setForm((prev) => ({ ...prev, username: '', password: '', first_name: '', last_name: '' })),
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
            <Field etiqueta="Usuario" error={visibles.username}>
              <Input autoComplete="off" value={form.username} onChange={(e) => setCampo('username', e.target.value)} />
            </Field>
            <Field etiqueta="Contraseña" error={visibles.password}>
              <Input type="password" autoComplete="new-password" value={form.password} onChange={(e) => setCampo('password', e.target.value)} />
            </Field>
            <Field etiqueta="Nombre" error={visibles.first_name}>
              <Input value={form.first_name} onChange={(e) => setCampo('first_name', e.target.value)} />
            </Field>
            <Field etiqueta="Apellido" error={visibles.last_name}>
              <Input value={form.last_name} onChange={(e) => setCampo('last_name', e.target.value)} />
            </Field>
            <Field etiqueta="Rol">
              <Select
                value={form.rol}
                onChange={(e) => {
                  const rol = e.target.value as Rol
                  setForm((prev) => ({
                    ...prev,
                    rol,
                    // al pasar a Administrador, la sucursal ya no aplica
                    sucursal: rol === Rol.ADMINISTRADOR ? '' : prev.sucursal,
                  }))
                  setErrores((prev) => ({ ...prev, sucursal: undefined }))
                }}
              >
                {Object.values(Rol).map((rol) => (
                  <option key={rol} value={rol}>{ROL_LABEL[rol]}</option>
                ))}
              </Select>
            </Field>
            {form.rol !== Rol.ADMINISTRADOR && (
              <Field etiqueta="Sucursal" error={visibles.sucursal}>
                <Select value={form.sucursal} onChange={(e) => setCampo('sucursal', e.target.value)}>
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
            <Button type="submit" variante="primary" cargando={isPending} icono={<UserPlus size={16} aria-hidden />}>
              Crear cuenta
            </Button>
          </div>
        </form>
      </Card>
    </>
  )
}
