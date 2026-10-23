// Une clases de Tailwind ignorando las vacías o condicionales en false.
export function cx(...clases: Array<string | false | null | undefined>): string {
  return clases.filter(Boolean).join(' ')
}
