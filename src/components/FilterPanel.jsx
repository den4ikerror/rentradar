import { useEffect, useState } from 'react'
import { api } from '../api'

function SavedFilterRow({ filter, onToggle, onDelete }) {
  const [busy, setBusy] = useState(false)

  const wrap = async (fn) => {
    setBusy(true)
    try {
      await fn()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="toggle-row" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 10, marginBottom: 10 }}>
      <div>
        <div style={{ fontWeight: 600, fontSize: 14 }}>
          {filter.city}{filter.district ? `, ${filter.district}` : ''}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {filter.min_price || '0'}–{filter.max_price || '∞'} ₴
          {filter.room_options?.length > 0 ? ` · ${filter.room_options.join(', ')}-кімн.` : ''}
          {filter.street ? ` · до ${filter.street_radius_km} км від «${filter.street}»` : ''}
          {' · кожні '}{filter.scan_interval_minutes} хв
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button className="action-btn hide" style={{ padding: '6px 10px', fontSize: 12 }} disabled={busy} onClick={() => wrap(() => onDelete(filter.id))}>
          Видалити
        </button>
        <button className={`ios-toggle ${filter.is_active ? 'on' : ''}`} disabled={busy} onClick={() => wrap(() => onToggle(filter.id))} />
      </div>
    </div>
  )
}

const EMPTY_FORM = {
  region: '', city: '', district: '', street: '', street_radius_km: '',
  min_price: '', max_price: '', room_options: [], min_area: '',
  floor_not_first: false, floor_not_last: false, pets_allowed_only: false,
  property_types: [], renovation_type: '', is_new_building: false, furnished_only: false,
  heating_type: '', has_elevator: false, has_parking: false, has_balcony: false,
  internet_included: false, utilities_included: false,
  min_lease_months: '', deposit_required: '',
  scan_interval_minutes: 60,
}

function ToggleField({ label, value, onChange }) {
  return (
    <div className="toggle-row">
      <label style={{ marginBottom: 0 }}>{label}</label>
      <button className={`ios-toggle ${value ? 'on' : ''}`} onClick={() => onChange(!value)} />
    </div>
  )
}

