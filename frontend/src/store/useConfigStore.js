import { create } from 'zustand'
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY
const SETTING_KEY = 'backend_api_url'
const CACHE_KEY = 'prospecta_config_cache'
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

/** Obtém user_id do usuário logado */
async function getUserId() {
  const { data: { user } } = await supabase.auth.getUser()
  return user?.id || null
}

const useConfigStore = create((set, get) => ({
  apiUrl: null,
  connectionStatus: 'unconfigured',
  lastTested: null,
  isLoading: false,

  loadFromSupabase: async () => {
    set({ isLoading: true })

    try {
      // Verificar cache
      const cached = sessionStorage.getItem(CACHE_KEY)
      if (cached) {
        const { backend_api_url, cached_at } = JSON.parse(cached)
        if (Date.now() - cached_at < CACHE_TTL && backend_api_url) {
          set({ apiUrl: backend_api_url, connectionStatus: 'disconnected', isLoading: false })
          return
        }
      }

      const userId = await getUserId()
      if (!userId) {
        set({ isLoading: false })
        return
      }

      const { data, error } = await supabase
        .from('app_settings')
        .select('value')
        .eq('user_id', userId)
        .eq('key', SETTING_KEY)
        .single()

      if (error && error.code !== 'PGRST116') {
        console.error('Error loading config from Supabase:', error)
        set({ isLoading: false })
        return
      }

      const url = data?.value || null

      if (url) {
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({ backend_api_url: url, cached_at: Date.now() }))
      }

      set({ apiUrl: url, connectionStatus: url ? 'disconnected' : 'unconfigured', isLoading: false })
    } catch (e) {
      console.error('Failed to load config:', e)
      set({ isLoading: false })
    }
  },

  setApiUrl: async (url) => {
    if (!validateUrl(url)) throw new Error('Invalid URL format')

    set({ apiUrl: url, connectionStatus: 'testing', isLoading: true })

    try {
      const userId = await getUserId()
      if (!userId) throw new Error('Usuário não autenticado')

      const { error } = await supabase
        .from('app_settings')
        .upsert(
          { user_id: userId, key: SETTING_KEY, value: url, updated_at: new Date().toISOString() },
          { onConflict: 'user_id,key' }
        )

      if (error) {
        console.error('Error saving config to Supabase:', error)
        throw new Error('Failed to save configuration to database')
      }

      sessionStorage.setItem(CACHE_KEY, JSON.stringify({ backend_api_url: url, cached_at: Date.now() }))

      const isHealthy = await get().testConnection()
      set({ connectionStatus: isHealthy ? 'connected' : 'disconnected', lastTested: Date.now(), isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  clearApiUrl: async () => {
    set({ isLoading: true })

    try {
      const userId = await getUserId()
      if (!userId) throw new Error('Usuário não autenticado')

      const { error } = await supabase
        .from('app_settings')
        .delete()
        .eq('user_id', userId)
        .eq('key', SETTING_KEY)

      if (error) {
        console.error('Error clearing config from Supabase:', error)
        throw new Error('Failed to clear configuration from database')
      }

      sessionStorage.removeItem(CACHE_KEY)
      set({ apiUrl: null, connectionStatus: 'unconfigured', lastTested: null, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  testConnection: async () => {
    const { apiUrl } = get()
    if (!apiUrl) return false

    try {
      const response = await fetch(`${apiUrl}/api/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
        signal: AbortSignal.timeout(5000)
      })
      if (response.ok) {
        const data = await response.json()
        return data.status === 'ok'
      }
      return false
    } catch (error) {
      console.error('[Config] Health check failed:', error)
      return false
    }
  },

  isConfigured: () => get().apiUrl !== null,
}))

function validateUrl(url) {
  if (!url || typeof url !== 'string') return false
  if (!url.startsWith('http://') && !url.startsWith('https://')) return false
  try { new URL(url); return true } catch { return false }
}

export default useConfigStore
