import { Link } from 'react-router-dom'

import type { BookListItem } from '../api/types'
import { DiscountBadge, Price, Stars } from './ui'

export function BookCard({ book }: { book: BookListItem }) {
  const authors = book.authors.map((author) => author.name).join(', ')

  return (
    <article className="group flex flex-col overflow-hidden rounded-card bg-white shadow-sm ring-1 ring-ink/5 transition hover:-translate-y-1 hover:shadow-lg">
      <Link to={`/books/${book.id}`} className="relative block">
        <div
          className="aspect-2/3 overflow-hidden"
          // Пока обложка грузится, место занимает цвет книги, а не серый блок.
          style={{ backgroundColor: book.accent_color || 'var(--color-mint-soft)' }}
        >
          {book.cover ? (
            <img
              src={book.cover}
              alt={`Обложка «${book.name}»`}
              loading="lazy"
              className="size-full object-cover transition duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="flex size-full items-center justify-center p-4">
              <span className="text-center text-sm font-semibold text-white/85">
                {book.name}
              </span>
            </div>
          )}
        </div>

        {book.sale && (
          <span className="absolute left-2 top-2">
            <DiscountBadge percent={book.sale.discount_percent} />
          </span>
        )}

        {book.is_liked && (
          <span
            className="absolute right-2 top-2 grid size-7 place-items-center rounded-full bg-white/90 text-sm text-blush shadow"
            aria-label="В избранном"
          >
            ♥
          </span>
        )}

        {book.is_read && (
          <span className="absolute bottom-2 left-2 rounded-pill bg-ink/75 px-2 py-0.5 text-[11px] font-medium text-white">
            Прочитано
          </span>
        )}
      </Link>

      <div className="flex flex-1 flex-col gap-1.5 p-3">
        <Link to={`/books/${book.id}`} className="hover:underline">
          <h3 className="line-clamp-2 text-sm font-bold leading-snug text-ink">{book.name}</h3>
        </Link>

        {authors && <p className="line-clamp-1 text-xs text-ink-soft">{authors}</p>}

        <Stars value={book.average_rating} count={book.reviews_count} />

        <div className="mt-auto flex items-end justify-between gap-2 pt-1">
          {book.min_price === null ? (
            <span className="text-xs text-ink-faint">Нет изданий</span>
          ) : (
            <Price
              value={book.sale ? book.sale.price : book.min_price}
              oldValue={book.sale ? book.sale.old_price : null}
            />
          )}
          <span className="text-[10px] uppercase tracking-wide text-ink-faint">
            {book.language_display}
          </span>
        </div>
      </div>
    </article>
  )
}

export function BookGrid({ books }: { books: BookListItem[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {books.map((book) => (
        <BookCard key={book.id} book={book} />
      ))}
    </div>
  )
}

/** Горизонтальная лента — для «Новинок» и «Со скидкой». */
export function BookRail({ books }: { books: BookListItem[] }) {
  return (
    <div className="-mx-4 overflow-x-auto px-4 pb-2">
      <div className="flex gap-4">
        {books.map((book) => (
          <div key={book.id} className="w-40 shrink-0 sm:w-44">
            <BookCard book={book} />
          </div>
        ))}
      </div>
    </div>
  )
}
