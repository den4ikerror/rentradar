const SOURCE_LABELS = {
  olx: 'OLX',
  domria: 'DOM.RIA',
  lunua: 'Lun.ua',
  rieltor: 'Rieltor.ua',
  flatfy: 'Flatfy.ua',
}

const PROPERTY_TYPE_LABELS = { studio: 'Студія', room: 'Кімната', house: 'Будинок', apartment: 'Квартира' }
const HEATING_LABELS = { autonomous: 'Автономне опалення', central: 'Центральне опалення', electric: 'Електроопалення' }

function collectBadges(listing) {
  const badges = []
  if (listing.property_type && listing.property_type !== 'apartment') {
    badges.push(PROPERTY_TYPE_LABELS[listing.property_type])
  }
  if (listing.is_new_building) badges.push('🏗️ Новобудова')
  if (listing.furnished === true) badges.push('🛋️ З меблями')
  if (listing.heating_type) badges.push(`🔥 ${HEATING_LABELS[listing.heating_type]}`)
  if (listing.has_elevator === true) badges.push('🛗 Ліфт')
  if (listing.has_parking === true) badges.push('🚗 Паркомісце')
  if (listing.has_balcony === true) badges.push('🌤️ Балкон')
  if (listing.internet_included === true) badges.push('📶 Інтернет вкл.')
  if (listing.utilities_included === true) badges.push('💡 Комунальні вкл.')
  if (listing.deposit_required === false) badges.push('✅ Без застави')
  return badges
}

export default function ApartmentCard({ listing, isLiked, onStatusChange }) {
  const openSource = () => window.open(listing.source_url, '_blank', 'noopener,noreferrer')

  const toggleLike = (e) => {
    e.stopPropagation()
    onStatusChange(listing.id, isLiked ? 'none' : 'liked')
  }

  const hide = (e) => {
    e.stopPropagation()
    onStatusChange(listing.id, 'hidden')
  }

  const handleImgError = (e) => {
    e.target.style.display = 'none'
    e.target.nextSibling?.style?.setProperty('display', 'flex')
  }

  const badges = collectBadges(listing)

  return (
    <div className="glass-card tile-card" onClick={openSource} role="button" tabIndex={0}>
      <div className="tile-photo-wrap">
        {listing.photos?.[0] ? (
          <>
            <img className="tile-photo" src={listing.photos[0]} alt={listing.title} loading="lazy" onError={handleImgError} />
            <div className="tile-photo tile-photo-placeholder" style={{ display: 'none', position: 'absolute', inset: 0 }}>🏠</div>
          </>
        ) : (
          <div className="tile-photo tile-photo-placeholder">🏠</div>
        )}

        <button className={`heart-btn ${isLiked ? 'active' : ''}`} onClick={toggleLike} aria-label="Зберегти">
          {isLiked ? '♥' : '♡'}
        </button>

        <span className="source-badge">{SOURCE_LABELS[listing.source] || listing.source}</span>
      </div>

      <div className="tile-body">
        <div className="tile-price-row">
          <span className="tile-price">{listing.price.toLocaleString('uk-UA')} ₴</span>
          {listing.price_vs_market_pct !== null && listing.price_vs_market_pct !== undefined && (
            <span
              className="tile-deviation"
              style={{ color: listing.price_vs_market_pct < 0 ? 'var(--green)' : 'var(--red)' }}
            >
              {listing.price_vs_market_pct < 0 ? '↓' : '↑'}{Math.abs(listing.price_vs_market_pct)}%
            </span>
          )}
        </div>
        <p className="tile-address">
          {listing.district ? `${listing.district}` : ''}
          {listing.district && listing.street ? ' · ' : ''}
          {listing.street || (!listing.district ? listing.city : '')}
          {listing.rooms ? ` · ${listing.rooms}-кімн.` : ''}
          {listing.area ? ` · ${listing.area} м²` : ''}
          {listing.distance_km !== null && listing.distance_km !== undefined ? ` · 📍 ${listing.distance_km} км` : ''}
        </p>

        {badges.length > 0 && (
          <div className="tile-badges">
            {badges.map((b) => <span key={b} className="tile-badge">{b}</span>)}
          </div>
        )}

        <button className="tile-hide-btn" onClick={hide}>Приховати</button>
      </div>
    </div>
  )
}