export default function FilterPanel({ filters, onSubmit, onToggle, onDelete }) {
  const [regions, setRegions] = useState({})
  const [districts, setDistricts] = useState([])
  const [options, setOptions] = useState({ property_type: [], renovation_type: [], heating_type: [], min_lease_months: [] })
  const [form, setForm] = useState(EMPTY_FORM)
  const [useStreetRadius, setUseStreetRadius] = useState(false)
  const [showForm, setShowForm] = useState(filters.length === 0)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getRegions().then(setRegions).catch(() => {})
    api.getFilterOptions().then(setOptions).catch(() => {})
  }, [])

  useEffect(() => {
    if (!form.city) { setDistricts([]); return }
    api.getDistricts(form.city).then(setDistricts).catch(() => setDistricts([]))
  }, [form.city])

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }))

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

  const submit = async () => {
    if (!form.city.trim()) {
      setError('Вкажи місто пошуку')
      return
    }
    setError(null)
    setSaving(true)
    try {
      await onSubmit({
        region: form.region || null,
        city: form.city.trim(),
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
        scan_interval_minutes: Number(form.scan_interval_minutes),
      })
      setForm(EMPTY_FORM)
      setUseStreetRadius(false)
      setShowForm(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      {filters.length > 0 && (
        <div className="glass-card filter-panel">
          <label style={{ display: 'block', marginBottom: 10 }}>Твої фільтри</label>
          {filters.map((f) => (
            <SavedFilterRow key={f.id} filter={f} onToggle={onToggle} onDelete={onDelete} />
          ))}
          {!showForm && (
            <button className="btn-primary" style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }} onClick={() => setShowForm(true)}>
              + Додати ще один фільтр
            </button>
          )}
        </div>
      )}

      {showForm && (
        <div className="glass-card filter-panel">
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
              <input value={form.city} onChange={(e) => update('city', e.target.value)} placeholder="Львів" />
            )}
          </div>

          <div className="filter-row">
            <label>Район {districts.length > 0 ? '' : "(необов'язково)"}</label>
            {districts.length > 0 ? (
              <select value={form.district} onChange={(e) => update('district', e.target.value)}>
                <option value="">Будь-який район</option>
                {districts.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            ) : (
              <input value={form.district} onChange={(e) => update('district', e.target.value)} placeholder={form.city ? 'Для цього міста введи район вручну' : 'Спочатку обери місто'} disabled={!form.city} />
            )}
          </div>

          <div className="filter-row">
            <ToggleField label="Обмежити відстань від вулиці" value={useStreetRadius} onChange={setUseStreetRadius} />
          </div>

          {useStreetRadius && (
            <>
              <div className="filter-row">
                <label>Вулиця-орієнтир</label>
                <input value={form.street} onChange={(e) => update('street', e.target.value)} placeholder="напр. вул. Пекарська" />
              </div>
              <div className="filter-row">
                <label>Максимальна відстань, км</label>
                <div className="segmented">
                  {['1', '2', '5', '10'].map((km) => (
                    <button key={km} className={form.street_radius_km === km ? 'active' : ''} onClick={() => update('street_radius_km', km)}>{km} км</button>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="filter-grid">
            <div className="filter-row">
              <label>Ціна від</label>
              <input type="number" value={form.min_price} onChange={(e) => update('min_price', e.target.value)} placeholder="5000" />
            </div>
            <div className="filter-row">
              <label>Ціна до</label>
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
            <ToggleField label="Не перший поверх" value={form.floor_not_first} onChange={(v) => update('floor_not_first', v)} />
            <ToggleField label="Не останній поверх" value={form.floor_not_last} onChange={(v) => update('floor_not_last', v)} />
          </div>

          <button
            className="action-btn"
            style={{ width: '100%', marginTop: 4, marginBottom: showAdvanced ? 14 : 0 }}
            onClick={() => setShowAdvanced((v) => !v)}
          >
            {showAdvanced ? '− Приховати додаткові критерії' : '+ Ще критерії (тип житла, ремонт, комунікації, умови)'}
          </button>

          {showAdvanced && (
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
                <ToggleField label="Новобудова" value={form.is_new_building} onChange={(v) => update('is_new_building', v)} />
                <ToggleField label="Умебльована" value={form.furnished_only} onChange={(v) => update('furnished_only', v)} />
                <ToggleField label="Дозволено з тваринами" value={form.pets_allowed_only} onChange={(v) => update('pets_allowed_only', v)} />
                <ToggleField label="Є ліфт" value={form.has_elevator} onChange={(v) => update('has_elevator', v)} />
                <ToggleField label="Є паркомісце" value={form.has_parking} onChange={(v) => update('has_parking', v)} />
                <ToggleField label="Є балкон/лоджія" value={form.has_balcony} onChange={(v) => update('has_balcony', v)} />
                <ToggleField label="Інтернет включено" value={form.internet_included} onChange={(v) => update('internet_included', v)} />
                <ToggleField label="Комунальні включено" value={form.utilities_included} onChange={(v) => update('utilities_included', v)} />
              </div>

              <div className="filter-row">
                <label>Мінімальний термін оренди</label>
                <div className="segmented">
                  {[{ value: '', label: 'Будь-який' }, ...options.min_lease_months.map((m) => ({ value: String(m), label: `${m} міс` }))].map((o) => (
                    <button key={o.value} className={form.min_lease_months === o.value ? 'active' : ''} onClick={() => update('min_lease_months', o.value)}>{o.label}</button>
                  ))}
                </div>
              </div>

              <div className="filter-row">
                <label>Застава</label>
                <div className="segmented">
                  {[{ value: '', label: 'Байдуже' }, { value: 'no', label: 'Без застави' }, { value: 'yes', label: 'Із заставою' }].map((o) => (
                    <button key={o.value} className={form.deposit_required === o.value ? 'active' : ''} onClick={() => update('deposit_required', o.value)}>{o.label}</button>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="filter-row" style={{ marginTop: 14 }}>
            <label>Інтервал сканування</label>
            <div className="segmented">
              {[30, 60, 120].map((m) => (
                <button key={m} className={Number(form.scan_interval_minutes) === m ? 'active' : ''} onClick={() => update('scan_interval_minutes', m)}>
                  {m < 60 ? `${m} хв` : `${m / 60} год`}
                </button>
              ))}
            </div>
          </div>

          {error && <p style={{ color: 'var(--red)', fontSize: 13, marginTop: -6 }}>{error}</p>}

          <div style={{ display: 'flex', gap: 10 }}>
            {filters.length > 0 && (
              <button className="action-btn" onClick={() => setShowForm(false)} disabled={saving}>Скасувати</button>
            )}
            <button className="btn-primary" onClick={submit} disabled={saving}>
              {saving ? 'Зберігаємо...' : 'Зберегти фільтр'}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
