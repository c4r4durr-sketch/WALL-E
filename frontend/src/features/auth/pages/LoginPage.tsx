import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { motion, useReducedMotion } from 'motion/react'
import { LogIn } from 'lucide-react'
import { Aviso, Button, Field, Input, PasswordInput } from '../../../components/ui'
import { reglas, useFormulario } from '../../../shared/validacion'
import { TRANSICION } from '../../../components/ui/movimiento'
import { useLogin } from '../hooks/useLogin'

// Login real (no mockeado): llama a POST /api/token/ vía useLogin, guarda
// el token y redirige a "/" si las credenciales son válidas. Si no, muestra
// el error dentro del formulario (nunca solo en consola). Se entra con el
// nombre de usuario. Acá solo se revisa que usuario y contraseña no estén
// vacíos: el formato no se valida para no dejar afuera a cuentas creadas
// antes de las reglas actuales, y sin barra de seguridad.
export function LoginPage() {
  const form = useFormulario({ username: '', password: '' }, (v) => ({
    username: reglas.obligatorio(v.username, 'Escribe tu usuario.'),
    password: v.password === '' ? 'Escribe tu contraseña.' : null,
  }))
  const { username, password } = form.valores
  const navigate = useNavigate()
  const reducido = useReducedMotion()
  const { mutate, isPending, error } = useLogin()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.enviar()) return
    mutate(
      { username: username.trim(), password },
      { onSuccess: () => navigate('/', { replace: true }) },
    )
  }

  let errorMessage: string | null = null
  if (error) {
    errorMessage =
      isAxiosError(error) && error.response?.status === 401
        ? 'Usuario o contraseña incorrectos.'
        : 'No se pudo conectar con el servidor. Intenta de nuevo.'
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <motion.div
        className="w-full max-w-[400px] rounded-panel bg-surf p-9 shadow-shh"
        initial={reducido ? false : { opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={TRANSICION}
      >
        <span aria-hidden className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-acc text-lg font-bold text-on-acc">
          W
        </span>
        <h1 className="mt-6 text-[28px] font-bold leading-tight tracking-[-0.035em] text-ink">Iniciar sesión</h1>
        <p className="mt-1 text-[13px] font-medium text-muted">Walle-Importaciones · inventario multisucursal</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4" noValidate>
          <Field etiqueta="Usuario" obligatorio error={form.error('username')}>
            <Input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => form.cambiar('username', event.target.value)}
              onBlur={() => form.tocar('username')}
              autoFocus
            />
          </Field>
          <Field etiqueta="Contraseña" obligatorio error={form.error('password')}>
            <PasswordInput
              autoComplete="current-password"
              value={password}
              onChange={(event) => form.cambiar('password', event.target.value)}
              onBlur={() => form.tocar('password')}
            />
          </Field>
          {errorMessage && <Aviso tono="error">{errorMessage}</Aviso>}
          <Button type="submit" variante="primary" cargando={isPending} disabled={!form.valido} icono={<LogIn size={16} aria-hidden />} className="mt-2 w-full">
            Ingresar
          </Button>
        </form>
      </motion.div>
    </main>
  )
}
