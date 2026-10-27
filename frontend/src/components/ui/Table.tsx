import type { HTMLAttributes, ReactNode, TdHTMLAttributes, ThHTMLAttributes } from 'react'
import { cx } from './cx'

// Tabla (docs/DISENO.md): sin líneas verticales, filas de 56 px con hover
// suave en --surf2, cabecera de 12 px en --muted. Va dentro de una Card
// sin padding; nunca lleva vidrio.

export function Table({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className="overflow-x-auto">
      <table className={cx('w-full border-collapse text-left text-sm', className)}>{children}</table>
    </div>
  )
}

export function THead({ children }: { children: ReactNode }) {
  return <thead className="text-xs font-semibold text-muted">{children}</thead>
}

export function Th({ className, numerico = false, ...props }: ThHTMLAttributes<HTMLTableCellElement> & { numerico?: boolean }) {
  return (
    <th
      scope="col"
      className={cx('h-11 whitespace-nowrap px-4 font-semibold first:pl-6 last:pr-6', numerico && 'text-right', className)}
      {...props}
    />
  )
}

export function Tr({ className, interactiva = false, seleccionada = false, ...props }: HTMLAttributes<HTMLTableRowElement> & {
  interactiva?: boolean
  seleccionada?: boolean
}) {
  return (
    <tr
      className={cx(
        'transicion h-14 border-t border-line',
        interactiva && 'cursor-pointer',
        seleccionada ? 'bg-soft' : 'hover:bg-surf2',
        className,
      )}
      {...props}
    />
  )
}

export function Td({ className, numerico = false, ...props }: TdHTMLAttributes<HTMLTableCellElement> & { numerico?: boolean }) {
  return (
    <td
      className={cx('px-4 py-2 align-middle first:pl-6 last:pr-6', numerico && 'text-right tabular-nums', className)}
      {...props}
    />
  )
}
