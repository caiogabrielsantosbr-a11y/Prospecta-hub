/**
 * API client for communicating with the FastAPI backend.
 */
import useConfigStore from '../store/useConfigStore'
import { supabase } from '../config/supabase'

/**
 * Get the base URL from the configuration store
 * @returns {string} The configured backend URL
 * @throws {Error} If backend URL is not configured
 */
function getBaseUrl() {
  const { apiUrl } = useConfigStore.getState()
  if (!apiUrl) {
    throw new Error('Backend URL not configured. Please configure in Admin Panel.')
  }
  return apiUrl
}

/**
 * Get the current Supabase session token for backend auth
 */
async function getAuthHeader() {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    return { 'Authorization': `Bearer ${session.access_token}` }
  }
  return {}
}

/**
 * Make an HTTP request to the backend API
 * @param {string} path - API endpoint path (e.g., '/tasks')
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Response JSON
 */
async function request(path, options = {}) {
  const baseUrl = getBaseUrl()
  const url = `${baseUrl}/api${path}`
  const authHeader = await getAuthHeader()

  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...authHeader, ...options.headers },
      ...options,
    })
    
    if (!res.ok) {
      // Handle specific HTTP error codes
      if (res.status === 404) {
        throw new Error('Endpoint não encontrado - verifique a versão do backend')
      }
      if (res.status === 500) {
        throw new Error('Erro interno do backend - verifique os logs')
      }
      
      const err = await res.text()
      throw new Error(err)
    }
    
    return res.json()
  } catch (error) {
    // Add timestamp to all error logs
    const timestamp = new Date().toISOString()
    console.error(`[${timestamp}] API Error:`, error)
    
    // Handle network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Backend não respondeu - verifique se o túnel está ativo')
    }
    
    // Handle timeout errors
    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      throw new Error('Timeout ao conectar com o backend - verifique a conexão')
    }
    
    // Handle CORS errors
    if (error.message.includes('CORS') || error.message.includes('cors')) {
      throw new Error('Erro de CORS - adicione a URL do Vercel no CORS_ORIGINS do backend')
    }
    
    throw error
  }
}

export const api = {
  // ── Dashboard ──
  getDashboardStats: () => request('/dashboard/stats'),

  // ── Tasks ──
  getTasks: () => request('/tasks'),
  getActiveTasks: () => request('/tasks/active'),
  getTask: (id) => request(`/tasks/${id}`),
  pauseTask: (id) => request(`/tasks/${id}/pause`, { method: 'POST' }),
  resumeTask: (id) => request(`/tasks/${id}/resume`, { method: 'POST' }),
  stopTask: (id) => request(`/tasks/${id}/stop`, { method: 'POST' }),

  // ── Emails ──
  startEmailExtraction: (domains, delay, proxy) =>
    request('/emails/start', {
      method: 'POST',
      body: JSON.stringify({ domains, delay, proxy }),
    }),
  getEmailResults: (taskId) => request(`/emails/results/${taskId}`),

  // ── GMap ──
  startGmapExtraction: (searchTerm, cities, delay, headless = true, extractEmails = true) =>
    request('/gmap/start', {
      method: 'POST',
      body: JSON.stringify({ searchTerm, cities, delay, headless, extractEmails }),
    }),
  getGmapResults: (taskId) => request(`/gmap/results/${taskId}`),
  getGmapProgress: () => request('/gmap/progress'),
  markCityCompleted: (data) => request('/gmap/progress/mark-completed', { method: 'POST', body: JSON.stringify(data) }),
  resetGmapProgress: () => request('/gmap/progress/reset', { method: 'POST' }),

  // ── Facebook ADS ──
  startFacebookFeed: (keyword, delay) =>
    request('/facebook/start-feed', {
      method: 'POST',
      body: JSON.stringify({ keyword, delay }),
    }),
  startFacebookContacts: (delay) =>
    request('/facebook/start-contacts', {
      method: 'POST',
      body: JSON.stringify({ delay }),
    }),
  getFacebookResults: (taskId) => request(`/facebook/results/${taskId}`),

  // ── Leads Management ──
  getLeads: (params) => {
    const query = new URLSearchParams()
    if (params.limit) query.append('limit', params.limit)
    if (params.offset) query.append('offset', params.offset)
    if (params.conjunto) query.append('conjunto', params.conjunto)
    if (params.cidade) query.append('cidade', params.cidade)
    if (params.search) query.append('search', params.search)
    return request(`/leads?${query}`)
  },
  getLeadsStats: () => request('/leads/stats'),
  getConjuntos: () => request('/leads/conjuntos'),
  getCidades: (conjunto) => {
    const query = conjunto ? `?conjunto=${encodeURIComponent(conjunto)}` : ''
    return request(`/leads/cidades${query}`)
  },
  deleteLead: (id) => request(`/leads/${id}`, { method: 'DELETE' }),
  updateLead: (id, data) =>
    request(`/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  exportLeads: (filters) =>
    request('/leads/export', {
      method: 'POST',
      body: JSON.stringify(filters),
    }),

  // ── Locations ──
  getLocationSets: () => request('/locations'),
  createLocationSet: (data) => request('/locations', { method: 'POST', body: JSON.stringify(data) }),
  deleteLocationSet: (id) => request(`/locations/${id}`, { method: 'DELETE' }),
  getLocationSetPreview: (id, limit = 10) => request(`/locations/${id}/preview?limit=${limit}`),
}
