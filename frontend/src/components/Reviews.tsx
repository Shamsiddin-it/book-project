import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { apiErrorMessage } from '../api/client'
import { fetchBookReviews, fetchRatingSummary, submitReview } from '../api/endpoints'
import { useAuth } from '../auth/useAuth'
import { ErrorNote, Spinner } from './Spinner'
import { SectionHeading, Stars } from './ui'
import { pillClass } from './styles'

function RatingBars({ distribution, total }: { distribution: Record<string, number>; total: number }) {
  return (
    <div className="space-y-1.5">
      {[5, 4, 3, 2, 1].map((star) => {
        const count = distribution[String(star)] ?? 0
        // При нуле отзывов делить нельзя — иначе получим NaN в ширине.
        const share = total > 0 ? Math.round((count / total) * 100) : 0

        return (
          <div key={star} className="flex items-center gap-2 text-xs">
            <span className="w-3 text-ink-soft">{star}</span>
            <span aria-hidden className="text-blush">
              ★
            </span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-pill bg-line">
              <div className="h-full rounded-pill bg-blush" style={{ width: `${share}%` }} />
            </div>
            <span className="w-6 text-right text-ink-faint">{count}</span>
          </div>
        )
      })}
    </div>
  )
}

function ReviewForm({ bookId }: { bookId: number }) {
  const queryClient = useQueryClient()
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => submitReview({ book: bookId, rating, text: text.trim() || undefined }),
    onSuccess: () => {
      setRating(0)
      setText('')
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['reviews', bookId] })
      queryClient.invalidateQueries({ queryKey: ['rating-summary', bookId] })
      queryClient.invalidateQueries({ queryKey: ['book', bookId] })
    },
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        if (rating === 0) {
          setError('Поставьте оценку от 1 до 5')
          return
        }
        mutation.mutate()
      }}
      className="space-y-3 rounded-card bg-white p-4 shadow-sm ring-1 ring-ink/5"
    >
      <p className="text-sm font-semibold text-ink">Ваша оценка</p>

      <div className="flex gap-1" role="radiogroup" aria-label="Оценка книги">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            role="radio"
            aria-checked={rating === star}
            aria-label={`${star} из 5`}
            onClick={() => setRating(star)}
            className={[
              'text-2xl leading-none transition',
              star <= rating ? 'text-blush' : 'text-ink-faint/40 hover:text-blush/60',
            ].join(' ')}
          >
            ★
          </button>
        ))}
      </div>

      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={3}
        placeholder="Несколько слов о книге — необязательно"
        className="w-full rounded-card border border-line bg-cream px-3 py-2 text-sm outline-none focus:border-mint"
      />

      {error && <ErrorNote message={error} />}

      <button type="submit" disabled={mutation.isPending} className={pillClass('mint')}>
        {mutation.isPending ? 'Отправляем…' : 'Оценить'}
      </button>
    </form>
  )
}

export function ReviewsSection({ bookId }: { bookId: number }) {
  const { user } = useAuth()

  const summaryQuery = useQuery({
    queryKey: ['rating-summary', bookId],
    queryFn: () => fetchRatingSummary(bookId),
  })

  const reviewsQuery = useQuery({
    queryKey: ['reviews', bookId],
    queryFn: () => fetchBookReviews(bookId),
  })

  const summary = summaryQuery.data

  return (
    <section className="space-y-5">
      <SectionHeading>Отзывы</SectionHeading>

      <div className="grid gap-5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="space-y-4">
          <div className="rounded-card bg-white p-4 text-center shadow-sm ring-1 ring-ink/5">
            <p className="display-title text-4xl text-ink">
              {summary?.average_rating?.toFixed(1) ?? '—'}
            </p>
            <div className="mt-1 flex justify-center">
              <Stars value={summary?.average_rating ?? null} />
            </div>
            <p className="mt-1 text-xs text-ink-faint">
              {summary?.reviews_count ?? 0} оценок
            </p>

            {summary && summary.reviews_count > 0 && (
              <div className="mt-4">
                <RatingBars
                  distribution={summary.distribution}
                  total={summary.reviews_count}
                />
              </div>
            )}
          </div>

          {user ? (
            <ReviewForm bookId={bookId} />
          ) : (
            <p className="text-sm text-ink-soft">Войдите, чтобы оставить отзыв.</p>
          )}
        </div>

        <div className="space-y-3">
          {reviewsQuery.isPending ? (
            <Spinner label="Загружаем отзывы" />
          ) : reviewsQuery.data && reviewsQuery.data.results.length > 0 ? (
            reviewsQuery.data.results.map((review) => (
              <article
                key={review.id}
                className="rounded-card bg-white p-4 shadow-sm ring-1 ring-ink/5"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-ink">
                    {review.user.username}
                  </span>
                  <span aria-label={`${review.rating} из 5`} className="text-blush">
                    {'★'.repeat(review.rating)}
                    <span className="text-ink-faint/40">{'★'.repeat(5 - review.rating)}</span>
                  </span>
                </div>
                {review.text && (
                  <p className="mt-2 text-sm leading-relaxed text-ink-soft">{review.text}</p>
                )}
              </article>
            ))
          ) : (
            <p className="text-sm text-ink-soft">
              Отзывов пока нет. Ваш может стать первым.
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
