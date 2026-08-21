export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16">
      <div
        className="size-8 animate-spin rounded-full border-2 border-line border-t-accent"
        role="status"
        aria-label={label ?? 'Загрузка'}
      />
      {label && <p className="text-sm text-ink-soft">{label}…</p>}
    </div>
  )
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-card border border-dashed border-line py-16 text-center">
      <p className="font-serif text-lg text-ink">{title}</p>
      {hint && <p className="mt-2 text-sm text-ink-soft">{hint}</p>}
    </div>
  )
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <p
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
    >
      {message}
    </p>
  )
}
