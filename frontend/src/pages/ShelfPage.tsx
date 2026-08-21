import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { fetchShelf, removeFromShelf, updateShelfItem } from '../api/endpoints'
import type { ShelfStatus } from '../api/types'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'

const TABS: { value: ShelfStatus | ''; label: string }[] = [
  { value: '', label: 'Все' },
  { value: 'reading', label: 'Читаю' },
  { value: 'read', label: 'Прочитано' },
  { value: 'want', label: 'Хочу прочитать' },
]

export function ShelfPage() {
  const [status, setStatus] = useState<ShelfStatus | ''>('')
  const queryClient = useQueryClient()

  const shelfQuery = useQuery({
    queryKey: ['shelf', status],
    queryFn: () => fetchShelf(status ? { status } : {}),
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['shelf'] })
  }

  const statusMutation = useMutation({
    mutationFn: ({ id, next }: { id: number; next: ShelfStatus }) =>
      updateShelfItem(id, { status: next }),
    onSuccess: invalidate,
  })

  const removeMutation = useMutation({
    mutationFn: (id: number) => removeFromShelf(id),
    onSuccess: invalidate,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-3xl text-ink">Моя полка</h1>
        <p className="mt-1 text-ink-soft">Купленное, прочитанное и отложенное.</p>
      </div>

      <div className="flex flex-wrap gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            onClick={() => setStatus(tab.value)}
            className={[
              'rounded-full px-3 py-1.5 text-sm transition',
              status === tab.value
                ? 'bg-ink text-paper'
                : 'border border-line text-ink-soft hover:text-ink',
            ].join(' ')}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {shelfQuery.isError && <ErrorNote message={apiErrorMessage(shelfQuery.error)} />}

      {shelfQuery.isPending ? (
        <Spinner label="Собираем полку" />
      ) : shelfQuery.data && shelfQuery.data.results.length > 0 ? (
        <ul className="space-y-3">
          {shelfQuery.data.results.map((item) => (
            <li
              key={item.id}
              className="flex flex-wrap items-center gap-4 rounded-card border border-line bg-paper-raised p-3"
            >
              <div
                className="h-24 w-16 shrink-0 overflow-hidden rounded"
                style={{ backgroundColor: item.edition.accent_color || 'var(--color-line)' }}
              >
                {item.edition.cover && (
                  <img
                    src={item.edition.cover}
                    alt=""
                    loading="lazy"
                    className="size-full object-cover"
                  />
                )}
              </div>

              <div className="min-w-48 flex-1">
                <Link
                  to={`/books/${item.edition.book_id}`}
                  className="font-serif text-lg text-ink hover:underline"
                >
                  {item.edition.book_name}
                </Link>
                <p className="text-sm text-ink-soft">
                  {item.edition.authors.map((author) => author.name).join(', ')}
                </p>
                <p className="mt-1 text-xs text-ink-faint">
                  {item.edition.format_display}
                  {item.is_owned ? ' · в библиотеке' : ''}
                </p>

                {item.progress_percent > 0 && (
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 w-32 overflow-hidden rounded-full bg-line">
                      <div
                        className="h-full rounded-full bg-ink"
                        style={{ width: `${item.progress_percent}%` }}
                      />
                    </div>
                    <span className="text-xs text-ink-faint">{item.progress_percent}%</span>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={item.status}
                  onChange={(event) =>
                    statusMutation.mutate({
                      id: item.id,
                      next: event.target.value as ShelfStatus,
                    })
                  }
                  aria-label="Статус книги"
                  className="rounded-full border border-line bg-paper px-3 py-1.5 text-sm"
                >
                  <option value="want">Хочу прочитать</option>
                  <option value="reading">Читаю</option>
                  <option value="read">Прочитано</option>
                </select>

                {item.is_owned && (
                  <Link
                    to={`/read/${item.edition.id}`}
                    className="rounded-full bg-ink px-3 py-1.5 text-sm text-paper"
                  >
                    Читать
                  </Link>
                )}

                <button
                  type="button"
                  onClick={() => removeMutation.mutate(item.id)}
                  className="rounded-full border border-line px-3 py-1.5 text-sm text-ink-soft hover:text-ink"
                >
                  Убрать
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          title="Полка пока пуста"
          hint="Найдите книгу в каталоге и добавьте её сюда"
        />
      )}
    </div>
  )
}
