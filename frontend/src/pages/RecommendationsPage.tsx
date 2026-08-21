import { useQuery } from '@tanstack/react-query'

import { apiErrorMessage } from '../api/client'
import { fetchRecommendations } from '../api/endpoints'
import type { RecommendationBasis } from '../api/types'
import { BookGrid } from '../components/BookCard'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'

/*
  Бэкенд честно сообщает, на чём построена подборка. Подписываем блок по факту,
  а не называем персональным то, что на деле просто популярное.
*/
const BASIS_LABEL: Record<RecommendationBasis, string> = {
  collaborative: 'Читатели с похожим вкусом выбрали это',
  taste: 'По жанрам и авторам, которые вы уже выбирали',
  popular: 'Пока мы вас не знаем — вот что читают чаще всего',
  mixed: 'По вашему вкусу, дополнено популярным',
}

export function RecommendationsPage() {
  const query = useQuery({
    queryKey: ['recommendations'],
    queryFn: () => fetchRecommendations(),
  })

  if (query.isPending) return <Spinner label="Подбираем книги" />
  if (query.isError) return <ErrorNote message={apiErrorMessage(query.error)} />

  const data = query.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-3xl text-ink">Для вас</h1>
        {data && <p className="mt-1 text-ink-soft">{BASIS_LABEL[data.basis]}</p>}
      </div>

      {data && data.results.length > 0 ? (
        <BookGrid books={data.results} />
      ) : (
        <EmptyState
          title="Пока нечего предложить"
          hint="Отметьте несколько книг — и подборка появится"
        />
      )}
    </div>
  )
}
