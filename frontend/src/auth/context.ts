import { createContext } from 'react'

import type { RegisterPayload } from '../api/endpoints'
import type { Me } from '../api/types'

export interface AuthValue {
  user: Me | null
  /** true, пока восстанавливаем сессию из сохранённого токена. */
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

/*
  Контекст вынесен из AuthContext.tsx намеренно: если файл экспортирует и
  компонент, и что-то ещё, Fast Refresh перестаёт обновлять его на лету
  и перезагружает страницу целиком при каждой правке.
*/
export const AuthContext = createContext<AuthValue | null>(null)
