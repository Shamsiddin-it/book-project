import { type FormEvent, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Logo } from './ui'
import { pillClass } from './styles'

const NAV = [
  { to: '/', label: 'Book Shop', end: true },
  { to: '/sale', label: 'Books on Sale' },
  { to: '/blog', label: 'Blogs & News' },
  { to: '/achievements', label: 'Level & Trophy' },
]

function navClass({ isActive }: { isActive: boolean }) {
  return [
    'tracked text-[11px] font-semibold transition',
    isActive ? 'text-ink' : 'text-ink-soft hover:text-ink',
  ].join(' ')
}

function IconLink({
  to,
  label,
  children,
}: {
  to: string
  label: string
  children: React.ReactNode
}) {
  return (
    <Link
      to={to}
      aria-label={label}
      title={label}
      className="grid size-9 place-items-center rounded-full text-ink transition hover:bg-white/70"
    >
      {children}
    </Link>
  )
}

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  function handleSearch(event: FormEvent) {
    event.preventDefault()
    navigate(query.trim() ? `/?search=${encodeURIComponent(query.trim())}` : '/')
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-line/70 bg-cream/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-3 px-4 py-3">
          <Logo />

          <form onSubmit={handleSearch} className="order-3 w-full sm:order-none sm:flex-1">
            <label className="sr-only" htmlFor="site-search">
              Поиск по каталогу
            </label>
            <div className="flex items-center gap-2 rounded-pill border-2 border-blush-soft bg-white px-4 py-1.5 focus-within:border-blush">
              <span aria-hidden className="text-ink-faint">
                ⌕
              </span>
              <input
                id="site-search"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Название, автор, жанр"
                className="w-full bg-transparent text-sm outline-none placeholder:text-ink-faint"
              />
            </div>
          </form>

          <div className="ml-auto flex items-center gap-1">
            <IconLink to="/?language=en" label="Книги на других языках">
              <span aria-hidden>🌐</span>
            </IconLink>

            {user ? (
              <>
                <IconLink to="/cart" label="Корзина">
                  <span aria-hidden>🛒</span>
                </IconLink>
                <IconLink to="/shelf" label="Моя полка">
                  <span aria-hidden className="text-blush">
                    ♥
                  </span>
                </IconLink>
                <IconLink to="/achievements" label={`Профиль: ${user.username}`}>
                  <span aria-hidden>👤</span>
                </IconLink>
                <button type="button" onClick={handleLogout} className={pillClass('outline', 'ml-1')}>
                  Выйти
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={pillClass('outline')}>
                  Войти
                </NavLink>
                <Link to="/register" className={pillClass('mint', 'ml-1')}>
                  Регистрация
                </Link>
              </>
            )}
          </div>
        </div>

        <nav className="mx-auto flex max-w-6xl flex-wrap justify-center gap-x-8 gap-y-2 px-4 pb-3">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
          {user && (
            <NavLink to="/recommendations" className={navClass}>
              Для вас
            </NavLink>
          )}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="mt-12 border-t border-line/70 bg-white/50">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-4 py-8 text-center">
          <Logo className="text-xl" />
          <nav className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-ink-soft">
            <Link to="/" className="hover:text-ink">
              Каталог
            </Link>
            <Link to="/sale" className="hover:text-ink">
              Скидки
            </Link>
            <Link to="/blog" className="hover:text-ink">
              Блог
            </Link>
            <Link to="/achievements" className="hover:text-ink">
              Достижения
            </Link>
          </nav>
          <p className="text-xs text-ink-faint">
            Книжная полка для книголюбов — читайте, отмечайте, обсуждайте.
          </p>
        </div>
      </footer>
    </div>
  )
}
