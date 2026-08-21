import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

/**
 * Логотип BOOKLY: две буквы «O» заменены розовыми кружками — в макете они
 * читаются как очки. Собран из текста, а не из картинки, чтобы масштабировался
 * вместе со шрифтом и оставался доступным для скринридера.
 */
export function Logo({ className = '' }: { className?: string }) {
  return (
    <Link
      to="/"
      aria-label="BOOKLY — на главную"
      className={`flex items-center gap-[0.1em] text-2xl display-title text-ink ${className}`}
    >
      <span aria-hidden>B</span>
      <span aria-hidden className="flex items-center gap-[0.12em] px-[0.08em]">
        <span className="block size-[0.42em] rounded-full bg-blush" />
        <span className="block size-[0.42em] rounded-full bg-blush" />
      </span>
      <span aria-hidden>KLY</span>
    </Link>
  )
}

/** Заголовок раздела: по центру, с линиями по бокам — как в макете. */
export function SectionHeading({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-6 py-2">
      <span className="h-px flex-1 bg-ink/25" />
      <h2 className="tracked text-center text-lg font-bold text-ink sm:text-xl">{children}</h2>
      <span className="h-px flex-1 bg-ink/25" />
    </div>
  )
}

/**
 * Оценка звёздами. Половинки не рисуем — в макете их нет.
 *
 * value допускает undefined намеренно: если бэкенд однажды перестанет
 * присылать поле, блок должен показать «нет оценок», а не уронить страницу
 * целиком на toFixed. Так уже случалось с выдачей рекомендаций.
 */
export function Stars({
  value,
  count,
}: {
  value: number | null | undefined
  count?: number
}) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return <span className="text-xs text-ink-faint">Нет оценок</span>
  }

  const filled = Math.round(value)
  return (
    <span
      className="flex items-center gap-1"
      aria-label={`Оценка ${value.toFixed(1)} из 5`}
    >
      <span className="text-sm font-semibold text-ink">{value.toFixed(1)}</span>
      <span aria-hidden className="text-blush">
        {'★★★★★'.slice(0, filled)}
        <span className="text-ink-faint/40">{'★★★★★'.slice(filled)}</span>
      </span>
      {count !== undefined && count > 0 && (
        <span className="text-xs text-ink-faint">({count})</span>
      )}
    </span>
  )
}

export function Price({ value, oldValue }: { value: string | number; oldValue?: string | null }) {
  const amount = Number(value)
  const previous = oldValue === undefined || oldValue === null ? null : Number(oldValue)

  const format = (input: number) =>
    Number.isNaN(input) ? String(input) : `${input.toLocaleString('ru-RU')} ₽`

  return (
    <span className="flex items-baseline gap-2">
      <span className="font-bold text-ink">{format(amount)}</span>
      {previous !== null && (
        <span className="text-xs text-ink-faint line-through">{format(previous)}</span>
      )}
    </span>
  )
}

export function DiscountBadge({ percent }: { percent: number }) {
  return (
    <span className="rounded-pill bg-blush px-2 py-0.5 text-xs font-bold text-white">
      −{percent}%
    </span>
  )
}

/** Мягкое розовое пятно из макета. Чисто декоративное. */
export function Blob({ className = '' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 160"
      aria-hidden
      className={`pointer-events-none absolute ${className}`}
    >
      <path
        fill="var(--color-blush)"
        d="M167 21c18 17 24 47 15 70-9 24-33 41-59 50-27 9-56 9-77-4C25 124 11 98 14 74 17 50 37 28 62 17c25-11 55-9 77 4z"
      />
    </svg>
  )
}
