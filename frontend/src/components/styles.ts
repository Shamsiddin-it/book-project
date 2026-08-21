type ButtonVariant = 'mint' | 'outline' | 'ink'

const BUTTON_STYLES: Record<ButtonVariant, string> = {
  mint: 'bg-mint text-white hover:bg-mint/90',
  outline: 'border border-ink/20 text-ink hover:border-ink/50',
  ink: 'bg-ink text-cream hover:bg-ink/90',
}

/** Кнопка-пилюля из макета. Живёт отдельно от компонентов ради Fast Refresh. */
export function pillClass(variant: ButtonVariant = 'mint', extra = '') {
  return [
    'inline-flex items-center justify-center rounded-pill px-5 py-2.5',
    'text-sm font-semibold transition disabled:opacity-50',
    BUTTON_STYLES[variant],
    extra,
  ].join(' ')
}
