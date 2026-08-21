import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'

import { apiErrorMessage } from '../api/client'
import {
  fetchFollowers,
  fetchFollowing,
  fetchPublicGamification,
  fetchPublicShelf,
  fetchPublicUser,
  fetchUserNotes,
  toggleFollow,
} from '../api/endpoints'
import { useAuth } from '../auth/useAuth'
import { plural } from '../lib/plural'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'
import { pillClass } from '../components/styles'

/**
 * Полка и статистика чтения закрываются одним флагом приватности, и бэкенд
 * отвечает на них 403. Это не ошибка страницы — просто соответствующий блок
 * показывать нечего, поэтому такой ответ обрабатываем отдельно от настоящих сбоев.
 */
function isPrivate(error: unknown) {
  return axios.isAxiosError(error) && error.response?.status === 403
}

type Tab = 'shelf' | 'quotes' | 'followers' | 'following'

const TABS: { value: Tab; label: string }[] = [
  { value: 'shelf', label: 'Полка' },
  { value: 'quotes', label: 'Цитаты' },
  { value: 'followers', label: 'Подписчики' },
  { value: 'following', label: 'Подписки' },
]

export function UserProfilePage() {
  const { id } = useParams()
  const userId = Number(id)
  const { user: me } = useAuth()
  const queryClient = useQueryClient()

  const [tab, setTab] = useState<Tab>('shelf')

  const userQuery = useQuery({
    queryKey: ['public-user', userId],
    queryFn: () => fetchPublicUser(userId),
    enabled: Number.isFinite(userId),
  })

  const gamificationQuery = useQuery({
    queryKey: ['public-gamification', userId],
    queryFn: () => fetchPublicGamification(userId),
    enabled: Number.isFinite(userId),
    retry: false,
  })

  const shelfQuery = useQuery({
    queryKey: ['public-shelf', userId],
    queryFn: () => fetchPublicShelf(userId),
    enabled: Number.isFinite(userId) && tab === 'shelf',
    retry: false,
  })

  const notesQuery = useQuery({
    queryKey: ['public-notes', userId],
    queryFn: () => fetchUserNotes(userId),
    enabled: Number.isFinite(userId) && tab === 'quotes',
    retry: false,
  })

  const followersQuery = useQuery({
    queryKey: ['followers', userId],
    queryFn: () => fetchFollowers(userId),
    enabled: Number.isFinite(userId) && tab === 'followers',
  })

  const followingQuery = useQuery({
    queryKey: ['following', userId],
    queryFn: () => fetchFollowing(userId),
    enabled: Number.isFinite(userId) && tab === 'following',
  })

  const followMutation = useMutation({
    mutationFn: () => toggleFollow(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['public-user', userId] })
      queryClient.invalidateQueries({ queryKey: ['followers', userId] })
    },
  })

  if (userQuery.isPending) return <Spinner label="Открываем профиль" />
  if (userQuery.isError) return <ErrorNote message={apiErrorMessage(userQuery.error)} />
  if (!userQuery.data) return <EmptyState title="Пользователь не найден" />

  const profile = userQuery.data
  const isMe = me?.id === profile.id
  const gamification = gamificationQuery.data

  return (
    <div className="space-y-10">
      <section className="flex flex-wrap items-center gap-5 rounded-card bg-white p-6 shadow-sm ring-1 ring-ink/5">
        <div className="grid size-20 shrink-0 place-items-center overflow-hidden rounded-full bg-mint-wash text-2xl">
          {profile.photo ? (
            <img src={profile.photo} alt="" className="size-full object-cover" />
          ) : (
            <span aria-hidden>👤</span>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <h1 className="display-title text-2xl text-ink">{profile.username}</h1>
          {profile.bio && <p className="mt-1 text-sm text-ink-soft">{profile.bio}</p>}

          <div className="mt-2 flex flex-wrap gap-4 text-sm text-ink-soft">
            <span>
              <strong className="text-ink">{profile.followers_count}</strong>{' '}
              {plural(profile.followers_count, 'подписчик', 'подписчика', 'подписчиков')}
            </span>
            <span>
              <strong className="text-ink">{profile.following_count}</strong>{' '}
              {plural(profile.following_count, 'подписка', 'подписки', 'подписок')}
            </span>
            {gamification?.level && (
              <span>
                {gamification.level.icon} {gamification.level.name} ·{' '}
                <strong className="text-ink">{gamification.points}</strong>{' '}
                {plural(gamification.points, 'очко', 'очка', 'очков')}
              </span>
            )}
          </div>
        </div>

        {me && !isMe && (
          <button
            type="button"
            onClick={() => followMutation.mutate()}
            disabled={followMutation.isPending}
            className={pillClass(profile.is_following ? 'outline' : 'mint')}
          >
            {profile.is_following ? 'Вы подписаны' : 'Подписаться'}
          </button>
        )}

        {isMe && (
          <Link to="/shelf" className={pillClass('outline')}>
            Моя полка
          </Link>
        )}
      </section>

      <section className="space-y-5">
        <div className="flex flex-wrap justify-center gap-1">
          {TABS.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => setTab(item.value)}
              className={[
                'rounded-pill px-4 py-1.5 text-sm font-semibold transition',
                tab === item.value
                  ? 'bg-ink text-cream'
                  : 'border border-line text-ink-soft hover:text-ink',
              ].join(' ')}
            >
              {item.label}
            </button>
          ))}
        </div>

        {tab === 'shelf' &&
          (shelfQuery.isPending ? (
            <Spinner label="Открываем полку" />
          ) : isPrivate(shelfQuery.error) ? (
            <EmptyState
              title="Полка закрыта"
              hint="Этот читатель не показывает свою полку другим"
            />
          ) : shelfQuery.data && shelfQuery.data.results.length > 0 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
              {shelfQuery.data.results.map((item) => (
                <Link
                  key={item.id}
                  to={`/books/${item.edition.book_id}`}
                  className="group space-y-2"
                >
                  <div
                    className="aspect-2/3 overflow-hidden rounded-card"
                    style={{ backgroundColor: item.edition.accent_color || 'var(--color-mint-soft)' }}
                  >
                    {item.edition.cover && (
                      <img
                        src={item.edition.cover}
                        alt=""
                        loading="lazy"
                        className="size-full object-cover transition group-hover:scale-105"
                      />
                    )}
                  </div>
                  <p className="line-clamp-2 text-xs font-semibold text-ink">
                    {item.edition.book_name}
                  </p>
                  <p className="text-[10px] text-ink-faint">{item.status_display}</p>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="На полке пока пусто" />
          ))}

        {tab === 'quotes' &&
          (notesQuery.isPending ? (
            <Spinner label="Загружаем цитаты" />
          ) : isPrivate(notesQuery.error) ? (
            <EmptyState title="Цитаты скрыты" hint="Читатель закрыл свою полку" />
          ) : notesQuery.data && notesQuery.data.results.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {notesQuery.data.results.map((note) => (
                <figure
                  key={note.id}
                  className="rounded-card bg-white p-4 shadow-sm ring-1 ring-ink/5"
                >
                  <blockquote className="border-l-4 border-blush pl-3 text-sm text-ink">
                    {note.text}
                  </blockquote>
                  <figcaption className="mt-2 text-xs text-ink-faint">
                    {note.kind_display}
                    {note.page ? ` · стр. ${note.page}` : ''}
                    {!note.is_public && ' · только для вас'}
                  </figcaption>
                </figure>
              ))}
            </div>
          ) : (
            <EmptyState title="Цитат пока нет" />
          ))}

        {tab === 'followers' && (
          <UserList
            loading={followersQuery.isPending}
            users={followersQuery.data?.results ?? []}
            empty="Пока никто не подписан"
          />
        )}

        {tab === 'following' && (
          <UserList
            loading={followingQuery.isPending}
            users={followingQuery.data?.results ?? []}
            empty="Пока ни на кого не подписан"
          />
        )}
      </section>
    </div>
  )
}

function UserList({
  loading,
  users,
  empty,
}: {
  loading: boolean
  users: { id: number; username: string; photo: string | null; bio: string }[]
  empty: string
}) {
  if (loading) return <Spinner label="Загружаем" />
  if (users.length === 0) return <EmptyState title={empty} />

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {users.map((item) => (
        <Link
          key={item.id}
          to={`/users/${item.id}`}
          className="flex items-center gap-3 rounded-card bg-white p-3 shadow-sm ring-1 ring-ink/5 transition hover:-translate-y-0.5"
        >
          <span className="grid size-10 shrink-0 place-items-center overflow-hidden rounded-full bg-mint-wash">
            {item.photo ? (
              <img src={item.photo} alt="" className="size-full object-cover" />
            ) : (
              <span aria-hidden>👤</span>
            )}
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-semibold text-ink">{item.username}</span>
            {item.bio && (
              <span className="block truncate text-xs text-ink-faint">{item.bio}</span>
            )}
          </span>
        </Link>
      ))}
    </div>
  )
}
