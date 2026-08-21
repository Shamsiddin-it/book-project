import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import {
  acquireEdition,
  fetchBook,
  fetchSimilarBooks,
  toggleLike,
} from '../api/endpoints'
import type { Edition } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { BookGrid } from '../components/BookCard'
import { CommentsSection } from '../components/Comments'
import { BookNotesSection } from '../components/Notes'
import { ReviewsSection } from '../components/Reviews'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'
import { DiscountBadge, Price, SectionHeading, Stars } from '../components/ui'

export function BookPage() {
  const { id } = useParams()
  const bookId = Number(id)
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [chosenEditionId, setChosenEditionId] = useState<number | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const bookQuery = useQuery({
    queryKey: ['book', bookId],
    queryFn: () => fetchBook(bookId),
    enabled: Number.isFinite(bookId),
  })

  const similarQuery = useQuery({
    queryKey: ['similar', bookId],
    queryFn: () => fetchSimilarBooks(bookId),
    enabled: Number.isFinite(bookId),
  })

  const book = bookQuery.data

  // По ТЗ пользователь сам выбирает издание, которое ему ближе.
  // По умолчанию — самое дешёвое из доступных.
  const editions = useMemo(
    () => (book?.editions ?? []).filter((edition) => edition.is_active),
    [book],
  )

  // Пока пользователь не выбрал издание сам, показываем самое дешёвое.
  // Это выводимое значение, а не состояние: эффект здесь дал бы лишний рендер
  // и рассинхрон при смене книги.
  const cheapestEdition = useMemo(
    () => [...editions].sort((a, b) => Number(a.price) - Number(b.price))[0],
    [editions],
  )

  const selectedEdition: Edition | undefined =
    editions.find((edition) => edition.id === chosenEditionId) ?? cheapestEdition

  const likeMutation = useMutation({
    mutationFn: () => toggleLike(bookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['book', bookId] })
      queryClient.invalidateQueries({ queryKey: ['books'] })
    },
    onError: (error) => setActionError(apiErrorMessage(error)),
  })

  const acquireMutation = useMutation({
    mutationFn: (editionId: number) => acquireEdition(editionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shelf'] })
      if (selectedEdition) navigate(`/read/${selectedEdition.id}`)
    },
    onError: (error) => setActionError(apiErrorMessage(error)),
  })

  if (bookQuery.isPending) return <Spinner label="Открываем книгу" />
  if (bookQuery.isError) return <ErrorNote message={apiErrorMessage(bookQuery.error)} />
  if (!book) return <EmptyState title="Книга не найдена" />

  const accent = book.accent_color || '#6b4f3a'
  const cover = selectedEdition?.cover ?? null

  return (
    // Цвет книги живёт в CSS-переменной: так его подхватывают все вложенные
    // элементы, не таская inline-стиль по каждому из них.
    <div style={{ ['--accent' as string]: accent }} className="space-y-12">
      <section className="overflow-hidden rounded-card">
        <div className="accent-surface px-6 py-10 text-white sm:px-10">
          <div className="flex flex-col gap-8 sm:flex-row">
            <div className="w-40 shrink-0 overflow-hidden rounded-lg bg-white/15 shadow-xl sm:w-52">
              {cover ? (
                <img
                  src={cover}
                  alt={`Обложка «${book.name}»`}
                  className="aspect-2/3 w-full object-cover"
                />
              ) : (
                <div className="flex aspect-2/3 items-center justify-center p-4 text-center text-sm font-semibold text-white/70">
                  {book.name}
                </div>
              )}
            </div>

            <div className="flex-1 space-y-4">
              <div>
                <h1 className="display-title text-3xl leading-tight sm:text-4xl">{book.name}</h1>
                <p className="mt-1 text-white/80">
                  {book.authors.map((author) => author.name).join(', ')}
                </p>
              </div>

              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded-pill bg-white/15 px-2.5 py-1">
                  {book.language_display}
                </span>
                <span className="rounded-pill bg-white/15 px-2.5 py-1">
                  {book.publishing_year}
                </span>
                {book.categories.map((category) => (
                  <span key={category.id} className="rounded-pill bg-white/15 px-2.5 py-1">
                    {category.name}
                  </span>
                ))}
              </div>

              {/* По ТЗ описание без спойлеров. */}
              <p className="max-w-prose leading-relaxed text-white/90">{book.description}</p>

              <div className="pt-1">
                <Stars value={book.average_rating} count={book.reviews_count} />
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                {user && (
                  <button
                    type="button"
                    onClick={() => likeMutation.mutate()}
                    disabled={likeMutation.isPending}
                    className="rounded-pill bg-white/15 px-4 py-2 text-sm transition hover:bg-white/25"
                  >
                    {book.is_liked ? '♥ В избранном' : '♡ В избранное'}
                  </button>
                )}
                {book.is_read && (
                  <span className="rounded-pill bg-white/15 px-4 py-2 text-sm">Прочитано</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {actionError && <ErrorNote message={actionError} />}

      <section className="space-y-4">
        <SectionHeading>Издания</SectionHeading>
        <p className="text-sm text-ink-soft">Выберите обложку, которая вам ближе.</p>

        {editions.length === 0 ? (
          <EmptyState title="У этой книги пока нет доступных изданий" />
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {editions.map((edition) => {
                const active = edition.id === selectedEdition?.id
                return (
                  <button
                    key={edition.id}
                    type="button"
                    onClick={() => setChosenEditionId(edition.id)}
                    aria-pressed={active}
                    className={[
                      'flex items-center gap-3 rounded-card border p-3 text-left transition',
                      active
                        ? 'accent-border bg-white shadow-sm'
                        : 'border-line hover:border-ink-faint',
                    ].join(' ')}
                  >
                    <div
                      className="h-20 w-14 shrink-0 overflow-hidden rounded"
                      style={{ backgroundColor: accent }}
                    >
                      {edition.cover && (
                        <img
                          src={edition.cover}
                          alt=""
                          className="size-full object-cover"
                          loading="lazy"
                        />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink">{edition.format_display}</p>
                      {edition.publisher && (
                        <p className="truncate text-xs text-ink-soft">{edition.publisher}</p>
                      )}
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <Price
                          value={edition.price}
                          oldValue={edition.is_on_sale ? edition.old_price : null}
                        />
                        {edition.is_on_sale && (
                          <DiscountBadge percent={edition.discount_percent} />
                        )}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>

            {selectedEdition && (
              <div className="flex flex-wrap gap-3 pt-2">
                {user ? (
                  <button
                    type="button"
                    onClick={() => acquireMutation.mutate(selectedEdition.id)}
                    disabled={acquireMutation.isPending}
                    className="accent-surface rounded-pill px-5 py-2.5 text-sm text-white transition hover:opacity-90 disabled:opacity-60"
                  >
                    {acquireMutation.isPending ? 'Добавляем…' : 'Получить бесплатно и читать'}
                  </button>
                ) : (
                  <Link
                    to="/login"
                    className="accent-surface rounded-pill px-5 py-2.5 text-sm text-white transition hover:opacity-90"
                  >
                    Войдите, чтобы читать
                  </Link>
                )}
              </div>
            )}
          </>
        )}
      </section>

      {book.characters.length > 0 && (
        <section className="space-y-4">
          <SectionHeading>Герои</SectionHeading>
          <div className="grid gap-4 sm:grid-cols-2">
            {book.characters.map((character) => (
              <article
                key={character.id}
                className="flex gap-4 rounded-card border border-line bg-white p-4"
              >
                {character.image && (
                  <img
                    src={character.image}
                    alt={character.name}
                    loading="lazy"
                    className="size-20 shrink-0 rounded-pill object-cover"
                  />
                )}
                <div className="min-w-0">
                  <h3 className="text-lg font-bold text-ink">{character.name}</h3>
                  {character.signature_quote && (
                    <blockquote className="accent-border mt-2 border-l-2 pl-3 text-sm italic text-ink-soft">
                      {character.signature_quote}
                    </blockquote>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {book.moodboard.length > 0 && (
        <section className="space-y-4">
          <SectionHeading>Мудборд</SectionHeading>
          <p className="text-sm text-ink-soft">Настроение книги в шести кадрах.</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {book.moodboard.map((image) => (
              <img
                key={image.id}
                src={image.image}
                alt=""
                loading="lazy"
                className="aspect-square w-full rounded-lg object-cover"
              />
            ))}
          </div>
        </section>
      )}

      <ReviewsSection bookId={book.id} />

      <BookNotesSection bookId={book.id} />

      <CommentsSection bookId={book.id} />

      {similarQuery.data && similarQuery.data.results.length > 0 && (
        <section className="space-y-4">
          <SectionHeading>Если вам понравилась эта книга</SectionHeading>
          <BookGrid books={similarQuery.data.results} />
        </section>
      )}
    </div>
  )
}
