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
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        'Bypass-Tunnel-Reminder': 'true',
        ...authHeader,
        ...options.headers
      },
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
  startGmapExtraction: (searchTerm, cities, delay, headless = true, extractEmails = true, locationSetName = null) =>
    request('/gmap/start', {
      method: 'POST',
      body: JSON.stringify({ searchTerm, cities, delay, headless, extractEmails, locationSetName }),
    }),
  getGmapResults: (taskId) => request(`/gmap/results/${taskId}`),
  getGmapProgress: (locationSetId) => supabase
    .from('gmap_progress')
    .select('city')
    .eq('location_set_id', locationSetId)
    .then(({ data, error }) => {
      if (error) throw new Error(error.message)
      const completed = {}
        ; (data || []).forEach(row => { completed[`${locationSetId}:${row.city}`] = true })
      return { completed_cities: completed }
    }),

  markCityCompleted: async ({ location_set, city }) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    const { error } = await supabase.from('gmap_progress').upsert([
      { user_id: session.user.id, location_set_id: location_set, city }
    ], { onConflict: 'user_id,location_set_id,city' })
    if (error) throw new Error(error.message)
    return { status: 'marked' }
  },

  resetGmapProgress: async (locationSetId) => {
    const { error } = await supabase.from('gmap_progress').delete().eq('location_set_id', locationSetId)
    if (error) throw new Error(error.message)
    return { status: 'reset' }
  },

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
  getLocationSets: async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return []

    const { data, error } = await supabase
      .from('location_sets')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) throw new Error(error.message)
    return data || []
  },

  createLocationSet: async (setData) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) throw new Error('Usuário não autenticado')

    const { data, error } = await supabase
      .from('location_sets')
      .insert([{
        name: setData.name.trim(),
        description: setData.description.trim(),
        location_count: setData.locations.length,
        locations: setData.locations,
        user_id: session.user.id
      }])
      .select()
      .single()

    if (error) {
      if (error.code === '23505') throw new Error('duplicate')
      throw new Error(`Failed to create: ${error.message}`)
    }
    return data
  },

  deleteLocationSet: async (id) => {
    const { error } = await supabase.from('location_sets').delete().eq('id', id)
    if (error) throw new Error(error.message)
    return { status: 'deleted' }
  },

  getLocationSetPreview: async (id, limit = 10) => {
    const { data, error } = await supabase.from('location_sets').select('locations').eq('id', id).single()
    if (error) throw new Error(error.message)
    return data.locations.slice(0, limit)
  },

  // ── Sync Configuration ──
  getSyncConfig: () => request('/gmap/sync-config'),
  saveSyncConfig: (config) =>
    request('/gmap/sync-config', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
}
