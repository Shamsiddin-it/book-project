import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { Spinner } from '../components/Spinner'
import { useAuth } from './useAuth'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  // Пока сессия восстанавливается из сохранённого токена, решать рано:
  // иначе при перезагрузке страницы пользователя выбрасывало бы на вход.
  if (loading) {
    return <Spinner label="Загружаем профиль" />
  }

  if (!user) {
    // Запоминаем, куда шли, чтобы вернуть туда после входа.
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}
