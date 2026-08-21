import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'

import { apiErrorMessage } from '../api/client'
import { fetchLeaderboard, fetchMyGamification, fetchTrophies } from '../api/endpoints'
import { useAuth } from '../auth/useAuth'
import { ErrorNote, Spinner } from '../components/Spinner'
import { SectionHeading } from '../components/ui'

const METRIC_LABEL: Record<string, string> = {
  books_read: 'Прочитано книг',
  reviews_written: 'Написано отзывов',
  notes_written: 'Заметок и цитат',
  genres_explored: 'Освоено жанров',
  languages_read: 'Языков',
}

export function AchievementsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const profileQuery = useQuery({
    queryKey: ['gamification-me'],
    queryFn: fetchMyGamification,
    enabled: Boolean(user),
  })

  const trophiesQuery = useQuery({
    queryKey: ['trophies'],
    queryFn: fetchTrophies,
  })

  const leaderboardQuery = useQuery({
    queryKey: ['leaderboard'],
    queryFn: fetchLeaderboard,
  })

  const profile = profileQuery.data
  const justAwarded = profile?.newly_awarded.length ?? 0

  /*
    Награды выдаются на стороне сервера во время запроса /me/. Списки наград и
    лидеров к этому моменту уже загружены, поэтому показывали бы устаревшую
    картину: «получено только что» рядом с прогресс-баром той же награды и
    заниженные очки в таблице. Как только что-то выдано — перезапрашиваем оба.
  */
  useEffect(() => {
    if (justAwarded === 0) return
    queryClient.invalidateQueries({ queryKey: ['trophies'] })
    queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
  }, [justAwarded, queryClient])

  return (
    <div className="space-y-12">
      <SectionHeading>Level &amp; Trophy</SectionHeading>

      {profileQuery.isError && <ErrorNote message={apiErrorMessage(profileQuery.error)} />}

      {user && profileQuery.isPending && <Spinner label="Считаем достижения" />}

      {profile && (
        <section className="space-y-6 rounded-card bg-white p-6 shadow-sm ring-1 ring-ink/5 sm:p-8">
          <div className="flex flex-wrap items-center gap-4">
            <span aria-hidden className="text-5xl">
              {profile.level?.icon || '🌱'}
            </span>
            <div>
              <p className="text-xs uppercase tracking-wide text-ink-faint">
                Ступень {profile.level?.number ?? 1}
              </p>
              <h2 className="display-title text-2xl text-ink">
                {profile.level?.name ?? 'Новичок'}
              </h2>
            </div>
            <div className="ml-auto text-right">
              <p className="display-title text-3xl text-ink">{profile.points}</p>
              <p className="text-xs text-ink-faint">очков</p>
            </div>
          </div>

          <div className="space-y-2">
            <div className="h-2.5 overflow-hidden rounded-pill bg-mint-wash">
              <div
                className="h-full rounded-pill bg-mint transition-all"
                style={{ width: `${profile.progress}%` }}
              />
            </div>
            <p className="text-sm text-ink-soft">
              {profile.next_level
                ? `До ступени «${profile.next_level.name}» — ${profile.points_to_next} очков`
                : 'Максимальная ступень достигнута'}
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-4 border-t border-line pt-5 sm:grid-cols-5">
            {Object.entries(profile.metrics).map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs text-ink-faint">{METRIC_LABEL[key] ?? key}</dt>
                <dd className="display-title text-xl text-ink">{value}</dd>
              </div>
            ))}
          </dl>

          {profile.newly_awarded.length > 0 && (
            <p className="rounded-card bg-blush-wash px-4 py-3 text-sm text-ink">
              Получено только что:{' '}
              <strong>
                {profile.newly_awarded.map((trophy) => trophy.name).join(', ')}
              </strong>
            </p>
          )}
        </section>
      )}

      {!user && (
        <p className="text-center text-ink-soft">
          Войдите, чтобы отслеживать свой прогресс. Список наград виден и так.
        </p>
      )}

      <section className="space-y-5">
        <SectionHeading>Награды</SectionHeading>

        {trophiesQuery.isPending ? (
          <Spinner label="Загружаем награды" />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {trophiesQuery.data?.map((row) => (
              <article
                key={row.trophy.id}
                className={[
                  'flex gap-4 rounded-card p-4 ring-1 transition',
                  row.earned
                    ? 'bg-white ring-mint'
                    : 'bg-white/60 ring-ink/5',
                ].join(' ')}
              >
                <span
                  aria-hidden
                  className={row.earned ? 'text-3xl' : 'text-3xl grayscale opacity-50'}
                >
                  {row.trophy.icon || '🏅'}
                </span>

                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-ink">{row.trophy.name}</h3>
                  <p className="text-sm text-ink-soft">{row.trophy.description}</p>

                  {row.earned ? (
                    <p className="mt-2 text-xs font-semibold text-mint">Получено</p>
                  ) : (
                    <div className="mt-2 space-y-1">
                      <div className="h-1.5 overflow-hidden rounded-pill bg-line">
                        <div
                          className="h-full rounded-pill bg-blush"
                          style={{ width: `${row.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-ink-faint">
                        {row.current} из {row.trophy.threshold}
                      </p>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-5">
        <SectionHeading>Таблица лидеров</SectionHeading>

        {leaderboardQuery.isPending ? (
          <Spinner label="Собираем рейтинг" />
        ) : leaderboardQuery.data && leaderboardQuery.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-md overflow-hidden rounded-card bg-white text-sm shadow-sm ring-1 ring-ink/5">
              <thead className="bg-mint-wash text-left text-xs uppercase tracking-wide text-ink-soft">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Читатель</th>
                  <th className="px-4 py-3">Ступень</th>
                  <th className="px-4 py-3 text-right">Книг</th>
                  <th className="px-4 py-3 text-right">Очков</th>
                </tr>
              </thead>
              <tbody>
                {leaderboardQuery.data.map((row) => (
                  <tr key={row.user.id} className="border-t border-line">
                    <td className="px-4 py-3 font-bold text-ink-faint">{row.rank}</td>
                    <td className="px-4 py-3 font-semibold text-ink">{row.user.username}</td>
                    <td className="px-4 py-3 text-ink-soft">
                      {row.level ? `${row.level.icon} ${row.level.name}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">{row.books_read}</td>
                    <td className="px-4 py-3 text-right font-bold">{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center text-ink-soft">
            Пока никто не дочитал ни одной книги — будьте первым.
          </p>
        )}
      </section>
    </div>
  )
}
