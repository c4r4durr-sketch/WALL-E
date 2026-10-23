import { StatCard } from '../../../components/ui'

// Tarjeta de indicador del panel y del cierre diario: etiqueta, número y
// una nota opcional. Si el indicador es una alerta activa, se marca con
// ícono + texto ("Requiere atención"), nunca solo con color.

interface Props {
  etiqueta: string
  valor: number
  nota?: string
  alerta?: boolean
}

export function StatTile({ etiqueta, valor, nota, alerta = false }: Props) {
  return <StatCard etiqueta={etiqueta} valor={valor} nota={nota} alerta={alerta} />
}
