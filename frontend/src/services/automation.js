/**
 * Automation Service - Backend local operations
 * Usado APENAS para iniciar/parar automações (scraping)
 * Dados são salvos diretamente no Supabase pelo worker
 */
import { supabase } from '../config/supabase'

/**
 * Get backend URL from user profile or fallback to config
 */
async function getBackendUrl() {
  // Try to get from user profile first
  const { data: { user } } = await supabase.auth.getUser()
  
  if (user) {
    const { data: profile } = await supabase
      .from('users')
      .select('backend_url')
      .eq('id', user.id)
      .single()
    
    if (profile?.backend_url) {
      return profile.backend_url
    }
  }
  
  // Fallback to localStorage or default
  return localStorage.getItem('backend_api_url') || null
}

/**
 * Get auth token for backend requests
 */
async function getAuthToken() {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token
}

/**
 * Make authenticated request to backend
 */
async function backendRequest(endpoint, options = {}) {
  const backendUrl = await getBackendUrl()
  
  if (!backendUrl) {
    throw new Error('Backend URL not configured. Please set it in your profile.')
  }
  
  const token = await getAuthToken()
  
  const response = await fetch(`${backendUrl}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      'ngrok-skip-browser-warning': 'true',
      ...options.headers
    }
  })
  
  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Backend error: ${response.status} - ${error}`)
  }
  
  return response.json()
}

/**
 * AUTOMATION OPERATIONS (Backend Local)
 */

export const automationService = {
  /**
   * Start Google Maps extraction
   */
  async startGMapExtraction(config) {
    return backendRequest('/api/gmap/start', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  },

  /**
   * Start Facebook Ads extraction
   */
  async startFacebookExtraction(config) {
    return backendRequest('/api/facebook/start', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  },

  /**
   * Start email extraction
   */
  async startEmailExtraction(config) {
    return backendRequest('/api/emails/start', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  },

  /**
   * Start email dispatch
   */
  async startEmailDispatch(config) {
    return backendRequest('/api/dispatch/start', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  },

  /**
   * Pause a task
   */
  async pauseTask(taskId) {
    return backendRequest(`/api/tasks/${taskId}/pause`, {
      method: 'POST'
    })
  },

  /**
   * Resume a task
   */
  async resumeTask(taskId) {
    return backendRequest(`/api/tasks/${taskId}/resume`, {
      method: 'POST'
    })
  },

  /**
   * Stop a task
   */
  async stopTask(taskId) {
    return backendRequest(`/api/tasks/${taskId}/stop`, {
      method: 'POST'
    })
  },

  /**
   * Get active tasks from backend
   */
  async getActiveTasks() {
    return backendRequest('/api/tasks/active')
  },

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const backendUrl = await getBackendUrl()
      if (!backendUrl) return { status: 'unconfigured' }
      
      const response = await fetch(`${backendUrl}/api/health`, {
        headers: { 'ngrok-skip-browser-warning': 'true' }
      })
      
      if (response.ok) {
        return { status: 'ok', ...(await response.json()) }
      }
      
      return { status: 'error' }
    } catch (error) {
      return { status: 'error', error: error.message }
    }
  }
}
