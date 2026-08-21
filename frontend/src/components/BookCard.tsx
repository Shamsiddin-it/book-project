import { Link } from 'react-router-dom'

import type { BookListItem } from '../api/types'

function formatPrice(value: string | null) {
  if (value === null) return 'Нет изданий'
  const amount = Number(value)
  if (Number.isNaN(amount)) return value
  return `${amount.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽`
}

export function BookCard({ book }: { book: BookListItem }) {
  const authors = book.authors.map((author) => author.name).join(', ')

  return (
    <Link
      to={`/books/${book.id}`}
      className="group flex flex-col overflow-hidden rounded-card border border-line bg-paper-raised transition hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div
        className="relative aspect-2/3 overflow-hidden"
        // Фон под обложкой — цвет книги. Пока обложка грузится, карточка уже
        // выглядит частью своей книги, а не серым прямоугольником.
        style={{ backgroundColor: book.accent_color || 'var(--color-line)' }}
      >
        {book.cover ? (
          <img
            src={book.cover}
            alt={`Обложка «${book.name}»`}
            loading="lazy"
            className="size-full object-cover transition duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="flex size-full items-center justify-center p-4">
            <span className="text-center font-serif text-sm text-white/80">{book.name}</span>
          </div>
        )}

        {book.is_read && (
          <span className="absolute left-2 top-2 rounded-full bg-black/70 px-2 py-0.5 text-xs text-white">
            Прочитано
          </span>
        )}
        {book.is_liked && (
          <span
            className="absolute right-2 top-2 text-lg text-white drop-shadow"
            aria-label="В избранном"
          >
            ♥
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-1 p-3">
        <h3 className="font-serif text-base leading-snug text-ink">{book.name}</h3>
        {authors && <p className="text-sm text-ink-soft">{authors}</p>}
        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="text-sm font-medium text-ink">{formatPrice(book.min_price)}</span>
          <span className="text-xs uppercase tracking-wide text-ink-faint">
            {book.language_display}
          </span>
        </div>
      </div>
    </Link>
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
