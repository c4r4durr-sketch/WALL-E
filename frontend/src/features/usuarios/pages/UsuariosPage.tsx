import { useState } from 'react'
import { Link } from 'react-router-dom'
import { KeyRound, Pencil, UserCheck, UserPlus, Users, UserX } from 'lucide-react'
import {
  Aviso,
  Badge,
  Button,
  Card,
  ConfirmModal,
  EmptyState,
  IconButton,
  PageHeader,
  SidePanel,
  SkeletonFilas,
  Table,
  THead,
  Td,
  Th,
  Tr,
  clasesBoton,
  cx,
} from '../../../components/ui'
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

type Panel = { tipo: 'editar' | 'password'; usuario: Usuario; clave: number }

export function UsuariosPage() {
  const session = getSession()
  const { data: usuarios, isLoading, isError, refetch } = useUsuarios()
  const cambiarEstado = useEditarUsuario()
  // El contenido del panel se conserva mientras se cierra (animación).
  const [panel, setPanel] = useState<Panel | null>(null)
  const [panelAbierto, setPanelAbierto] = useState(false)
  const [porDesactivar, setPorDesactivar] = useState<Usuario | null>(null)

  function abrir(tipo: Panel['tipo'], usuario: Usuario) {
    setPanel((anterior) => ({ tipo, usuario, clave: (anterior?.clave ?? 0) + 1 }))
    setPanelAbierto(true)
  }

  function activar(usuario: Usuario, activo: boolean) {
    cambiarEstado.mutate({ id: usuario.id, is_active: activo }, { onSuccess: () => setPorDesactivar(null) })
  }

  return (
    <>
      <PageHeader
        migas={['Administración', 'Cuentas']}
        titulo="Cuentas"
        subtitulo="Quién entra al sistema, con qué rol y en qué sucursal."
        acciones={
          <Link to="/usuarios/nuevo" className={clasesBoton({ variante: 'primary' })}>
            <UserPlus size={16} aria-hidden />
            Nueva cuenta
          </Link>
        }
      />

      {cambiarEstado.isError && !porDesactivar && (
        <Aviso tono="error">{mensajeDeError(cambiarEstado.error, 'No se pudo cambiar el estado de la cuenta.')}</Aviso>
      )}
      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudieron cargar las cuentas.
        </Aviso>
      )}

      <Card sinPadding className="overflow-hidden">
        {isLoading && <SkeletonFilas filas={5} columnas={5} />}
        {usuarios?.length === 0 && (
          <EmptyState icono={Users} titulo="No hay cuentas registradas" ayuda="Crea la primera cuenta para que alguien pueda entrar." />
        )}
        {usuarios && usuarios.length > 0 && (
          <Table>
            <THead>
              <tr>
                <Th>Usuario</Th>
                <Th>Nombre</Th>
                <Th>Rol</Th>
                <Th>Sucursal</Th>
                <Th>Estado</Th>
                <Th><span className="sr-only">Acciones</span></Th>
              </tr>
            </THead>
            <tbody>
              {usuarios.map((u) => {
                const esMiCuenta = session !== null && String(u.id) === String(session.user_id)
                return (
                  <Tr key={u.id} className={cx(!u.is_active && 'text-muted')}>
                    <Td className="font-semibold">
                      {u.username}
                      {esMiCuenta && <span className="ml-2 text-xs font-medium text-muted">(tú)</span>}
                    </Td>
                    <Td>{`${u.first_name} ${u.last_name}`.trim() || <span className="text-muted">—</span>}</Td>
                    <Td>{ROL_LABEL[u.rol]}</Td>
                    <Td>{u.sucursal_nombre ?? <span className="text-muted">—</span>}</Td>
                    <Td><Badge tono={u.is_active ? 'ok' : 'neutral'}>{u.is_active ? 'Activa' : 'Inactiva'}</Badge></Td>
                    <Td>
                      <div className="flex justify-end gap-0.5">
                        <IconButton etiqueta={`Editar ${u.username}`} onClick={() => abrir('editar', u)}>
                          <Pencil size={17} aria-hidden />
                        </IconButton>
                        <IconButton etiqueta={`Restablecer contraseña de ${u.username}`} onClick={() => abrir('password', u)}>
                          <KeyRound size={17} aria-hidden />
                        </IconButton>
                        {/* Nadie se desactiva a sí mismo (el backend también lo impide). */}
                        {!esMiCuenta && u.is_active && (
                          <IconButton
                            etiqueta={`Desactivar ${u.username}`}
                            peligro
                            onClick={() => {
                              cambiarEstado.reset()
                              setPorDesactivar(u)
                            }}
                          >
                            <UserX size={17} aria-hidden />
                          </IconButton>
                        )}
                        {!u.is_active && (
                          <IconButton
                            etiqueta={`Activar ${u.username}`}
                            disabled={cambiarEstado.isPending}
                            onClick={() => activar(u, true)}
                          >
                            <UserCheck size={17} aria-hidden />
                          </IconButton>
                        )}
                      </div>
                    </Td>
                  </Tr>
                )
              })}
            </tbody>
          </Table>
        )}
      </Card>

      <SidePanel
        abierto={panelAbierto}
        onCerrar={() => setPanelAbierto(false)}
        titulo={panel?.tipo === 'password' ? 'Restablecer contraseña' : 'Editar cuenta'}
        descripcion={panel?.usuario.username}
      >
        {panel?.tipo === 'editar' && (
          <EditarUsuarioForm key={panel.clave} usuario={panel.usuario} onTerminar={() => setPanelAbierto(false)} />
        )}
        {panel?.tipo === 'password' && (
          <RestablecerPasswordForm key={panel.clave} usuario={panel.usuario} onTerminar={() => setPanelAbierto(false)} />
        )}
      </SidePanel>

      <ConfirmModal
        abierto={porDesactivar !== null}
        onCerrar={() => setPorDesactivar(null)}
        onConfirmar={() => porDesactivar && activar(porDesactivar, false)}
        titulo="¿Desactivar la cuenta?"
        textoConfirmar="Desactivar"
        cargando={cambiarEstado.isPending}
        error={cambiarEstado.isError ? mensajeDeError(cambiarEstado.error, 'No se pudo desactivar la cuenta.') : null}
      >
        {porDesactivar && (
          <>
            <strong className="font-semibold text-ink">{porDesactivar.username}</strong> no podrá iniciar sesión. Su historial
            se conserva y la cuenta se puede volver a activar.
          </>
        )}
      </ConfirmModal>
    </>
  )
}
