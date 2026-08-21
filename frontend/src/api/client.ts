import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'

import type { TokenPair } from './types'

const ACCESS_KEY = 'bookstore.access'
const REFRESH_KEY = 'bookstore.refresh'

/*
  Токены лежат в localStorage. Это стандартный вариант для SPA с JWT в заголовке
  Authorization, но у него есть цена: любой XSS получает доступ к токену.
  Полностью закрыть это можно только refresh-токеном в httpOnly-куке — тогда
  бэкенду нужен отдельный набор ручек. Пока остаёмся здесь осознанно.
*/

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  save(tokens: TokenPair) {
    localStorage.setItem(ACCESS_KEY, tokens.access)
    localStorage.setItem(REFRESH_KEY, tokens.refresh)
  },
  saveAccess(access: string) {
    localStorage.setItem(ACCESS_KEY, access)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

/** Слушатели разлогина — AuthContext подписывается, чтобы сбросить состояние. */
type Listener = () => void
const sessionEndedListeners = new Set<Listener>()

export function onSessionEnded(listener: Listener): () => void {
  sessionEndedListeners.add(listener)
  return () => {
    sessionEndedListeners.delete(listener)
  }
}

function endSession() {
  tokenStore.clear()
  sessionEndedListeners.forEach((listener) => listener())
}

export const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

/** Отдельный клиент для обновления токена — иначе интерсептор зациклится. */
const refreshClient = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.access
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/*
  На бэкенде включены ROTATE_REFRESH_TOKENS и BLACKLIST_AFTER_ROTATION: каждое
  обновление выдаёт новую пару и заносит старый refresh в чёрный список.
  Значит два параллельных обновления убьют сессию — второе придёт со уже
  отозванным токеном. Поэтому обновление всегда одно на всех: остальные запросы
  ждут этот же промис.
*/
let refreshInFlight: Promise<string> | null = null

function refreshAccessToken(): Promise<string> {
  if (refreshInFlight) return refreshInFlight

  const refresh = tokenStore.refresh
  if (!refresh) return Promise.reject(new Error('Нет refresh-токена'))

  refreshInFlight = refreshClient
    .post<TokenPair>('/accounts/token/refresh/', { refresh })
    .then((response) => {
      const { access, refresh: rotated } = response.data
      // Ротация может вернуть новый refresh — его обязательно нужно сохранить,
      // иначе следующее обновление уйдёт с уже отозванным токеном.
      if (rotated) {
        tokenStore.save({ access, refresh: rotated })
      } else {
        tokenStore.saveAccess(access)
      }
      return access
    })
    .finally(() => {
      refreshInFlight = null
    })

  return refreshInFlight
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined

    if (error.response?.status !== 401 || !config || config._retried) {
      return Promise.reject(error)
    }

    // На самом обновлении 401 означает, что сессия кончилась по-настоящему.
    if (config.url?.includes('/accounts/token/')) {
      endSession()
      return Promise.reject(error)
    }

    if (!tokenStore.refresh) {
      return Promise.reject(error)
    }

    config._retried = true
    try {
      const access = await refreshAccessToken()
      config.headers.Authorization = `Bearer ${access}`
      return api.request(config)
    } catch (refreshError) {
      endSession()
      return Promise.reject(refreshError)
    }
  },
)

/** Достаёт человекочитаемое сообщение из ответа DRF. */
export function apiErrorMessage(error: unknown, fallback = 'Что-то пошло не так'): string {
  if (!axios.isAxiosError(error)) return fallback

  const data = error.response?.data
  if (typeof data === 'string') return data

  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>
    // DRF кладёт общие ошибки в detail, а полевые — под именами полей.
    if (typeof record.detail === 'string') return record.detail

    const first = Object.values(record)[0]
    if (Array.isArray(first) && typeof first[0] === 'string') return first[0]
    if (typeof first === 'string') return first
  }

  return error.message || fallback
}
