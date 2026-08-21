import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { Layout } from './components/Layout'
import { EmptyState } from './components/Spinner'
import { AchievementsPage } from './pages/AchievementsPage'
import { BlogPage, BlogPostPage } from './pages/BlogPage'
import { BookPage } from './pages/BookPage'
import { CartPage } from './pages/CartPage'
import { CatalogPage } from './pages/CatalogPage'
import { LoginPage } from './pages/LoginPage'
import { ReaderPage } from './pages/ReaderPage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import { RegisterPage } from './pages/RegisterPage'
import { SalePage } from './pages/SalePage'
import { ShelfPage } from './pages/ShelfPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      // 401 разбирает интерсептор: он обновляет токен и повторяет запрос сам.
      // Повторять здесь ещё раз — значит дублировать чужую работу.
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<CatalogPage />} />
              <Route path="books/:id" element={<BookPage />} />
              <Route path="sale" element={<SalePage />} />
              <Route path="blog" element={<BlogPage />} />
              <Route path="blog/:slug" element={<BlogPostPage />} />
              <Route path="achievements" element={<AchievementsPage />} />
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />

              <Route
                path="shelf"
                element={
                  <ProtectedRoute>
                    <ShelfPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="recommendations"
                element={
                  <ProtectedRoute>
                    <RecommendationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="cart"
                element={
                  <ProtectedRoute>
                    <CartPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="read/:editionId"
                element={
                  <ProtectedRoute>
                    <ReaderPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="*"
                element={<EmptyState title="Такой страницы нет" hint="Проверьте адрес" />}
              />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
