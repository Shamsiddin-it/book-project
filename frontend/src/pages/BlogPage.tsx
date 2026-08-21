import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { apiErrorMessage } from '../api/client'
import { fetchBlogPost, fetchBlogPosts, fetchBlogTags } from '../api/endpoints'
import { EmptyState, ErrorNote, Spinner } from '../components/Spinner'
import { SectionHeading } from '../components/ui'
import { pillClass } from '../components/styles'

function formatDate(value: string | null) {
  if (!value) return ''
  return new Date(value).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function BlogPage() {
  const [params, setParams] = useSearchParams()
  const tag = params.get('tag') ?? ''

  const tagsQuery = useQuery({
    queryKey: ['blog-tags'],
    queryFn: fetchBlogTags,
    staleTime: 5 * 60 * 1000,
  })

  const postsQuery = useQuery({
    queryKey: ['blog-posts', tag],
    queryFn: () => fetchBlogPosts({ tag: tag || undefined }),
  })

  function setTag(value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set('tag', value)
    else next.delete('tag')
    setParams(next)
  }

  return (
    <div className="space-y-6">
      <SectionHeading>Blogs &amp; News</SectionHeading>

      {tagsQuery.data && tagsQuery.data.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2">
          <button
            type="button"
            onClick={() => setTag('')}
            className={[
              'rounded-pill px-3 py-1.5 text-xs font-semibold transition',
              tag === '' ? 'bg-ink text-cream' : 'border border-line text-ink-soft',
            ].join(' ')}
          >
            Все темы
          </button>
          {tagsQuery.data.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTag(item.slug)}
              className={[
                'rounded-pill px-3 py-1.5 text-xs font-semibold transition',
                tag === item.slug
                  ? 'bg-ink text-cream'
                  : 'border border-line text-ink-soft hover:text-ink',
              ].join(' ')}
            >
              {item.name}
            </button>
          ))}
        </div>
      )}

      {postsQuery.isError && <ErrorNote message={apiErrorMessage(postsQuery.error)} />}

      {postsQuery.isPending ? (
        <Spinner label="Загружаем материалы" />
      ) : postsQuery.data && postsQuery.data.results.length > 0 ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {postsQuery.data.results.map((post) => (
            <article
              key={post.id}
              className="flex flex-col overflow-hidden rounded-card bg-white shadow-sm ring-1 ring-ink/5 transition hover:-translate-y-1 hover:shadow-lg"
            >
              <Link to={`/blog/${post.slug}`}>
                <div className="aspect-16/9 bg-mint-wash">
                  {post.cover && (
                    <img
                      src={post.cover}
                      alt=""
                      loading="lazy"
                      className="size-full object-cover"
                    />
                  )}
                </div>
              </Link>

              <div className="flex flex-1 flex-col gap-2 p-4">
                <div className="flex flex-wrap gap-1">
                  {post.tags.map((item) => (
                    <span
                      key={item.id}
                      className="rounded-pill bg-blush-wash px-2 py-0.5 text-[10px] font-semibold text-ink-soft"
                    >
                      {item.name}
                    </span>
                  ))}
                </div>

                <Link to={`/blog/${post.slug}`}>
                  <h3 className="text-base font-bold leading-snug text-ink hover:underline">
                    {post.title}
                  </h3>
                </Link>

                {post.excerpt && (
                  <p className="line-clamp-3 text-sm text-ink-soft">{post.excerpt}</p>
                )}

                <p className="mt-auto pt-2 text-xs text-ink-faint">
                  {post.author?.username}
                  {post.author && post.published_at ? ' · ' : ''}
                  {formatDate(post.published_at)}
                </p>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          title="Материалов пока нет"
          hint="Редакция ещё ничего не опубликовала"
        />
      )}
    </div>
  )
}

export function BlogPostPage() {
  const { slug } = useParams()

  const query = useQuery({
    queryKey: ['blog-post', slug],
    queryFn: () => fetchBlogPost(slug as string),
    enabled: Boolean(slug),
  })

  if (query.isPending) return <Spinner label="Открываем материал" />
  if (query.isError) return <ErrorNote message={apiErrorMessage(query.error)} />
  if (!query.data) return <EmptyState title="Материал не найден" />

  const post = query.data

  return (
    <article className="mx-auto max-w-3xl space-y-6">
      <Link to="/blog" className="text-sm text-ink-soft hover:text-ink">
        ← Ко всем материалам
      </Link>

      <header className="space-y-3">
        <h1 className="display-title text-3xl text-ink sm:text-4xl">{post.title}</h1>
        <p className="text-sm text-ink-faint">
          {post.author?.username}
          {post.author && post.published_at ? ' · ' : ''}
          {formatDate(post.published_at)}
        </p>
      </header>

      {post.cover && (
        <img src={post.cover} alt="" className="w-full rounded-card object-cover" />
      )}

      {post.excerpt && (
        <p className="border-l-4 border-blush pl-4 text-lg text-ink-soft">{post.excerpt}</p>
      )}

      {/*
        Текст выводится как обычные абзацы, а не через dangerouslySetInnerHTML:
        материалы приходят из админки, и вставлять оттуда сырой HTML в страницу
        означало бы открыть XSS для любого, у кого есть доступ к редактору.
      */}
      <div className="space-y-4 text-base leading-relaxed text-ink">
        {post.body.split(/\n{2,}/).map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>

      <div className="flex flex-wrap gap-2 pt-4">
        {post.tags.map((item) => (
          <Link
            key={item.id}
            to={`/blog?tag=${item.slug}`}
            className={pillClass('outline', 'text-xs')}
          >
            {item.name}
          </Link>
        ))}
      </div>
    </article>
  )
}
