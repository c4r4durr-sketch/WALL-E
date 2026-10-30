import {
  ArrowLeftRight,
  BarChart3,
  Boxes,
  CalendarCheck,
  ClipboardList,
  Gauge,
  Hourglass,
  LayoutDashboard,
  PackagePlus,
  ShieldCheck,
  Tag,
  Truck,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { Rol } from '../../shared/types/roles'

// Menú de la barra lateral (docs/DISENO.md, "Navegación"). `roles` repite
// lo que exigen las rutas (router.tsx) y el backend: solo decide qué se
// muestra; un ítem que el rol no puede abrir no aparece, y un grupo que
// queda vacío tampoco.

export interface ItemNav {
  ruta: string
  texto: string
  icono: LucideIcon
  roles?: Rol[]
}

export interface GrupoNav {
  id: string
  texto: string
  items: ItemNav[]
}

const ADMIN_Y_SUPERVISOR = [Rol.ADMINISTRADOR, Rol.SUPERVISOR]

export const PANEL: ItemNav = { ruta: '/', texto: 'Panel', icono: LayoutDashboard }

export const GRUPOS: GrupoNav[] = [
  {
    id: 'inventario',
    texto: 'Inventario',
    items: [
      { ruta: '/catalogo', texto: 'Catálogo', icono: Boxes },
      { ruta: '/movimientos', texto: 'Movimientos', icono: ArrowLeftRight },
      { ruta: '/transferencias', texto: 'Transferencias', icono: Truck },
      { ruta: '/promociones', texto: 'Promociones', icono: Tag },
      { ruta: '/cierre-diario', texto: 'Cierre diario', icono: CalendarCheck, roles: ADMIN_Y_SUPERVISOR },
    ],
  },
  {
    id: 'analisis',
    texto: 'Análisis',
    items: [
      { ruta: '/indicadores', texto: 'Indicadores', icono: Gauge },
      { ruta: '/reposicion', texto: 'Reposición EOQ', icono: PackagePlus },
      { ruta: '/abc', texto: 'Clasificación ABC', icono: BarChart3 },
      { ruta: '/antiguedad', texto: 'Antigüedad del stock', icono: Hourglass, roles: ADMIN_Y_SUPERVISOR },
    ],
  },
  {
    // "Órdenes de compra" se agrega acá cuando exista la pantalla.
    id: 'compras',
    texto: 'Compras',
    items: [{ ruta: '/proveedores', texto: 'Proveedores', icono: ClipboardList }],
  },
  {
    id: 'administracion',
    texto: 'Administración',
    items: [
      { ruta: '/usuarios', texto: 'Cuentas', icono: Users, roles: [Rol.ADMINISTRADOR] },
      { ruta: '/historial', texto: 'Auditoría', icono: ShieldCheck, roles: ADMIN_Y_SUPERVISOR },
    ],
  },
]

export function gruposVisibles(rol: Rol): GrupoNav[] {
  return GRUPOS.map((g) => ({ ...g, items: g.items.filter((i) => !i.roles || i.roles.includes(rol)) })).filter(
    (g) => g.items.length > 0,
  )
}

// /usuarios/nuevo cuenta como "Cuentas"; "/" solo como Panel exacto.
export function estaActiva(ruta: string, actual: string): boolean {
  if (ruta === '/') return actual === '/'
  return actual === ruta || actual.startsWith(`${ruta}/`)
}
