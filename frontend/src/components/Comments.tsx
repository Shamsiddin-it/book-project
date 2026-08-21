import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import {
  deleteComment,
  fetchComments,
  postComment,
  toggleCommentLike,
} from '../api/endpoints'
import type { Comment } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { ErrorNote, Spinner } from './Spinner'
import { pillClass } from './styles'
import { SectionHeading } from './ui'

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
  })
}

function CommentForm({
  bookId,
  parent,
  onDone,
  autoFocus,
}: {
  bookId: number
  parent?: number
  onDone?: () => void
  autoFocus?: boolean
}) {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')
  const [hasSpoilers, setHasSpoilers] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      postComment({
        book: bookId,
        text: text.trim(),
        parent,
        has_spoilers: hasSpoilers,
      }),
    onSuccess: () => {
      setText('')
      setHasSpoilers(false)
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['comments', bookId] })
      onDone?.()
    },
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        if (!text.trim()) {
          setError('Напишите что-нибудь')
          return
        }
        mutation.mutate()
      }}
      className="space-y-2"
    >
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={parent ? 2 : 3}
        autoFocus={autoFocus}
        placeholder={parent ? 'Ваш ответ' : 'Что вы думаете об этой книге?'}
        className="w-full rounded-card border border-line bg-white px-3 py-2 text-sm outline-none focus:border-mint"
      />

      {error && <ErrorNote message={error} />}

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-ink-soft">
          <input
            type="checkbox"
            checked={hasSpoilers}
            onChange={(event) => setHasSpoilers(event.target.checked)}
            className="accent-[var(--color-blush)]"
          />
          Есть спойлеры
        </label>

        <button type="submit" disabled={mutation.isPending} className={pillClass('mint')}>
          {mutation.isPending ? 'Отправляем…' : parent ? 'Ответить' : 'Отправить'}
        </button>

        {onDone && (
          <button type="button" onClick={onDone} className={pillClass('outline')}>
            Отмена
          </button>
        )}
      </div>
    </form>
  )
}

function CommentCard({
  comment,
  bookId,
  depth = 0,
}: {
  comment: Comment
  bookId: number
  depth?: number
}) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [replying, setReplying] = useState(false)
  // Комментарий со спойлером закрыт, пока читатель сам не решит его открыть.
  const [revealed, setRevealed] = useState(false)

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['comments', bookId] })
  }

  const likeMutation = useMutation({
    mutationFn: () => toggleCommentLike(comment.id),
    onSuccess: invalidate,
  })

  const removeMutation = useMutation({
    mutationFn: () => deleteComment(comment.id),
    onSuccess: invalidate,
  })

  const isMine = user?.id === comment.user.id
  const hidden = comment.has_spoilers && !revealed

  return (
    <article className="rounded-card bg-white p-4 shadow-sm ring-1 ring-ink/5">
      <div className="flex flex-wrap items-center gap-2">
        <Link
          to={`/users/${comment.user.id}`}
          className="text-sm font-semibold text-ink hover:underline"
        >
          {comment.user.username}
        </Link>
        <span className="text-xs text-ink-faint">{formatDate(comment.created_at)}</span>

        {comment.has_spoilers && (
          <span className="rounded-pill bg-blush-wash px-2 py-0.5 text-[10px] font-semibold text-ink-soft">
            спойлер
          </span>
        )}
      </div>

      {hidden ? (
        <button
          type="button"
          onClick={() => setRevealed(true)}
          className="mt-2 w-full rounded-card border border-dashed border-line py-3 text-sm text-ink-soft hover:text-ink"
        >
          Здесь спойлер — нажмите, чтобы показать
        </button>
      ) : (
        <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-ink">
          {comment.text}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
        <button
          type="button"
          onClick={() => user && likeMutation.mutate()}
          disabled={!user || likeMutation.isPending}
          className={[
            'flex items-center gap-1 transition',
            comment.is_liked ? 'text-blush' : 'text-ink-faint hover:text-blush',
            user ? '' : 'cursor-not-allowed',
          ].join(' ')}
          title={user ? 'Нравится' : 'Войдите, чтобы отмечать'}
        >
          ♥ {comment.likes_count}
        </button>

        {/* Ветки ограничены одним уровнем — так же, как на бэкенде. */}
        {user && depth === 0 && (
          <button
            type="button"
            onClick={() => setReplying((value) => !value)}
            className="text-ink-faint hover:text-ink"
          >
            Ответить
          </button>
        )}

        {isMine && (
          <button
            type="button"
            onClick={() => removeMutation.mutate()}
            className="text-ink-faint hover:text-red-600"
          >
            Удалить
          </button>
        )}
      </div>

      {replying && (
        <div className="mt-3">
          <CommentForm
            bookId={bookId}
            parent={comment.id}
            autoFocus
            onDone={() => setReplying(false)}
          />
        </div>
      )}

      {comment.replies.length > 0 && (
        <div className="mt-3 space-y-3 border-l-2 border-line pl-4">
          {comment.replies.map((reply) => (
            <CommentCard key={reply.id} comment={reply} bookId={bookId} depth={depth + 1} />
          ))}
        </div>
      )}
    </article>
  )
}

export function CommentsSection({ bookId }: { bookId: number }) {
  const { user } = useAuth()

  const query = useQuery({
    queryKey: ['comments', bookId],
    queryFn: () => fetchComments(bookId),
  })

  return (
    <section className="space-y-5">
      <SectionHeading>Обсуждение</SectionHeading>

      {user ? (
        <CommentForm bookId={bookId} />
      ) : (
        <p className="text-sm text-ink-soft">Войдите, чтобы участвовать в обсуждении.</p>
      )}

      {query.isError && <ErrorNote message={apiErrorMessage(query.error)} />}

      {query.isPending ? (
        <Spinner label="Загружаем обсуждение" />
      ) : query.data && query.data.results.length > 0 ? (
        <div className="space-y-4">
          {query.data.results.map((comment) => (
            <CommentCard key={comment.id} comment={comment} bookId={bookId} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-ink-soft">
          Обсуждения пока нет. Начните первым.
        </p>
      )}
    </section>
  )
}
