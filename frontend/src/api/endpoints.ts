import { api, tokenStore } from './client'
import type {
  BookDetail,
  BookListItem,
  CartResponse,
  Category,
  LanguageOption,
  Me,
  Order,
  Paginated,
  ReaderManifest,
  RecommendationResponse,
  ShelfItem,
  ShelfStatus,
  SimilarBooksResponse,
  TokenPair,
} from './types'

/* ---------------------------------------------------------------- аккаунты */

export async function login(username: string, password: string): Promise<Me> {
  const { data } = await api.post<TokenPair>('/accounts/token/', { username, password })
  tokenStore.save(data)
  return fetchMe()
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  password2: string
}

export async function register(payload: RegisterPayload): Promise<Me> {
  await api.post('/accounts/register/', payload)
  return login(payload.username, payload.password)
}

export async function logout(): Promise<void> {
  const refresh = tokenStore.refresh
  if (refresh) {
    // Отзываем токен на сервере. Если не вышло — всё равно чистим локально:
    // пользователь нажал «выйти», и он должен выйти.
    await api.post('/accounts/logout/', { refresh }).catch(() => undefined)
  }
  tokenStore.clear()
}

export async function fetchMe(): Promise<Me> {
  const { data } = await api.get<Me>('/accounts/me/')
  return data
}

/* ----------------------------------------------------------------- каталог */

export interface CatalogParams {
  search?: string
  language?: string
  categories?: number
  ordering?: string
  page?: number
}

export async function fetchBooks(params: CatalogParams = {}) {
  const { data } = await api.get<Paginated<BookListItem>>('/books/', { params })
  return data
}

export async function fetchBook(id: number): Promise<BookDetail> {
  const { data } = await api.get<BookDetail>(`/books/${id}/`)
  return data
}

export async function toggleLike(bookId: number) {
  const { data } = await api.post<{ liked: boolean; likes_count: number }>(
    `/books/${bookId}/toggle_like/`,
  )
  return data
}

export async function fetchCategories() {
  const { data } = await api.get<Paginated<Category>>('/categories/')
  return data.results
}

export async function fetchLanguages(): Promise<LanguageOption[]> {
  const { data } = await api.get<LanguageOption[]>('/languages/')
  return data
}

/* --------------------------------------------------------- рекомендации */

export async function fetchRecommendations(language?: string) {
  const { data } = await api.get<RecommendationResponse>('/recommendations/', {
    params: language ? { language } : undefined,
  })
  return data
}

export async function fetchSimilarBooks(bookId: number) {
  const { data } = await api.get<SimilarBooksResponse>(`/recommendations/similar/${bookId}/`)
  return data
}

/* -------------------------------------------------------------------- полка */

export async function fetchShelf(params: { status?: ShelfStatus } = {}) {
  const { data } = await api.get<Paginated<ShelfItem>>('/shelf/', { params })
  return data
}

export async function addToShelf(editionId: number) {
  const { data } = await api.post<ShelfItem>('/shelf/', { edition_id: editionId })
  return data
}

export async function updateShelfItem(id: number, patch: Partial<Pick<ShelfItem, 'status'>>) {
  const { data } = await api.patch<ShelfItem>(`/shelf/${id}/`, patch)
  return data
}

export async function removeFromShelf(id: number) {
  await api.delete(`/shelf/${id}/`)
}

/* ----------------------------------------------------------------- покупки */

export async function fetchCart(): Promise<CartResponse> {
  const { data } = await api.get<CartResponse>('/purchase/cart/')
  return data
}

export async function addToCart(editionId: number) {
  const { data } = await api.post('/purchase/cart/', { edition_id: editionId })
  return data
}

export async function removeFromCart(itemId: number) {
  await api.delete(`/purchase/cart/${itemId}/`)
}

export async function checkout(): Promise<Order> {
  const { data } = await api.post<Order>('/purchase/checkout/')
  return data
}

/** Получить книгу одним действием, минуя корзину. Пока выдача бесплатная. */
export async function acquireEdition(editionId: number): Promise<Order> {
  const { data } = await api.post<Order>(`/purchase/editions/${editionId}/acquire/`)
  return data
}

export async function fetchOrders() {
  const { data } = await api.get<Paginated<Order>>('/purchase/orders/')
  return data
}

/* ------------------------------------------------------------------- ридер */

export async function fetchReaderManifest(editionId: number): Promise<ReaderManifest> {
  const { data } = await api.get<ReaderManifest>(`/reader/${editionId}/`)
  return data
}

export async function saveReadingProgress(
  editionId: number,
  progress: { progress_percent?: number; position?: string },
) {
  const { data } = await api.patch(`/reader/${editionId}/progress/`, progress)
  return data
}
