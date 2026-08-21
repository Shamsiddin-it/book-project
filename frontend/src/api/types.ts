/**
 * Типы ответов API. Сняты с сериализаторов Django — если меняешь сериализатор,
 * поправь и здесь, иначе TypeScript будет уверенно врать о форме данных.
 */

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface UserBrief {
  id: number
  username: string
  photo: string | null
}

export interface PublicUser extends UserBrief {
  bio: string
  followers_count: number
  following_count: number
  is_shelf_public: boolean
}

export interface Me {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string | null
  photo: string | null
  birthdate: string | null
  bio: string
  role: 'admin' | 'customer'
  is_shelf_public: boolean
  followers_count: number
  following_count: number
  date_joined: string
}

export interface Author {
  id: number
  name: string
  description: string
  image: string | null
  books_amount: number
}

export interface Category {
  id: number
  name: string
  image: string | null
  subcategory_of: number | null
  subcategories: { id: number; name: string }[]
}

export type EditionFormat = 'soft' | 'hard' | 'ebook' | 'audio'

export interface Edition {
  id: number
  book: number
  format: EditionFormat
  format_display: string
  cover: string | null
  isbn: string
  publisher: string
  published_year: number
  pages: number | null
  price: string
  is_physical: boolean
  is_active: boolean
  audio_link: string | null
}

export interface MoodboardImage {
  id: number
  book: number
  image: string
  position: number
}

export interface Character {
  id: number
  book: number
  name: string
  image: string | null
  signature_quote: string
  is_main: boolean
}

/** Облегчённый вид для каталога. */
export interface BookListItem {
  id: number
  name: string
  language: string
  language_display: string
  authors: Author[]
  accent_color: string
  cover: string | null
  min_price: string | null
  is_liked: boolean
  is_read: boolean
}

/** Полная страница книги. */
export interface BookDetail {
  id: number
  name: string
  description: string
  language: string
  language_display: string
  authors: Author[]
  categories: Category[]
  publishing_year: number
  accent_color: string
  editions: Edition[]
  moodboard: MoodboardImage[]
  characters: Character[]
  is_active: boolean
  created_at: string
  is_liked: boolean
  is_read: boolean
}

export interface LanguageOption {
  code: string
  name: string
  books_count: number
}

export type ShelfStatus = 'want' | 'reading' | 'read'

export interface ShelfEdition {
  id: number
  book_id: number
  book_name: string
  accent_color: string
  authors: Author[]
  format: EditionFormat
  format_display: string
  cover: string | null
}

export interface ShelfItem {
  id: number
  edition: ShelfEdition
  status: ShelfStatus
  status_display: string
  is_owned: boolean
  progress_percent: number
  position: string
  last_read_at: string | null
  added_at: string
  finished_at: string | null
}

export interface Comment {
  id: number
  user: UserBrief
  book: number
  character: number | null
  parent: number | null
  text: string
  has_spoilers: boolean
  likes_count: number
  is_liked: boolean
  replies: Comment[]
  created_at: string
  updated_at: string
}

export type NoteKind = 'note' | 'quote'

export interface Note {
  id: number
  user: UserBrief
  book: number
  kind: NoteKind
  kind_display: string
  text: string
  page: number | null
  is_public: boolean
  has_spoilers: boolean
  created_at: string
  updated_at: string
}

export interface CartItem {
  id: number
  edition: ShelfEdition
  price: string
  added_at: string
}

export interface CartResponse {
  count: number
  total: string | number
  purchases_are_free: boolean
  results: CartItem[]
}

export interface OrderItem {
  id: number
  edition: ShelfEdition
  unit_price: string
}

export interface Order {
  id: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
  status_display: string
  provider: 'free' | 'stripe'
  total: string
  amount_paid: string
  is_free: boolean
  items: OrderItem[]
  created_at: string
  paid_at: string | null
}

/** Ответ ридера при открытии издания. */
export interface ReaderManifest {
  edition_id: number
  book_id: number
  book_name: string
  authors: Author[]
  accent_color: string
  language: string
  format: EditionFormat
  format_display: string
  is_audio: boolean
  content_url: string | null
  audio_link: string | null
  content_type: string | null
  size_bytes: number | null
  progress_percent: number
  position: string
  status: ShelfStatus
  last_read_at: string | null
}

/** На чём построена подборка — это подписывает блок на фронте. */
export type RecommendationBasis = 'collaborative' | 'taste' | 'popular' | 'mixed'

export interface RecommendationResponse {
  basis: RecommendationBasis
  count: number
  results: BookListItem[]
}

export interface SimilarBooksResponse {
  book_id: number
  count: number
  results: BookListItem[]
}

export interface TokenPair {
  access: string
  refresh: string
}
