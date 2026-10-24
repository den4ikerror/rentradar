import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import OnboardingWizard from './components/OnboardingWizard'
import SearchingScreen from './components/SearchingScreen'
import FilterPanel from './components/FilterPanel'
import ApartmentCard from './components/ApartmentCard'

const PAGE_SIZE = 20

export default function App() {
  const user = { id: 1, name: 'Гість' }
  const [filters, setFilters] = useState(null)
  const [pendingFilterId, setPendingFilterId] = useState(null)

  const [tab, setTab] = useState('feed')
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [totalFound, setTotalFound] = useState(0)
  const [feedError, setFeedError] = useState(null)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [logLines, setLogLines] = useState([])
  const [showLogs, setShowLogs] = useState(true)
  const [radiusTab, setRadiusTab] = useState('within')

  const fetchLogs = async () => {
    try {
      const res = await api.getLogs()
      setLogLines(res.logs || [])
    } catch (e) {
      setLogLines([`Помилка завантаження логів: ${e.message}`])
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const goOnline = () => setIsOnline(true)
    const goOffline = () => setIsOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  const loadFilters = useCallback(async () => {
    try {
      const data = await api.getFilters()
      setFilters(data)
      return data
    } catch (e) {
      setFeedError(e.message)
      setFilters([])
    }
  }, [])

  useEffect(() => {
    loadFilters().catch((e) => setFeedError(e.message))
  }, [loadFilters])

  const loadListings = useCallback(async (offset = 0, targetTab = tab, currentRadiusTab = radiusTab) => {
    offset === 0 ? setLoading(true) : setLoadingMore(true)
    setFeedError(null)
    try {
      const page = await api.getListings({
        offset,
        limit: PAGE_SIZE,
        onlyLiked: targetTab === 'saved',
        onlyOutsideRadius: targetTab === 'feed' && currentRadiusTab === 'outside',
      })
      setListings((prev) => (offset === 0 ? page.items : [...prev, ...page.items]))
      setHasMore(page.has_more)
      setTotalFound(page.total)
    } catch (e) {
      setFeedError(e.message)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [tab, radiusTab])

  useEffect(() => {
    if (filters && filters.length > 0 && !pendingFilterId) {
      loadListings(0, tab, radiusTab)
    }
  }, [filters, tab, radiusTab, pendingFilterId, loadListings])

  const handleOnboardingComplete = async (payload) => {
    const created = await api.createFilter(payload)
    await loadFilters()
    setPendingFilterId(created.id)
  }

  const handleSearchReady = () => {
    setPendingFilterId(null)
    setTab('feed')
  }

  const handleCreateFilter = async (payload) => {
    await api.createFilter(payload)
    await loadFilters()
    await loadListings(0, tab)
  }
  const handleToggleFilter = async (filterId) => { await api.toggleFilter(filterId); await loadFilters() }
  const handleDeleteFilter = async (filterId) => { await api.deleteFilter(filterId); await loadFilters() }

  const handleStatusChange = async (listingId, status) => {
    const isRemovingFromView = status === 'hidden' || (tab === 'saved' && status === 'none')
    if (isRemovingFromView) {
      setListings((prev) => prev.filter((l) => l.id !== listingId))
    } else {
      setListings((prev) => prev.map((l) => (l.id === listingId ? { ...l, user_status: status === 'none' ? null : status } : l)))
    }
    try {
      if (status === 'none') {
        await api.clearListingStatus(listingId)
      } else {
        await api.setListingStatus(listingId, status)
      }
    } catch (e) {
      setFeedError(`Не вдалось зберегти дію: ${e.message}`)
      loadListings(0, tab)
    }
  }

  return (
    <div className="app-container-split">
      {/* Ліва колонка: Логи в реальному часі */}
      {showLogs ? (
        <div className="log-sidebar">
          <div className="log-sidebar-header">
            <span>📋 Логи бекенду (наживо)</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={fetchLogs}
                style={{
                  background: 'var(--accent-soft)',
                  border: 'none',
                  borderRadius: 6,
                  padding: '4px 8px',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--accent)',
                  cursor: 'pointer',
                }}
              >
                Оновити
              </button>
              <button
                onClick={() => setShowLogs(false)}
                style={{
                  background: 'rgba(255,59,48,0.1)',
                  border: 'none',
                  borderRadius: 6,
                  padding: '4px 8px',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--red)',
                  cursor: 'pointer',
                }}
              >
                Сховати
              </button>
            </div>
          </div>
          <div className="log-sidebar-content">
            {logLines.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: 20 }}>Очікування логів...</div>
            ) : (
              logLines.map((line, idx) => (
                <div key={idx} style={{ marginBottom: 4, borderBottom: '1px solid var(--border)', paddingBottom: 2 }}>
                  {line}
                </div>
              ))
            )}
          </div>
          <div style={{ padding: '8px 14px', borderTop: '1px solid var(--border)', fontSize: 10, color: 'var(--text-secondary)', textAlign: 'center' }}>
            Оновлення кожні 2 сек
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowLogs(true)}
          style={{
            position: 'fixed',
            left: 16,
            bottom: 24,
            zIndex: 100,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            padding: '10px 16px',
            fontSize: 13,
            fontWeight: 700,
            color: 'var(--accent)',
            boxShadow: 'var(--shadow)',
            cursor: 'pointer',
            backdropFilter: 'blur(20px)',
          }}
        >
          📋 Показати логи
        </button>
      )}

      {/* Права колонка: Основний інтерфейс */}
      <div className="main-content-area">
        {!isOnline && <OfflineBanner />}

        {filters === null ? (
          <div className="empty-state">Завантаження...</div>
        ) : filters.length === 0 && !pendingFilterId ? (
          <div>
            <div className="navbar"><div><h1>RentFinder</h1><div className="subtitle">Пошук оренди без обмежень</div></div></div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Налаштуй перший пошук — і система почне автоматично знаходити для тебе квартири.
            </p>
            <OnboardingWizard onComplete={handleOnboardingComplete} />
          </div>
        ) : pendingFilterId ? (
          <SearchingScreen filterId={pendingFilterId} onReady={handleSearchReady} />
        ) : (
          <>
            <div className="navbar">
              <div>
                <h1>RentFinder</h1>
                <div className="subtitle">
                  {tab === 'feed' && `Знайдено ${totalFound} квартир`}
                  {tab === 'saved' && 'Збережені квартири'}
                  {tab === 'filters' && 'Керування фільтрами'}
                </div>
              </div>
              <div className="segmented" style={{ width: 180 }}>
                <button className={tab === 'feed' ? 'active' : ''} onClick={() => setTab('feed')}>Стрічка</button>
                <button className={tab === 'saved' ? 'active' : ''} onClick={() => setTab('saved')}>♥</button>
                <button className={tab === 'filters' ? 'active' : ''} onClick={() => setTab('filters')}>Фільтри</button>
              </div>
            </div>

            {tab === 'filters' && (
              <FilterPanel filters={filters} onSubmit={handleCreateFilter} onToggle={handleToggleFilter} onDelete={handleDeleteFilter} />
            )}

            {tab === 'feed' && (
              <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                <button
                  onClick={() => setRadiusTab('within')}
                  style={{
                    flex: 1, padding: '8px 12px', borderRadius: 10, border: 'none',
                    background: radiusTab === 'within' ? 'var(--accent)' : 'var(--bg-elevated)',
                    color: radiusTab === 'within' ? 'white' : 'var(--text-primary)',
                    fontWeight: 600, fontSize: 13, cursor: 'pointer', boxShadow: 'var(--shadow)'
                  }}
                >
                  🎯 У заданому радіусі
                </button>
                <button
                  onClick={() => setRadiusTab('outside')}
                  style={{
                    flex: 1, padding: '8px 12px', borderRadius: 10, border: 'none',
                    background: radiusTab === 'outside' ? 'var(--accent)' : 'var(--bg-elevated)',
                    color: radiusTab === 'outside' ? 'white' : 'var(--text-primary)',
                    fontWeight: 600, fontSize: 13, cursor: 'pointer', boxShadow: 'var(--shadow)'
                  }}
                >
                  🗺️ За межами радіусу
                </button>
              </div>
            )}

            {(tab === 'feed' || tab === 'saved') && (
              <>
                {loading && <div className="empty-state">Завантаження...</div>}

                {!loading && feedError && (
                  <div className="empty-state">
                    <p style={{ color: 'var(--red)' }}>{feedError}</p>
                    <button className="btn-primary" style={{ width: 'auto', padding: '10px 24px' }} onClick={() => loadListings(0, tab)}>
                      Спробувати ще раз
                    </button>
                  </div>
                )}

                {!loading && !feedError && listings.length === 0 && (
                  <div className="empty-state">
                    {tab === 'saved'
                      ? 'Тут з\'являться квартири, які ти позначиш сердечком.'
                      : 'За твоїми фільтрами поки немає оголошень. Перевір логи зліва, щоб побачити статус сканування джерел.'}
                  </div>
                )}

                {!loading && !feedError && listings.length > 0 && (
                  <div className="tile-grid">
                    {listings.map((l) => (
                      <ApartmentCard key={l.id} listing={l} isLiked={l.user_status === 'liked'} onStatusStatusChange={handleStatusChange} onStatusChange={handleStatusChange} />
                    ))}
                  </div>
                )}

                {!loading && !feedError && hasMore && (
                  <button
                    className="btn-primary"
                    style={{ background: 'var(--accent-soft)', color: 'var(--accent)', marginTop: 14 }}
                    disabled={loadingMore}
                    onClick={() => loadListings(listings.length, tab)}
                  >
                    {loadingMore ? 'Завантаження...' : 'Показати ще'}
                  </button>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function OfflineBanner() {
  return (
    <div style={{
      position: 'sticky', top: 0, zIndex: 20, background: 'var(--orange)', color: 'white',
      textAlign: 'center', fontSize: 13, fontWeight: 600, padding: '8px', margin: '0 -16px 8px',
    }}>
      Немає з'єднання з інтернетом
    </div>
  )
}
