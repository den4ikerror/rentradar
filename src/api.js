const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('rentfinder_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  } catch (e) {
    throw new Error('Немає з\'єднання з сервером. Перевір інтернет і спробуй ще раз.')
  }

  if (res.status === 401) {
    localStorage.removeItem('rentfinder_token')
    localStorage.removeItem('rentfinder_user')
    throw new Error('Сесія закінчилась, увійди ще раз')
  }


  if (!res.ok) {
    let detail = `Помилка сервера (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      /* тіло не JSON — лишаємо дефолтне повідомлення */
    }
    throw new Error(detail)
  }
  return res.json()
}

function saveSession({ user, token }) {
  localStorage.setItem('rentfinder_token', token)
  localStorage.setItem('rentfinder_user', JSON.stringify(user))
  return user
}

export const api = {
  registerUser: async (name) =>
    saveSession(await request('/api/users/register', { method: 'POST', body: JSON.stringify({ name }) })),

  logout: () => {
    localStorage.removeItem('rentfinder_token')
    localStorage.removeItem('rentfinder_user')
  },

  getRegions: () => request('/api/reference/regions'),
  getDistricts: (city) => request(`/api/reference/districts?city=${encodeURIComponent(city)}`),
  getFilterOptions: () => request('/api/reference/filter-options'),
  getLogs: () => request('/api/reference/logs'),


  getFilters: () => request('/api/filters'),
  createFilter: (payload) => request('/api/filters', { method: 'POST', body: JSON.stringify(payload) }),
  updateFilter: (filterId, payload) => request(`/api/filters/${filterId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  toggleFilter: (filterId) => request(`/api/filters/${filterId}/toggle`, { method: 'PATCH' }),
  deleteFilter: (filterId) => request(`/api/filters/${filterId}`, { method: 'DELETE' }),
  getFilterProgress: (filterId) => request(`/api/filters/${filterId}/progress`),

  getListings: ({ city, offset = 0, limit = 20, onlyLiked = false, onlyOutsideRadius = false } = {}) => {
    const params = new URLSearchParams({ offset, limit })
    if (city) params.set('city', city)
    if (onlyLiked) params.set('only_liked', 'true')
    if (onlyOutsideRadius) params.set('only_outside_radius', 'true')
    return request(`/api/listings?${params.toString()}`)
  },
  setListingStatus: (listingId, status) =>
    request(`/api/listings/${listingId}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  clearListingStatus: (listingId) =>
    request(`/api/listings/${listingId}/status`, { method: 'DELETE' }),
}
