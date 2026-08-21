import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, apiErrorMessage } from '../api/client'
import { fetchReaderManifest, saveReadingProgress } from '../api/endpoints'
import { ErrorNote, Spinner } from '../components/Spinner'

/**
 * Содержимое книги защищено: эндпоинт требует заголовок Authorization,
 * поэтому подставить ссылку прямо в <iframe src> нельзя — браузер пойдёт
 * туда без токена и получит 401. Тянем файл запросом и отдаём просмотрщику
 * blob-ссылку.
 */
function useProtectedContent(contentUrl: string | null, editionId: number) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!contentUrl) return

    let objectUrl: string | null = null
    let cancelled = false

    api
      .get(`/reader/${editionId}/content/`, { responseType: 'blob' })
      .then((response) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(response.data as Blob)
        setBlobUrl(objectUrl)
      })
      .catch((loadError) => {
        if (!cancelled) setError(apiErrorMessage(loadError, 'Не удалось открыть книгу'))
      })

    return () => {
      cancelled = true
      // Освобождаем память: без revoke blob висит до перезагрузки вкладки.
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [contentUrl, editionId])

  return { blobUrl, error }
}

export function ReaderPage() {
  const { editionId: rawId } = useParams()
  const editionId = Number(rawId)

  // null означает «пользователь ещё не трогал ползунок» — тогда показываем
  // прогресс из манифеста. Без этого понадобился бы эффект-синхронизатор.
  const [draftProgress, setDraftProgress] = useState<number | null>(null)
  const [saved, setSaved] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const lastSavedRef = useRef(0)

  const manifestQuery = useQuery({
    queryKey: ['reader', editionId],
    queryFn: () => fetchReaderManifest(editionId),
    enabled: Number.isFinite(editionId),
  })

  const manifest = manifestQuery.data
  const progress = draftProgress ?? manifest?.progress_percent ?? 0

  const { blobUrl, error: contentError } = useProtectedContent(
    manifest?.content_url ?? null,
    editionId,
  )

  // Восстанавливаем место в аудио: позиция хранится строкой, для аудио это секунды.
  useEffect(() => {
    if (!manifest?.is_audio || !audioRef.current || !manifest.position) return
    const seconds = Number(manifest.position)
    if (!Number.isNaN(seconds)) audioRef.current.currentTime = seconds
  }, [manifest])

  async function persist(percent: number, position?: string) {
    try {
      await saveReadingProgress(editionId, {
        progress_percent: percent,
        ...(position !== undefined ? { position } : {}),
      })
      setSaved(new Date().toLocaleTimeString('ru-RU'))
    } catch (saveError) {
      setSaved(null)
      console.error(apiErrorMessage(saveError))
    }
  }

  function handleAudioTime() {
    const audio = audioRef.current
    if (!audio || !audio.duration) return

    const percent = Math.round((audio.currentTime / audio.duration) * 100)
    setDraftProgress(percent)

    // Пишем на сервер не чаще раза в 15 секунд — иначе завалим API
    // запросами по событию timeupdate, которое стреляет несколько раз в секунду.
    if (audio.currentTime - lastSavedRef.current >= 15) {
      lastSavedRef.current = audio.currentTime
      void persist(percent, String(Math.floor(audio.currentTime)))
    }
  }

  if (manifestQuery.isPending) return <Spinner label="Открываем книгу" />

  if (manifestQuery.isError) {
    return (
      <div className="space-y-4">
        <ErrorNote message={apiErrorMessage(manifestQuery.error)} />
        <p className="text-sm text-ink-soft">
          Книгу нужно сначала получить.{' '}
          <Link to="/" className="text-ink underline">
            Вернуться в каталог
          </Link>
        </p>
      </div>
    )
  }

  if (!manifest) return null

  return (
    <div
      style={{ ['--accent' as string]: manifest.accent_color || '#6b4f3a' }}
      className="space-y-5"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h1 className="display-title text-2xl text-ink">{manifest.book_name}</h1>
          <p className="text-sm text-ink-soft">
            {manifest.authors.map((author) => author.name).join(', ')} ·{' '}
            {manifest.format_display}
          </p>
        </div>
        <Link
          to={`/books/${manifest.book_id}`}
          className="text-sm text-ink-soft underline hover:text-ink"
        >
          К странице книги
        </Link>
      </div>

      {contentError && <ErrorNote message={contentError} />}

      {manifest.is_audio ? (
        manifest.audio_link ? (
          <audio
            ref={audioRef}
            controls
            src={manifest.audio_link}
            onTimeUpdate={handleAudioTime}
            className="w-full"
          />
        ) : (
          <ErrorNote message="У этого издания нет аудиодорожки" />
        )
      ) : blobUrl ? (
        <iframe
          src={blobUrl}
          title={manifest.book_name}
          className="h-[75vh] w-full rounded-card border border-line bg-white"
        />
      ) : manifest.content_url ? (
        <Spinner label="Загружаем текст" />
      ) : (
        <ErrorNote message="У этого издания нет файла для чтения" />
      )}

      <div className="flex flex-wrap items-center gap-4 rounded-card border border-line bg-white p-4">
        <label htmlFor="progress" className="text-sm text-ink-soft">
          Прогресс
        </label>
        <input
          id="progress"
          type="range"
          min={0}
          max={100}
          value={progress}
          onChange={(event) => setDraftProgress(Number(event.target.value))}
          onPointerUp={() => void persist(progress)}
          className="flex-1 accent-[var(--accent)]"
        />
        <span className="w-12 text-right text-sm text-ink">{progress}%</span>

        <button
          type="button"
          onClick={() => {
            setDraftProgress(100)
            void persist(100)
          }}
          className="accent-surface rounded-pill px-4 py-1.5 text-sm text-white"
        >
          Дочитал
        </button>

        {saved && <span className="text-xs text-ink-faint">Сохранено в {saved}</span>}
      </div>

      {/*
        Полноценная постраничная навигация по EPUB требует отдельного движка
        (epub.js). Пока PDF показывается встроенным просмотрщиком браузера,
        а прогресс отмечается вручную — этого достаточно, чтобы полка знала,
        что читается и что дочитано.
      */}
    </div>
  )
}
