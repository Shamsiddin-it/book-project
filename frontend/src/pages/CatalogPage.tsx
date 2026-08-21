import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { fetchBooks, fetchCategories, fetchLanguages } from '../api/endpoints'
import { BookGrid, BookRail } from '../components/BookCard'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'
import { Blob, SectionHeading } from '../components/ui'
import { pillClass } from '../components/styles'

function Hero() {
  return (
    <section className="relative overflow-hidden rounded-card bg-white px-6 py-12 shadow-sm ring-1 ring-ink/5 sm:px-12 sm:py-16">
      <Blob className="-right-16 -top-20 h-72 w-80 opacity-90" />

      <div className="relative max-w-lg">
        <div className="mb-6 flex gap-2">
          {['Читай', 'Слушай', 'Собирай'].map((label) => (
            <span
              key={label}
              className="rounded-pill border border-ink/15 bg-white/70 px-3 py-1 text-[11px] font-semibold text-ink-soft"
            >
              {label}
            </span>
          ))}
        </div>

        <h1 className="display-title text-4xl text-ink sm:text-5xl">
          Твоя следующая глава начинается здесь
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-ink-soft">
          Покупай истории прямо с экрана — читай, слушай и собирай свою полку.
        </p>

        <Link to="/sale" className={pillClass('mint', 'mt-8')}>
          Смотреть каталог
        </Link>
      </div>
    </section>
  )
}

export function CatalogPage() {
  const [params, setParams] = useSearchParams()

  const search = params.get('search') ?? ''
  const language = params.get('language') ?? ''
  const category = params.get('categories') ?? ''
  const page = Number(params.get('page') ?? 1)

  const [searchDraft, setSearchDraft] = useState(search)

  // Адрес мог поменяться снаружи — кнопкой «назад» или поиском в шапке.
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

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories,
    staleTime: 5 * 60 * 1000,
  })

  const booksQuery = useQuery({
    queryKey: ['books', { search, language, category, page }],
    queryFn: () =>
      fetchBooks({
        search: search || undefined,
        language: language || undefined,
        categories: category ? Number(category) : undefined,
        page: page > 1 ? page : undefined,
      }),
    placeholderData: keepPreviousData,
  })

  // Витрины на главной. Показываем их только когда каталог не отфильтрован —
  // иначе они спорят с результатами поиска.
  const isBrowsing = !search && !language && !category && page === 1

  const newReleasesQuery = useQuery({
    queryKey: ['books', 'new'],
    queryFn: () => fetchBooks({ ordering: '-created_at' }),
    enabled: isBrowsing,
  })

  const saleQuery = useQuery({
    queryKey: ['books', 'sale'],
    queryFn: () => fetchBooks({ on_sale: true }),
    enabled: isBrowsing,
  })

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
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
    <div className="space-y-12">
      {isBrowsing && <Hero />}

      {isBrowsing && categoriesQuery.data && categoriesQuery.data.length > 0 && (
        <section className="space-y-5">
          <SectionHeading>Категории</SectionHeading>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {categoriesQuery.data.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setParam('categories', String(item.id))}
                className="group relative aspect-4/3 overflow-hidden rounded-card bg-ink text-left"
              >
                {item.image && (
                  <img
                    src={item.image}
                    alt=""
                    loading="lazy"
                    className="size-full object-cover opacity-70 transition group-hover:scale-105 group-hover:opacity-60"
                  />
                )}
                <span className="absolute inset-0 flex flex-col justify-end gap-2 p-4">
                  <span className="tracked text-sm font-bold text-white">{item.name}</span>
                  <span className="w-fit rounded-pill border border-white/60 px-2 py-0.5 text-[10px] font-semibold text-white">
                    Смотреть
                  </span>
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {isBrowsing && newReleasesQuery.data && newReleasesQuery.data.results.length > 0 && (
        <section className="space-y-5">
          <SectionHeading>Новинки</SectionHeading>
          <BookRail books={newReleasesQuery.data.results.slice(0, 10)} />
        </section>
      )}

      {isBrowsing && saleQuery.data && saleQuery.data.results.length > 0 && (
        <section className="space-y-5">
          <SectionHeading>Со скидкой</SectionHeading>
          <BookRail books={saleQuery.data.results.slice(0, 10)} />
          <div className="text-center">
            <Link to="/sale" className={pillClass('outline')}>
              Все скидки
            </Link>
          </div>
        </section>
      )}

      <section className="space-y-5">
        <SectionHeading>{isBrowsing ? 'Весь каталог' : 'Каталог'}</SectionHeading>

        <div className="flex flex-wrap items-center gap-3">
          <input
            type="search"
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            placeholder="Название или автор"
            aria-label="Поиск по каталогу"
            className="min-w-56 flex-1 rounded-pill border border-line bg-white px-4 py-2 text-sm outline-none focus:border-mint"
          />

          <div className="flex flex-wrap gap-1">
            <button
              type="button"
              onClick={() => setParam('language', '')}
              className={[
                'rounded-pill px-3 py-1.5 text-xs font-semibold transition',
                language === '' ? 'bg-ink text-cream' : 'border border-line text-ink-soft',
              ].join(' ')}
            >
              Все языки
            </button>
            {languagesQuery.data?.map((option) => (
              <button
                key={option.code}
                type="button"
                onClick={() => setParam('language', option.code)}
                className={[
                  'rounded-pill px-3 py-1.5 text-xs font-semibold transition',
                  language === option.code
                    ? 'bg-ink text-cream'
                    : 'border border-line text-ink-soft hover:text-ink',
                ].join(' ')}
              >
                {option.name}
                <span className="ml-1 opacity-60">{option.books_count}</span>
              </button>
            ))}
          </div>

          {category && (
            <button
              type="button"
              onClick={() => setParam('categories', '')}
              className={pillClass('outline', 'text-xs')}
            >
              Сбросить категорию ✕
            </button>
          )}
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
                  className={pillClass('outline')}
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
                  className={pillClass('outline')}
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
      </section>
    </div>
  )
}
