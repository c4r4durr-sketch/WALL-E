// Formatos de la reposición (panel, Reposición EOQ, Productos para pedir).

// "3 cajas (36 u.)".
export function pedidoEnCajas(pedido: number | null, unidadesPorCaja: number): string {
  if (pedido === null) return '—'
  const unidades = Math.round(pedido)
  if (unidadesPorCaja <= 1) return `${unidades} u.`
  const cajas = Math.round(unidades / unidadesPorCaja)
  return `${cajas} ${cajas === 1 ? 'caja' : 'cajas'} (${unidades} u.)`
}
