import { api, tokenStore } from './client'
import type {
  BlogPost,
  BlogPostCard,
  BlogTag,
  BookDetail,
  BookListItem,
  CartResponse,
  Category,
  Comment,
  GamificationProfile,
  LanguageOption,
  LeaderboardEntry,
  Me,
  Note,
  NoteKind,
  Order,
  Paginated,
  PublicUser,
  RatingSummary,
  ReaderManifest,
  RecommendationResponse,
  Review,
  ShelfItem,
  ShelfStatus,
  SimilarBooksResponse,
  TokenPair,
  TrophyProgress,
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
  on_sale?: boolean
  min_rating?: number
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

/* ------------------------------------------------------------- отзывы */

export async function fetchBookReviews(bookId: number) {
  const { data } = await api.get<Paginated<Review>>(`/reviews/books/${bookId}/`)
  return data
}

export async function fetchRatingSummary(bookId: number): Promise<RatingSummary> {
  const { data } = await api.get<RatingSummary>(`/reviews/books/${bookId}/summary/`)
  return data
}

export async function submitReview(payload: {
  book: number
  rating: number
  text?: string
  has_spoilers?: boolean
}) {
  const { data } = await api.post<Review>('/reviews/', payload)
  return data
}

export async function updateReview(id: number, payload: { rating?: number; text?: string }) {
  const { data } = await api.patch<Review>(`/reviews/${id}/`, payload)
  return data
}

/* -------------------------------------------------------- геймификация */

export async function fetchMyGamification(): Promise<GamificationProfile> {
  const { data } = await api.get<GamificationProfile>('/gamification/me/')
  return data
}

export async function fetchTrophies(): Promise<TrophyProgress[]> {
  const { data } = await api.get<TrophyProgress[]>('/gamification/trophies/')
  return data
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  const { data } = await api.get<LeaderboardEntry[]>('/gamification/leaderboard/')
  return data
}

/* ---------------------------------------------------------------- блог */

export async function fetchBlogPosts(params: { search?: string; tag?: string } = {}) {
  const { data } = await api.get<Paginated<BlogPostCard>>('/blog/posts/', {
    params: {
      search: params.search || undefined,
      // Бэкенд фильтрует по slug тега.
      tags__slug: params.tag || undefined,
    },
  })
  return data
}

export async function fetchBlogPost(slug: string): Promise<BlogPost> {
  const { data } = await api.get<BlogPost>(`/blog/posts/${slug}/`)
  return data
}

export async function fetchBlogTags(): Promise<BlogTag[]> {
  const { data } = await api.get<BlogTag[]>('/blog/tags/')
  return data
}

/* ------------------------------------------------------------ соцчасть */

export async function fetchComments(bookId: number) {
  const { data } = await api.get<Paginated<Comment>>('/social/comments/', {
    params: { book: bookId },
  })
  return data
}

export async function postComment(payload: {
  book: number
  text: string
  parent?: number
  character?: number
  has_spoilers?: boolean
}) {
  const { data } = await api.post<Comment>('/social/comments/', payload)
  return data
}

export async function updateComment(id: number, text: string) {
  const { data } = await api.patch<Comment>(`/social/comments/${id}/`, { text })
  return data
}

export async function deleteComment(id: number) {
  await api.delete(`/social/comments/${id}/`)
}

export async function toggleCommentLike(id: number) {
  const { data } = await api.post<{ liked: boolean; likes_count: number }>(
    `/social/comments/${id}/toggle_like/`,
  )
  return data
}

export async function toggleFollow(userId: number) {
  const { data } = await api.post<{ following: boolean; followers_count: number }>(
    `/social/users/${userId}/follow/`,
  )
  return data
}

export async function fetchFollowers(userId: number) {
  const { data } = await api.get<Paginated<PublicUser>>(`/social/users/${userId}/followers/`)
  return data
}

export async function fetchFollowing(userId: number) {
  const { data } = await api.get<Paginated<PublicUser>>(`/social/users/${userId}/following/`)
  return data
}

/* --------------------------------------------------- чужие пользователи */

export async function fetchPublicUser(userId: number): Promise<PublicUser> {
  const { data } = await api.get<PublicUser>(`/accounts/users/${userId}/`)
  return data
}

export async function fetchPublicShelf(userId: number) {
  const { data } = await api.get<Paginated<ShelfItem>>(`/shelf/users/${userId}/`)
  return data
}

export async function fetchPublicGamification(userId: number): Promise<GamificationProfile> {
  const { data } = await api.get<GamificationProfile>(`/gamification/users/${userId}/`)
  return data
}

/* ------------------------------------------------- заметки и цитаты */

export async function fetchMyNotes(params: { book?: number; kind?: NoteKind } = {}) {
  const { data } = await api.get<Paginated<Note>>('/notes/', { params })
  return data
}

export async function createNote(payload: {
  book: number
  text: string
  kind?: NoteKind
  page?: number
  is_public?: boolean
  has_spoilers?: boolean
}) {
  const { data } = await api.post<Note>('/notes/', payload)
  return data
}

export async function deleteNote(id: number) {
  await api.delete(`/notes/${id}/`)
}

/** Публичные цитаты и заметки по книге — их видно всем на странице книги. */
export async function fetchBookNotes(bookId: number, kind?: NoteKind) {
  const { data } = await api.get<Paginated<Note>>(`/notes/books/${bookId}/`, {
    params: kind ? { kind } : undefined,
  })
  return data
}

export async function fetchUserNotes(userId: number) {
  const { data } = await api.get<Paginated<Note>>(`/notes/users/${userId}/`)
  return data
}
