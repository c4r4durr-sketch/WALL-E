import type { InputHTMLAttributes } from 'react'
import { Search } from 'lucide-react'
import { cx } from './cx'

// Buscador en píldora (radio 999) con lupa. La etiqueta accesible es
// obligatoria porque no lleva <label> visible.

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'aria-label'> {
  etiqueta: string
}

export function SearchInput({ etiqueta, className, ...props }: Props) {
  return (
    <div className={cx('relative', className)}>
      <Search size={16} aria-hidden className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
      <input
        type="search"
        aria-label={etiqueta}
        className="transicion h-10 w-full rounded-full bg-surf pl-10 pr-4 text-sm text-ink shadow-sh outline-none placeholder:text-muted focus:ring-2 focus:ring-acc"
        {...props}
      />
    </div>
  )
}
