import { useEffect, useState } from 'react'
import { api } from '../api'

const SOURCES = ['OLX', 'DOM.RIA', 'Lun.ua', 'Rieltor.ua', 'Flatfy.ua']

export default function SearchingScreen({ filterId, onReady }) {
  const [dotIndex, setDotIndex] = useState(0)

  useEffect(() => {
    const anim = setInterval(() => setDotIndex((i) => (i + 1) % SOURCES.length), 900)
    return () => clearInterval(anim)
  }, [])

  useEffect(() => {
    let cancelled = false

    const poll = async () => {
      try {
        const progress = await api.getFilterProgress(filterId)
        if (!progress.is_scanning && !cancelled) {
          onReady()
          return
        }
      } catch {
        /* мовчки повторимо спробу — не хочемо лякати помилкою на екрані очікування */
      }
      if (!cancelled) setTimeout(poll, 4000)
    }

    poll()
    const fallback = setTimeout(() => !cancelled && onReady(), 45000)

    return () => {
      cancelled = true
      clearTimeout(fallback)
    }
  }, [filterId, onReady])

  return (
    <div className="app-shell" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '70vh' }}>
      <div className="glass-card filter-panel" style={{ textAlign: 'center', maxWidth: 360 }}>
        <div style={{ fontSize: 44, marginBottom: 12 }}>🔍</div>
        <h2 style={{ margin: '0 0 8px' }}>Шукаємо квартири...</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 18 }}>
          Перевіряємо {SOURCES[dotIndex]} — це займає до хвилини
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 6 }}>
          {SOURCES.map((s, i) => (
            <div
              key={s}
              style={{
                width: 8, height: 8, borderRadius: '50%',
                background: i === dotIndex ? 'var(--accent)' : 'var(--border)',
                transition: 'background 0.3s ease',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
