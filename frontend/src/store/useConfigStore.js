import { create } from 'zustand'
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY
const SETTING_KEY = 'backend_api_url'
const CACHE_KEY = 'prospecta_config_cache'
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

const useConfigStore = create((set, get) => ({
  apiUrl: null,
  connectionStatus: 'unconfigured',
  lastTested: null,
  isLoading: false,
  
  // Initialize from Supabase with cache
  loadFromSupabase: async () => {
    set({ isLoading: true })
    
    try {
      // Try cache first
      const cached = sessionStorage.getItem(CACHE_KEY)
      if (cached) {
        const { backend_api_url, cached_at } = JSON.parse(cached)
        const age = Date.now() - cached_at
        
        if (age < CACHE_TTL && backend_api_url) {
          set({ 
            apiUrl: backend_api_url, 
            connectionStatus: 'disconnected',
            isLoading: false
          })
          return
        }
      }
      
      // Fetch from Supabase
      const { data, error } = await supabase
        .from('app_settings')
        .select('value')
        .eq('key', SETTING_KEY)
        .single()
      
      if (error && error.code !== 'PGRST116') { // PGRST116 = not found
        console.error('Error loading config from Supabase:', error)
        set({ isLoading: false })
        return
      }
      
      const url = data?.value || null
      
      // Update cache
      if (url) {
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({
          backend_api_url: url,
          cached_at: Date.now()
        }))
      }
      
      set({ 
        apiUrl: url, 
        connectionStatus: url ? 'disconnected' : 'unconfigured',
        isLoading: false
      })
    } catch (e) {
      console.error('Failed to load config:', e)
      set({ isLoading: false })
    }
  },
  
  // Set new URL
  setApiUrl: async (url) => {
    if (!validateUrl(url)) {
      throw new Error('Invalid URL format')
    }
    
    set({ apiUrl: url, connectionStatus: 'testing', isLoading: true })
    
    try {
      // Save to Supabase (upsert)
      const { error } = await supabase
        .from('app_settings')
        .upsert({
          key: SETTING_KEY,
          value: url,
          updated_at: new Date().toISOString()
        }, {
          onConflict: 'key'
        })
      
      if (error) {
        console.error('Error saving config to Supabase:', error)
        throw new Error('Failed to save configuration to database')
      }
      
      // Update cache
      sessionStorage.setItem(CACHE_KEY, JSON.stringify({
        backend_api_url: url,
        cached_at: Date.now()
      }))
      
      // Test connection
      const isHealthy = await get().testConnection()
      set({ 
        connectionStatus: isHealthy ? 'connected' : 'disconnected',
        lastTested: Date.now(),
        isLoading: false
      })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },
  
  // Clear configuration
  clearApiUrl: async () => {
    set({ isLoading: true })
    
    try {
      // Delete from Supabase
      const { error } = await supabase
        .from('app_settings')
        .delete()
        .eq('key', SETTING_KEY)
      
      if (error) {
        console.error('Error clearing config from Supabase:', error)
        throw new Error('Failed to clear configuration from database')
      }
      
      // Clear cache
      sessionStorage.removeItem(CACHE_KEY)
      
      set({ 
        apiUrl: null, 
        connectionStatus: 'unconfigured',
        lastTested: null,
        isLoading: false
      })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },
  
  // Test connection to backend
  testConnection: async () => {
    const { apiUrl } = get()
    if (!apiUrl) return false
    
    try {
      const response = await fetch(`${apiUrl}/api/health`, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
        },
        signal: AbortSignal.timeout(5000)
      })
      return response.ok
    } catch (error) {
      console.error('Health check failed:', error)
      return false
    }
  },
  
  // Computed
  isConfigured: () => get().apiUrl !== null,
}))

// URL validation helper
function validateUrl(url) {
  if (!url || typeof url !== 'string') return false
  if (!url.startsWith('http://') && !url.startsWith('https://')) return false
  
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export default useConfigStore
