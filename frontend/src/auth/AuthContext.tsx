import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { onSessionEnded, tokenStore } from '../api/client'
import * as apiEndpoints from '../api/endpoints'
import type { Me } from '../api/types'
import { AuthContext } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null)
  // Ждать нечего, если сохранённого токена нет — сразу отдаём готовое состояние,
  // чтобы не гонять лишний рендер через эффект.
  const [loading, setLoading] = useState(
    () => Boolean(tokenStore.access || tokenStore.refresh),
  )

  // Токен пережил перезагрузку страницы — восстанавливаем пользователя.
  // Пока это не закончится, защищённые маршруты не должны решать,
  // пускать или нет: иначе будет мигание на страницу входа.
  useEffect(() => {
    if (!tokenStore.access && !tokenStore.refresh) return

    let cancelled = false
    apiEndpoints
      .fetchMe()
      .then((me) => {
        if (!cancelled) setUser(me)
      })
      .catch(() => {
        if (!cancelled) setUser(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Интерсептор сообщает, что refresh окончательно протух.
  useEffect(() => onSessionEnded(() => setUser(null)), [])

  const login = useCallback(async (username: string, password: string) => {
    setUser(await apiEndpoints.login(username, password))
  }, [])

  const register = useCallback(async (payload: apiEndpoints.RegisterPayload) => {
    setUser(await apiEndpoints.register(payload))
  }, [])

  const logout = useCallback(async () => {
    await apiEndpoints.logout()
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    setUser(await apiEndpoints.fetchMe())
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
