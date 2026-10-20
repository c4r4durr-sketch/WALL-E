import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, KeyRound, Pencil, UserCheck, UserPlus, UserX } from 'lucide-react'
import { getSession } from '../../auth/session'
import { mensajeDeError } from '../../../shared/api/errores'
import { EditarUsuarioForm } from '../components/EditarUsuarioForm'
import { RestablecerPasswordForm } from '../components/RestablecerPasswordForm'
import { useEditarUsuario, useUsuarios } from '../hooks/useUsuarios'
import { ROL_LABEL } from '../roles'
import type { Usuario } from '../api/usuariosApi'

// Cuentas de usuario (HU3/HU4/HU5), solo Administrador (la ruta tiene
// RequireRol y el backend responde 403 a otros roles). Por cuenta: editar,
// restablecer la contraseña y desactivar/activar. No se eliminan cuentas:
// quedan referenciadas por movimientos y el historial.

type Panel = { tipo: 'editar' | 'password'; usuario: Usuario } | null

const COLUMNAS = 6

export function UsuariosPage() {
  const session = getSession()
  const { data: usuarios, isLoading, isError, refetch } = useUsuarios()
  const cambiarEstado = useEditarUsuario()
  const [panel, setPanel] = useState<Panel>(null)
  const [confirmandoId, setConfirmandoId] = useState<number | null>(null)

  function abrir(tipo: 'editar' | 'password', usuario: Usuario) {
    setPanel({ tipo, usuario })
    setConfirmandoId(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function activar(usuario: Usuario, activo: boolean) {
    cambiarEstado.mutate(
      { id: usuario.id, is_active: activo },
      { onSettled: () => setConfirmandoId(null) },
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:underline">
              <ArrowLeft size={14} aria-hidden />
              Volver
            </Link>
            <h1 className="mt-2 text-xl font-semibold text-slate-800">Cuentas de usuario</h1>
          </div>
          <Link
            to="/usuarios/nuevo"
            className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            <UserPlus size={16} aria-hidden />
            Nueva cuenta
          </Link>
        </div>

        {panel?.tipo === 'editar' && (
          <EditarUsuarioForm key={panel.usuario.id} usuario={panel.usuario} onTerminar={() => setPanel(null)} />
        )}
        {panel?.tipo === 'password' && (
          <RestablecerPasswordForm key={panel.usuario.id} usuario={panel.usuario} onTerminar={() => setPanel(null)} />
        )}

        {cambiarEstado.isError && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mensajeDeError(cambiarEstado.error, 'No se pudo cambiar el estado de la cuenta.')}
          </p>
        )}

        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="px-3 py-2">Usuario</th>
                <th className="px-3 py-2">Nombre</th>
                <th className="px-3 py-2">Rol</th>
                <th className="px-3 py-2">Sucursal</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={COLUMNAS} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={COLUMNAS} className="px-3 py-4 text-center text-red-600">
                    No se pudieron cargar las cuentas.{' '}
                    <button type="button" onClick={() => refetch()} className="font-medium underline">Reintentar</button>
                  </td>
                </tr>
              )}
              {usuarios?.length === 0 && (
                <tr><td colSpan={COLUMNAS} className="px-3 py-4 text-center text-slate-500">No hay cuentas registradas.</td></tr>
              )}
              {usuarios?.map((u) => {
                const esMiCuenta = session !== null && String(u.id) === String(session.user_id)
                const seleccionado = panel?.usuario.id === u.id
                return (
                  <tr key={u.id} className={`border-t border-slate-100 ${seleccionado ? 'bg-blue-50' : ''} ${u.is_active ? '' : 'text-slate-400'}`}>
                    <td className="px-3 py-2 font-medium">
                      {u.username}
                      {esMiCuenta && <span className="ml-2 text-xs font-normal text-slate-500">(tú)</span>}
                    </td>
                    <td className="px-3 py-2">{`${u.first_name} ${u.last_name}`.trim() || <span className="text-slate-400">—</span>}</td>
                    <td className="px-3 py-2">{ROL_LABEL[u.rol]}</td>
                    <td className="px-3 py-2">{u.sucursal_nombre ?? <span className="text-slate-400">—</span>}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          u.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'
                        }`}
                      >
                        {u.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-right">
                      {confirmandoId === u.id ? (
                        <span className="inline-flex items-center gap-2">
                          <span className="text-slate-600">¿Desactivar? No podrá iniciar sesión.</span>
                          <button
                            type="button"
                            onClick={() => activar(u, false)}
                            disabled={cambiarEstado.isPending}
                            className="font-medium text-red-600 hover:underline disabled:opacity-50"
                          >
                            Sí
                          </button>
                          <button type="button" onClick={() => setConfirmandoId(null)} className="font-medium text-slate-600 hover:underline">
                            No
                          </button>
                        </span>
                      ) : (
                        <span className="inline-flex gap-1">
                          <BotonIcono titulo="Editar" onClick={() => abrir('editar', u)}>
                            <Pencil size={16} aria-hidden />
                          </BotonIcono>
                          <BotonIcono titulo="Restablecer contraseña" onClick={() => abrir('password', u)}>
                            <KeyRound size={16} aria-hidden />
                          </BotonIcono>
                          {/* Nadie se desactiva a sí mismo (el backend también lo impide). */}
                          {!esMiCuenta && u.is_active && (
                            <BotonIcono
                              titulo="Desactivar"
                              peligro
                              onClick={() => {
                                cambiarEstado.reset()
                                setConfirmandoId(u.id)
                              }}
                            >
                              <UserX size={16} aria-hidden />
                            </BotonIcono>
                          )}
                          {!u.is_active && (
                            <BotonIcono titulo="Activar" onClick={() => activar(u, true)} disabled={cambiarEstado.isPending}>
                              <UserCheck size={16} aria-hidden />
                            </BotonIcono>
                          )}
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

interface BotonIconoProps {
  titulo: string
  onClick: () => void
  children: ReactNode
  peligro?: boolean
  disabled?: boolean
}

// Botón solo con icono: `title` muestra el texto al pasar el mouse y
// `aria-label` lo lee el lector de pantalla.
function BotonIcono({ titulo, onClick, children, peligro = false, disabled = false }: BotonIconoProps) {
  return (
    <button
      type="button"
      title={titulo}
      aria-label={titulo}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-md p-1.5 hover:bg-slate-100 disabled:opacity-50 ${peligro ? 'text-red-600' : 'text-slate-600'}`}
    >
      {children}
    </button>
  )
}
