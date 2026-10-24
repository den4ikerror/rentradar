import { useEffect, useState } from 'react'
import { api } from '../api'

const STEPS = ['Локація', 'Орієнтир', 'Параметри', 'Додатково', 'Підтвердження']

export default function OnboardingWizard({ onComplete }) {
  const [step, setStep] = useState(0)
  const [regions, setRegions] = useState({})
  const [districts, setDistricts] = useState([])
  const [options, setOptions] = useState({ property_type: [], renovation_type: [], heating_type: [], min_lease_months: [] })
  const [form, setForm] = useState({
    region: '',
    city: '',
    district: '',
    street: '',
    street_radius_km: '',
    min_price: '',
    max_price: '',
    room_options: [],
    min_area: '',
    floor_not_first: false,
    floor_not_last: false,
    pets_allowed_only: false,
    property_types: [],
    renovation_type: '',
    is_new_building: false,
    furnished_only: false,
    heating_type: '',
    has_elevator: false,
    has_parking: false,
    has_balcony: false,
    internet_included: false,
    utilities_included: false,
    min_lease_months: '',
    deposit_required: '',
  })
  const [useStreetRadius, setUseStreetRadius] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getRegions().then(setRegions).catch(() => {})
    api.getFilterOptions().then(setOptions).catch(() => {})
  }, [])

  useEffect(() => {
    if (!form.city) { setDistricts([]); return }
    api.getDistricts(form.city).then(setDistricts).catch(() => setDistricts([]))
  }, [form.city])

  const togglePropertyType = (value) => setForm((f) => ({
    ...f,
    property_types: f.property_types.includes(value)
      ? f.property_types.filter((v) => v !== value)
      : [...f.property_types, value],
  }))

  const toggleRoomOption = (value) => setForm((f) => ({
    ...f,
    room_options: f.room_options.includes(value)
      ? f.room_options.filter((v) => v !== value)
      : [...f.room_options, value],
  }))

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const canProceed = () => {
    if (step === 0) return form.region && form.city
    return true
  }

  const next = () => {
    if (!canProceed()) {
      setError('Обери область і місто, щоб продовжити')
      return
    }
    setError(null)
    setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }
  const back = () => setStep((s) => Math.max(s - 1, 0))

  const submit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await onComplete({
        region: form.region,
        city: form.city,
        district: form.district || null,
        street: useStreetRadius ? form.street || null : null,
        street_radius_km: useStreetRadius && form.street_radius_km ? Number(form.street_radius_km) : null,
        min_price: form.min_price ? Number(form.min_price) : null,
        max_price: form.max_price ? Number(form.max_price) : null,
        room_options: form.room_options,
        min_area: form.min_area ? Number(form.min_area) : null,
        floor_not_first: form.floor_not_first,
        floor_not_last: form.floor_not_last,
        pets_allowed_only: form.pets_allowed_only,
        property_types: form.property_types,
        renovation_type: form.renovation_type || null,
        is_new_building: form.is_new_building,
        furnished_only: form.furnished_only,
        heating_type: form.heating_type || null,
        has_elevator: form.has_elevator,
        has_parking: form.has_parking,
        has_balcony: form.has_balcony,
        internet_included: form.internet_included,
        utilities_included: form.utilities_included,
        min_lease_months: form.min_lease_months ? Number(form.min_lease_months) : null,
        deposit_required: form.deposit_required === '' ? null : form.deposit_required === 'yes',
        scan_interval_minutes: 30,
      })
    } catch (e) {
      setError(e.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="glass-card filter-panel" style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', gap: 6, marginBottom: 18 }}>
        {STEPS.map((s, i) => (
          <div
            key={s}
            style={{
              flex: 1, height: 4, borderRadius: 2,
              background: i <= step ? 'var(--accent)' : 'var(--border)',
              transition: 'background 0.2s ease',
            }}
          />
        ))}
      </div>
      <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.3 }}>
        Крок {step + 1} з {STEPS.length} · {STEPS[step]}
      </p>

      {step === 0 && (
        <>
          <div className="filter-row">
            <label>Область</label>
            <select value={form.region} onChange={(e) => update('region', e.target.value)}>
              <option value="">Обери область</option>
              {Object.keys(regions).map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="filter-row">
            <label>Місто</label>
            {form.region && regions[form.region] ? (
              <select value={form.city} onChange={(e) => update('city', e.target.value)}>
                <option value="">Обери місто</option>
                {regions[form.region].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            ) : (
              <input value={form.city} onChange={(e) => update('city', e.target.value)} placeholder="Спочатку обери область" disabled={!form.region} />
            )}
          </div>
          <div className="filter-row">
            <label>Район міста {districts.length > 0 ? '' : "(необов'язково)"}</label>
            {districts.length > 0 ? (
              <select value={form.district} onChange={(e) => update('district', e.target.value)}>
                <option value="">Будь-який район</option>
                {districts.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            ) : (
              <input value={form.district} onChange={(e) => update('district', e.target.value)} placeholder={form.city ? 'Введи район вручну' : 'Спочатку обери місто'} disabled={!form.city} />
            )}
          </div>
        </>
      )}

      {step === 1 && (
        <>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 0 }}>
            Якщо тобі важливо жити не далі певної відстані від конкретного місця (університет, робота) —
            увімкни цю опцію. Актуально, наприклад, для студентів.
          </p>
          <div className="toggle-row">
            <label style={{ marginBottom: 0 }}>Обмежити відстань від вулиці</label>
            <button className={`ios-toggle ${useStreetRadius ? 'on' : ''}`} onClick={() => setUseStreetRadius((v) => !v)} />
          </div>

          {useStreetRadius && (
            <>
              <div className="filter-row" style={{ marginTop: 10 }}>
                <label>Вулиця-орієнтир</label>
                <input value={form.street} onChange={(e) => update('street', e.target.value)} placeholder="напр. вул. Січових Стрільців" />
              </div>
              <div className="filter-row">
                <label>Максимальна відстань, км</label>
                <div className="segmented">
                  {['1', '2', '5', '10'].map((km) => (
                    <button key={km} className={form.street_radius_km === km ? 'active' : ''} onClick={() => update('street_radius_km', km)}>
                      {km} км
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </>
      )}

      {step === 2 && (
        <>
          <div className="filter-grid">
            <div className="filter-row">
              <label>Ціна від, ₴</label>
              <input type="number" value={form.min_price} onChange={(e) => update('min_price', e.target.value)} placeholder="5000" />
            </div>
            <div className="filter-row">
              <label>Ціна до, ₴</label>
              <input type="number" value={form.max_price} onChange={(e) => update('max_price', e.target.value)} placeholder="15000" />
            </div>
          </div>

          <div className="filter-row">
            <label>Кількість кімнат (можна кілька)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {[1, 2, 3, 4, 5].map((r) => {
                const active = form.room_options.includes(r)
                return (
                  <button
                    key={r}
                    onClick={() => toggleRoomOption(r)}
                    className="action-btn"
                    style={active ? { background: 'var(--accent-soft)', color: 'var(--accent)', borderColor: 'var(--accent)' } : {}}
                  >
                    {active ? '✓ ' : ''}{r === 5 ? '5+' : r}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="filter-row">
            <label>Мінімальна площа, м²</label>
            <input type="number" value={form.min_area} onChange={(e) => update('min_area', e.target.value)} placeholder="30" />
          </div>

          <div className="filter-row">
            <div className="toggle-row">
              <label style={{ marginBottom: 0 }}>Не перший поверх</label>
              <button className={`ios-toggle ${form.floor_not_first ? 'on' : ''}`} onClick={() => update('floor_not_first', !form.floor_not_first)} />
            </div>
            <div className="toggle-row">
              <label style={{ marginBottom: 0 }}>Не останній поверх</label>
              <button className={`ios-toggle ${form.floor_not_last ? 'on' : ''}`} onClick={() => update('floor_not_last', !form.floor_not_last)} />
            </div>
            <div className="toggle-row">
              <label style={{ marginBottom: 0 }}>Дозволено з тваринами</label>
              <button className={`ios-toggle ${form.pets_allowed_only ? 'on' : ''}`} onClick={() => update('pets_allowed_only', !form.pets_allowed_only)} />
            </div>
          </div>
        </>
      )}

      {step === 3 && (
        <>
          <div className="filter-row">
            <label>Тип житла (можна кілька)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {options.property_type.map((o) => {
                const active = form.property_types.includes(o.value)
                return (
                  <button
                    key={o.value}
                    onClick={() => togglePropertyType(o.value)}
                    className="action-btn"
                    style={active ? { background: 'var(--accent-soft)', color: 'var(--accent)', borderColor: 'var(--accent)' } : {}}
                  >
                    {active ? '✓ ' : ''}{o.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="filter-row">
            <label>Стан ремонту</label>
            <div className="segmented">
              {[{ value: '', label: 'Будь-який' }, ...options.renovation_type].map((o) => (
                <button key={o.value} className={form.renovation_type === o.value ? 'active' : ''} onClick={() => update('renovation_type', o.value)}>{o.label}</button>
              ))}
            </div>
          </div>

          <div className="filter-row">
            <label>Опалення</label>
            <div className="segmented">
              {[{ value: '', label: 'Будь-яке' }, ...options.heating_type].map((o) => (
                <button key={o.value} className={form.heating_type === o.value ? 'active' : ''} onClick={() => update('heating_type', o.value)}>{o.label}</button>
              ))}
            </div>
          </div>

          <div className="filter-row">
            {[
              ['is_new_building', 'Новобудова'], ['furnished_only', 'Умебльована'],
              ['has_elevator', 'Є ліфт'], ['has_parking', 'Є паркомісце'],
              ['has_balcony', 'Є балкон/лоджія'], ['internet_included', 'Інтернет включено'],
              ['utilities_included', 'Комунальні включено'],
            ].map(([key, label]) => (
              <div className="toggle-row" key={key}>
                <label style={{ marginBottom: 0 }}>{label}</label>
                <button className={`ios-toggle ${form[key] ? 'on' : ''}`} onClick={() => update(key, !form[key])} />
              </div>
            ))}
          </div>

          <div className="filter-row">
            <label>Мінімальний термін оренди</label>
            <div className="segmented">
              {[{ value: '', label: 'Будь-який' }, ...options.min_lease_months.map((m) => ({ value: String(m), label: `${m} міс` }))].map((o) => (
                <button key={o.value} className={form.min_lease_months === o.value ? 'active' : ''} onClick={() => update('min_lease_months', o.value)}>{o.label}</button>
              ))}
            </div>
          </div>
        </>
      )}

      {step === 4 && (
        <div style={{ fontSize: 14, lineHeight: 1.7 }}>
          <p><strong>{form.city}</strong>{form.district ? `, ${form.district}` : ''}, {form.region}</p>
          {useStreetRadius && form.street && <p>Не далі {form.street_radius_km || '?'} км від «{form.street}»</p>}
          <p>Ціна: {form.min_price || '0'}–{form.max_price || '∞'} ₴</p>
          <p>Кімнат: {form.room_options.length > 0 ? form.room_options.join(', ') : 'будь-яка кількість'}{form.min_area ? ` · від ${form.min_area} м²` : ''}</p>
          {form.property_types.length > 0 && <p>Тип житла: {form.property_types.join(', ')}</p>}
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 12 }}>
            Пошук перевірить OLX, DOM.RIA, Lun.ua, Rieltor.ua та Flatfy.ua й надсилатиме нові пропозиції в Telegram.
          </p>
        </div>
      )}

      {error && <p style={{ color: 'var(--red)', fontSize: 13 }}>{error}</p>}

      <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
        {step > 0 && (
          <button className="action-btn" onClick={back} disabled={submitting}>Назад</button>
        )}
        {step < STEPS.length - 1 ? (
          <button className="btn-primary" onClick={next}>Далі</button>
        ) : (
          <button className="btn-primary" onClick={submit} disabled={submitting}>
            {submitting ? 'Запускаємо пошук...' : 'Почати пошук'}
          </button>
        )}
      </div>
    </div>
  )
}
