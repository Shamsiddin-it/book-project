import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { ErrorNote, Spinner } from '../components/Spinner'

const fieldClass =
  'w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-ink'

export function RegisterPage() {
  const { user, loading, register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (loading) return <Spinner label="Проверяем сессию" />
  if (user) return <Navigate to="/" replace />

  function update(field: keyof typeof form) {
    return (event: React.ChangeEvent<HTMLInputElement>) =>
      setForm((previous) => ({ ...previous, [field]: event.target.value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (form.password !== form.password2) {
      setError('Пароли не совпадают')
      return
    }

    setSubmitting(true)
    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (registerError) {
      setError(apiErrorMessage(registerError, 'Не удалось зарегистрироваться'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 py-8">
      <h1 className="display-title text-3xl text-ink">Регистрация</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <ErrorNote message={error} />}

        <div className="space-y-1">
          <label htmlFor="username" className="text-sm text-ink-soft">
            Имя пользователя
          </label>
          <input
            id="username"
            value={form.username}
            onChange={update('username')}
            autoComplete="username"
            required
            className={fieldClass}
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="email" className="text-sm text-ink-soft">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={form.email}
            onChange={update('email')}
            autoComplete="email"
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
            value={form.password}
            onChange={update('password')}
            autoComplete="new-password"
            required
            className={fieldClass}
          />
          <p className="text-xs text-ink-faint">
            Не короче 8 символов, не только цифры и не слишком простой.
          </p>
        </div>

        <div className="space-y-1">
          <label htmlFor="password2" className="text-sm text-ink-soft">
            Повторите пароль
          </label>
          <input
            id="password2"
            type="password"
            value={form.password2}
            onChange={update('password2')}
            autoComplete="new-password"
            required
            className={fieldClass}
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-pill bg-ink py-2.5 text-sm text-cream transition hover:opacity-90 disabled:opacity-60"
        >
          {submitting ? 'Создаём аккаунт…' : 'Зарегистрироваться'}
        </button>
      </form>

      <p className="text-center text-sm text-ink-soft">
        Уже есть аккаунт?{' '}
        <Link to="/login" className="text-ink underline">
          Войти
        </Link>
      </p>
    </div>
  )
}
