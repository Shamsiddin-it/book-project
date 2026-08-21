import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { ErrorNote, Spinner } from '../components/Spinner'

const fieldClass =
  'w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink'

export function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (loading) return <Spinner label="Проверяем сессию" />

  if (user) {
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={from ?? '/'} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(username, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from ?? '/', { replace: true })
    } catch (loginError) {
      setError(apiErrorMessage(loginError, 'Неверный логин или пароль'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 py-8">
      <h1 className="display-title text-3xl text-ink">Вход</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <ErrorNote message={error} />}

        <div className="space-y-1">
          <label htmlFor="username" className="text-sm text-ink-soft">
            Имя пользователя
          </label>
          <input
            id="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
            className={fieldClass}
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="password" className="text-sm text-ink-soft">
            Пароль
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
            className={fieldClass}
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-pill bg-ink py-2.5 text-sm text-cream transition hover:opacity-90 disabled:opacity-60"
        >
          {submitting ? 'Входим…' : 'Войти'}
        </button>
      </form>

      <p className="text-center text-sm text-ink-soft">
        Ещё нет аккаунта?{' '}
        <Link to="/register" className="text-ink underline">
          Зарегистрироваться
        </Link>
      </p>
    </div>
  )
}
