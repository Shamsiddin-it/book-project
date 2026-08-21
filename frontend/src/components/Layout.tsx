import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

function navClass({ isActive }: { isActive: boolean }) {
  return [
    'rounded-full px-3 py-1.5 text-sm transition',
    isActive ? 'bg-ink text-paper' : 'text-ink-soft hover:text-ink',
  ].join(' ')
}

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-paper/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
          <Link to="/" className="font-serif text-xl tracking-tight text-ink">
            Полка
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navClass}>
              Каталог
            </NavLink>
            {user && (
              <>
                <NavLink to="/shelf" className={navClass}>
                  Моя полка
                </NavLink>
                <NavLink to="/recommendations" className={navClass}>
                  Для вас
                </NavLink>
              </>
            )}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <>
                <NavLink to="/cart" className={navClass}>
                  Корзина
                </NavLink>
                <span className="hidden text-sm text-ink-soft sm:inline">{user.username}</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-full border border-line px-3 py-1.5 text-sm text-ink-soft transition hover:text-ink"
                >
                  Выйти
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>
                  Войти
                </NavLink>
                <Link
                  to="/register"
                  className="rounded-full bg-ink px-3 py-1.5 text-sm text-paper transition hover:opacity-90"
                >
                  Регистрация
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-line py-6 text-center text-sm text-ink-faint">
        Книжная полка для книголюбов
      </footer>
    </div>
  )
}
