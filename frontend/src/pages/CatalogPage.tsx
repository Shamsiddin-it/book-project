import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { fetchBooks, fetchLanguages } from '../api/endpoints'
import { BookGrid } from '../components/BookCard'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'
import { apiErrorMessage } from '../api/client'

export function CatalogPage() {
  const [params, setParams] = useSearchParams()

  const search = params.get('search') ?? ''
  const language = params.get('language') ?? ''
  const page = Number(params.get('page') ?? 1)

  // Локальное состояние поля ввода, чтобы не дёргать API на каждую букву.
  const [searchDraft, setSearchDraft] = useState(search)

  // Адрес мог измениться снаружи — кнопкой «назад» например. Правим поле прямо
  // во время рендера: это рекомендованный способ, эффект тут дал бы лишний проход.
  const [lastSearch, setLastSearch] = useState(search)
  if (search !== lastSearch) {
    setLastSearch(search)
    setSearchDraft(search)
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchDraft === search) return
      const next = new URLSearchParams(params)
      if (searchDraft) next.set('search', searchDraft)
      else next.delete('search')
      next.delete('page')
      setParams(next, { replace: true })
    }, 350)

    return () => clearTimeout(timer)
  }, [searchDraft, search, params, setParams])

  const languagesQuery = useQuery({
    queryKey: ['languages'],
    queryFn: fetchLanguages,
    staleTime: 5 * 60 * 1000,
  })

  const booksQuery = useQuery({
    queryKey: ['books', { search, language, page }],
    queryFn: () =>
      fetchBooks({
        search: search || undefined,
        language: language || undefined,
        page: page > 1 ? page : undefined,
      }),
    // Держим прошлую страницу на экране, пока грузится следующая:
    // без этого список моргает в пустоту при каждом переходе.
    placeholderData: keepPreviousData,
  })

  function setLanguage(code: string) {
    const next = new URLSearchParams(params)
    if (code) next.set('language', code)
    else next.delete('language')
    next.delete('page')
    setParams(next)
  }

  function goToPage(target: number) {
    const next = new URLSearchParams(params)
    if (target > 1) next.set('page', String(target))
    else next.delete('page')
    setParams(next)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const data = booksQuery.data
  const totalPages = data ? Math.max(1, Math.ceil(data.count / 20)) : 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-3xl text-ink">Каталог</h1>
        <p className="mt-1 text-ink-soft">Книги, издания и обложки на любой вкус.</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          value={searchDraft}
          onChange={(event) => setSearchDraft(event.target.value)}
          placeholder="Название или автор"
          aria-label="Поиск по каталогу"
          className="min-w-56 flex-1 rounded-full border border-line bg-paper-raised px-4 py-2 text-sm outline-none focus:border-ink"
        />

        <div className="flex flex-wrap gap-1">
          <button
            type="button"
            onClick={() => setLanguage('')}
            className={[
              'rounded-full px-3 py-1.5 text-sm transition',
              language === '' ? 'bg-ink text-paper' : 'border border-line text-ink-soft',
            ].join(' ')}
          >
            Все языки
          </button>
          {languagesQuery.data?.map((option) => (
            <button
              key={option.code}
              type="button"
              onClick={() => setLanguage(option.code)}
              className={[
                'rounded-full px-3 py-1.5 text-sm transition',
                language === option.code
                  ? 'bg-ink text-paper'
                  : 'border border-line text-ink-soft hover:text-ink',
              ].join(' ')}
            >
              {option.name}
              <span className="ml-1 text-xs opacity-60">{option.books_count}</span>
            </button>
          ))}
        </div>
      </div>

      {booksQuery.isError && <ErrorNote message={apiErrorMessage(booksQuery.error)} />}

      {booksQuery.isPending ? (
        <Spinner label="Загружаем каталог" />
      ) : data && data.results.length > 0 ? (
        <>
          <BookGrid books={data.results} />

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-4">
              <button
                type="button"
                disabled={!data.previous}
                onClick={() => goToPage(page - 1)}
                className="rounded-full border border-line px-4 py-1.5 text-sm disabled:opacity-40"
              >
                Назад
              </button>
              <span className="text-sm text-ink-soft">
                {page} из {totalPages}
              </span>
              <button
                type="button"
                disabled={!data.next}
                onClick={() => goToPage(page + 1)}
                className="rounded-full border border-line px-4 py-1.5 text-sm disabled:opacity-40"
              >
                Дальше
              </button>
            </div>
          )}
        </>
      ) : (
        <EmptyState
          title="Ничего не нашлось"
          hint={search ? 'Попробуйте изменить запрос' : 'В каталоге пока пусто'}
        />
      )}
    </div>
  )
}
