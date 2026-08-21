import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { createNote, fetchBookNotes } from '../api/endpoints'
import type { NoteKind } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { ErrorNote, Spinner } from './Spinner'
import { pillClass } from './styles'
import { SectionHeading } from './ui'

function NoteForm({ bookId }: { bookId: number }) {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')
  const [kind, setKind] = useState<NoteKind>('quote')
  const [page, setPage] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      createNote({
        book: bookId,
        text: text.trim(),
        kind,
        page: page ? Number(page) : undefined,
        is_public: isPublic,
      }),
    onSuccess: () => {
      setText('')
      setPage('')
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['book-notes', bookId] })
      queryClient.invalidateQueries({ queryKey: ['my-notes'] })
    },
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        if (!text.trim()) {
          setError('Введите текст')
          return
        }
        mutation.mutate()
      }}
      className="space-y-3 rounded-card bg-white p-4 shadow-sm ring-1 ring-ink/5"
    >
      <div className="flex gap-1">
        {(['quote', 'note'] as NoteKind[]).map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setKind(option)}
            className={[
              'rounded-pill px-3 py-1.5 text-xs font-semibold transition',
              kind === option ? 'bg-ink text-cream' : 'border border-line text-ink-soft',
            ].join(' ')}
          >
            {option === 'quote' ? 'Цитата' : 'Заметка'}
          </button>
        ))}
      </div>

      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={3}
        placeholder={kind === 'quote' ? 'Строки, которые захотелось сохранить' : 'Ваша мысль о книге'}
        className="w-full rounded-card border border-line bg-cream px-3 py-2 text-sm outline-none focus:border-mint"
      />

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="number"
          min={1}
          value={page}
          onChange={(event) => setPage(event.target.value)}
          placeholder="Стр."
          aria-label="Номер страницы"
          className="w-20 rounded-pill border border-line bg-white px-3 py-1.5 text-sm outline-none focus:border-mint"
        />

        <label className="flex items-center gap-2 text-xs text-ink-soft">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(event) => setIsPublic(event.target.checked)}
            className="accent-[var(--color-mint)]"
          />
          Видно другим
        </label>

        {error && <ErrorNote message={error} />}

        <button
          type="submit"
          disabled={mutation.isPending}
          className={pillClass('mint', 'ml-auto')}
        >
          {mutation.isPending ? 'Сохраняем…' : 'Сохранить'}
        </button>
      </div>
    </form>
  )
}

/** Публичные цитаты читателей на странице книги. */
export function BookNotesSection({ bookId }: { bookId: number }) {
  const { user } = useAuth()

  const query = useQuery({
    queryKey: ['book-notes', bookId],
    queryFn: () => fetchBookNotes(bookId),
  })

  const notes = query.data?.results ?? []

  return (
    <section className="space-y-5">
      <SectionHeading>Цитаты читателей</SectionHeading>

      {user ? (
        <NoteForm bookId={bookId} />
      ) : (
        <p className="text-sm text-ink-soft">
          Войдите, чтобы сохранять цитаты и заметки.
        </p>
      )}

      {query.isPending ? (
        <Spinner label="Загружаем цитаты" />
      ) : notes.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {notes.map((note) => (
            <figure
              key={note.id}
              className="rounded-card bg-white p-4 shadow-sm ring-1 ring-ink/5"
            >
              <blockquote className="border-l-4 border-blush pl-3 text-sm leading-relaxed text-ink">
                {note.text}
              </blockquote>
              <figcaption className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-faint">
                <Link to={`/users/${note.user.id}`} className="font-semibold hover:text-ink">
                  {note.user.username}
                </Link>
                <span>{note.kind_display}</span>
                {note.page && <span>стр. {note.page}</span>}
              </figcaption>
            </figure>
          ))}
        </div>
      ) : (
        <p className="text-sm text-ink-soft">
          Пока никто не сохранил цитату из этой книги.
        </p>
      )}
    </section>
  )
}
