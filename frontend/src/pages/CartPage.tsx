import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { checkout, fetchCart, removeFromCart } from '../api/endpoints'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'

function formatPrice(value: string | number) {
  const amount = Number(value)
  return Number.isNaN(amount)
    ? String(value)
    : `${amount.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽`
}

export function CartPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const cartQuery = useQuery({ queryKey: ['cart'], queryFn: fetchCart })

  const removeMutation = useMutation({
    mutationFn: (itemId: number) => removeFromCart(itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cart'] }),
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  const checkoutMutation = useMutation({
    mutationFn: checkout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] })
      queryClient.invalidateQueries({ queryKey: ['shelf'] })
      navigate('/shelf')
    },
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  if (cartQuery.isPending) return <Spinner label="Открываем корзину" />
  if (cartQuery.isError) return <ErrorNote message={apiErrorMessage(cartQuery.error)} />

  const cart = cartQuery.data

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl text-ink">Корзина</h1>

      {error && <ErrorNote message={error} />}

      {cart && cart.results.length > 0 ? (
        <>
          <ul className="space-y-3">
            {cart.results.map((item) => (
              <li
                key={item.id}
                className="flex items-center gap-4 rounded-card border border-line bg-paper-raised p-3"
              >
                <div
                  className="h-20 w-14 shrink-0 overflow-hidden rounded"
                  style={{ backgroundColor: item.edition.accent_color || 'var(--color-line)' }}
                >
                  {item.edition.cover && (
                    <img src={item.edition.cover} alt="" className="size-full object-cover" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <Link
                    to={`/books/${item.edition.book_id}`}
                    className="font-serif text-lg text-ink hover:underline"
                  >
                    {item.edition.book_name}
                  </Link>
                  <p className="text-sm text-ink-soft">{item.edition.format_display}</p>
                </div>

                <span className="text-sm text-ink">{formatPrice(item.price)}</span>

                <button
                  type="button"
                  onClick={() => removeMutation.mutate(item.id)}
                  className="rounded-full border border-line px-3 py-1.5 text-sm text-ink-soft hover:text-ink"
                >
                  Убрать
                </button>
              </li>
            ))}
          </ul>

          <div className="flex flex-wrap items-center justify-between gap-4 rounded-card border border-line bg-paper-raised p-4">
            <div>
              <p className="text-sm text-ink-soft">Итого по прайсу</p>
              <p className="font-serif text-2xl text-ink">{formatPrice(cart.total)}</p>
              {cart.purchases_are_free && (
                <p className="mt-1 text-sm text-ink-soft">
                  Сейчас книги выдаются бесплатно — оплата не потребуется.
                </p>
              )}
            </div>

            <button
              type="button"
              onClick={() => checkoutMutation.mutate()}
              disabled={checkoutMutation.isPending}
              className="rounded-full bg-ink px-6 py-2.5 text-sm text-paper transition hover:opacity-90 disabled:opacity-60"
            >
              {checkoutMutation.isPending
                ? 'Оформляем…'
                : cart.purchases_are_free
                  ? 'Забрать бесплатно'
                  : 'Оформить заказ'}
            </button>
          </div>
        </>
      ) : (
        <EmptyState title="Корзина пуста" hint="Добавьте издания из каталога" />
      )}
    </div>
  )
}
