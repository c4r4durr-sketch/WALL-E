// Página de login. Formulario intencionalmente mínimo: existe para validar
// el flujo técnico (llamada a POST /api/token/ vía useLogin) sin implementar
// todavía las reglas de UX (validación, manejo de errores, guardar sesión,
// redirección según rol).
export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="mb-4 text-xl font-semibold text-slate-800">Iniciar sesión</h1>
        <p className="text-sm text-slate-500">
          Formulario pendiente de implementar (feature: auth).
        </p>
      </div>
    </div>
  )
}
