import { useQuery } from '@tanstack/react-query'

import { apiErrorMessage } from '../api/client'
import { fetchBooks } from '../api/endpoints'
import { BookGrid } from '../components/BookCard'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'
import { SectionHeading } from '../components/ui'

export function SalePage() {
  const query = useQuery({
    queryKey: ['books', 'sale', 'page'],
    queryFn: () => fetchBooks({ on_sale: true }),
  })

  if (query.isPending) return <Spinner label="Ищем скидки" />
  if (query.isError) return <ErrorNote message={apiErrorMessage(query.error)} />

  const books = query.data?.results ?? []

  return (
    <div className="space-y-6">
      <SectionHeading>Books on Sale</SectionHeading>
      <p className="text-center text-ink-soft">
        Издания, которые сейчас стоят дешевле обычного.
      </p>

      {books.length > 0 ? (
        <BookGrid books={books} />
      ) : (
        <EmptyState
          title="Сейчас скидок нет"
          hint="Загляните позже — подборка обновляется"
        />
      )}
    </div>
  )
}
