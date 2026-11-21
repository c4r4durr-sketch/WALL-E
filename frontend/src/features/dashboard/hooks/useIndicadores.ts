import { useQuery } from '@tanstack/react-query'
import {
  obtenerClasificacionABC,
  obtenerEOQ,
  obtenerEOQPorSucursal,
  obtenerProductosParaPedir,
  obtenerROP,
} from '../api/indicadoresApi'

export function useClasificacionABC() {
  return useQuery({ queryKey: ['indicadores', 'abc'], queryFn: obtenerClasificacionABC })
}

// EOQ y ROP de una herramienta; sin herramienta elegida no se consulta.
export function useEOQ(herramientaId: number | null) {
  return useQuery({
    queryKey: ['indicadores', 'eoq', herramientaId],
    queryFn: () => obtenerEOQ(herramientaId!),
    enabled: herramientaId !== null,
  })
}

export function useROP(herramientaId: number | null) {
  return useQuery({
    queryKey: ['indicadores', 'rop', herramientaId],
    queryFn: () => obtenerROP(herramientaId!),
    enabled: herramientaId !== null,
  })
}

export function useEOQPorSucursal(herramientaId: number | null) {
  return useQuery({
    queryKey: ['indicadores', 'eoq-sucursales', herramientaId],
    queryFn: () => obtenerEOQPorSucursal(herramientaId!),
    enabled: herramientaId !== null,
  })
}

// null = todas las sucursales activas.
export function useProductosParaPedir(sucursal: number | null) {
  return useQuery({
    queryKey: ['indicadores', 'productos-para-pedir', sucursal],
    queryFn: () => obtenerProductosParaPedir(sucursal),
  })
}
